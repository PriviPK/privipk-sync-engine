import json
import time
from tests.util.base import api_client, add_fake_message, db, thread

__all__ = ['api_client', 'db', 'thread']


def get_cursor(api_client, timestamp):
    cursor_response = api_client.post_data('/delta/generate_cursor',
                                           {'start': timestamp})
    return json.loads(cursor_response.data)['cursor']


def test_invalid_input(api_client):
    cursor_response = api_client.post_data('/delta/generate_cursor',
                                           {'start': "I'm not a timestamp!"})
    assert cursor_response.status_code == 400

    sync_response = api_client.client.get(api_client.full_path(
        '/delta?cursor={}'.format('fake cursor')))
    assert sync_response.status_code == 400


def test_event_generation(api_client):
    """Test that deltas are returned in response to client sync API calls.
    Doesn't test formatting of individual deltas in the response."""
    ts = int(time.time())
    cursor = get_cursor(api_client, ts)

    sync_data = api_client.get_data('/delta?cursor={}'.format(cursor))
    assert len(sync_data['deltas']) == 0
    assert sync_data['cursor_end'] == cursor
    assert sync_data['cursor_end'] == sync_data['cursor_start']

    api_client.post_data('/tags/', {'name': 'foo'})

    sync_data = api_client.get_data('/delta?cursor={}'.format(cursor))
    assert len(sync_data['deltas']) == 1

    thread_id = api_client.get_data('/threads/')[0]['id']
    thread_path = '/threads/{}'.format(thread_id)
    api_client.put_data(thread_path, {'add_tags': ['foo']})

    sync_data = api_client.get_data('/delta?cursor={}'.format(cursor))
    assert len(sync_data['deltas']) == 2

    cursor = sync_data['cursor_end']
    # Test result limiting
    for i in range(1, 10):
        thread_id = api_client.get_data('/threads/')[i]['id']
        thread_path = '/threads/{}'.format(thread_id)
        api_client.put_data(thread_path, {'add_tags': ['foo']})

    sync_data = api_client.get_data('/delta?cursor={0}&limit={1}'.
                                    format(cursor, 8))
    assert len(sync_data['deltas']) == 8

    new_cursor = sync_data['cursor_end']
    sync_data = api_client.get_data('/delta?cursor={0}'.format(new_cursor))
    assert len(sync_data['deltas']) == 1


def test_events_are_condensed(api_client):
    """Test that multiple revisions of the same object are rolled up in the
    delta response."""
    ts = int(time.time())
    cursor = get_cursor(api_client, ts)

    # Create, then modify a tag; then modify it again
    tag = json.loads(api_client.post_data('/tags/', {'name': 'foo'}).data)
    tag_id = tag['id']
    api_client.put_data('/tags/{}'.format(tag_id), {'name': 'bar'})
    api_client.put_data('/tags/{}'.format(tag_id), {'name': 'baz'})

    # Modify a thread, then modify it again
    thread_id = api_client.get_data('/threads/')[0]['id']
    thread_path = '/threads/{}'.format(thread_id)
    api_client.put_data(thread_path, {'add_tags': [tag_id]})
    api_client.put_data(thread_path, {'remove_tags': [tag_id]})

    sync_data = api_client.get_data('/delta?cursor={}'.format(cursor))
    assert len(sync_data['deltas']) == 3
    first_delta = sync_data['deltas'][0]
    assert first_delta['object'] == 'tag' and first_delta['event'] == 'create'

    # Check that successive modifies are condensed.

    second_delta = sync_data['deltas'][1]
    assert (second_delta['object'] == 'tag' and
            second_delta['event'] == 'modify')
    assert second_delta['attributes']['name'] == 'baz'

    third_delta = sync_data['deltas'][2]
    assert (third_delta['object'] == 'thread' and
            third_delta['event'] == 'modify')


def test_handle_missing_objects(api_client, db, thread, default_namespace):
    ts = int(time.time())
    cursor = get_cursor(api_client, ts)

    messages = []
    for _ in range(100):
        messages.append(add_fake_message(db.session, default_namespace.id,
                                         thread))
    for message in messages:
        db.session.delete(message)
    db.session.commit()
    sync_data = api_client.get_data('/delta?cursor={}&exclude_types=thread'.
                                    format(cursor))
    assert len(sync_data['deltas']) == 100
    assert all(delta['event'] == 'delete' for delta in sync_data['deltas'])
