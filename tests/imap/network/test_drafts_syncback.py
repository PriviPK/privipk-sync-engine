import uuid
from datetime import datetime

import pytest

from tests.util.crispin import crispin_client

ACCOUNT_ID = 1
NAMESPACE_ID = 1
THREAD_ID = 2

# These tests use a real Gmail test account and idempotently put the account
# back to the state it started in when the test is done.


@pytest.fixture(autouse=True)
def register_action_backends(db):
    """
    Normally action backends only get registered when the actions
    rqworker starts. So we need to register them explicitly for these
    tests.
    """
    from inbox.server.actions.base import register_backends
    register_backends()


@pytest.fixture(scope='function')
def message(db, config):
    from inbox.models.tables.imap import ImapAccount

    account = db.session.query(ImapAccount).get(ACCOUNT_ID)
    to = [{'name': u'"\u2605The red-haired mermaid\u2605"',
           'email': account.email_address}]
    subject = 'Draft test: ' + str(uuid.uuid4().hex)
    body = '<html><body><h2>Sea, birds, yoga and sand.</h2></body></html>'

    return (to, subject, body)


def test_remote_save_draft(db, config, message):
    """ Tests the save_draft function, which saves the draft to the remote. """
    from inbox.actions.gmail import remote_save_draft
    from inbox.sendmail.base import _parse_recipients, all_recipients
    from inbox.sendmail.message import create_email, SenderInfo
    from inbox.models.tables.base import Account

    account = db.session.query(Account).get(ACCOUNT_ID)
    sender_info = SenderInfo(name=account.full_name,
                             email=account.email_address)
    to, subject, body = message
    to_addr = _parse_recipients(to)
    recipients = all_recipients(to_addr)
    email = create_email(sender_info, None, recipients, subject, body,
                         None)
    date = datetime.utcnow()

    remote_save_draft(account, account.drafts_folder.name, email.to_string(),
                      db.session, date)

    with crispin_client(account.id, account.provider) as c:
        criteria = ['NOT DELETED', 'SUBJECT "{0}"'.format(subject)]

        c.conn.select_folder(account.drafts_folder.name, readonly=False)

        inbox_uids = c.conn.search(criteria)
        assert inbox_uids, 'Message missing from Drafts folder'

        c.conn.delete_messages(inbox_uids)
        c.conn.expunge()


def test_remote_delete_draft(db, config, message):
    """
    Tests the delete_draft function, which deletes the draft from the
    remote.

    """
    from inbox.actions.gmail import (remote_save_draft,
                                            remote_delete_draft)
    from inbox.sendmail.base import _parse_recipients, all_recipients
    from inbox.sendmail.message import create_email, SenderInfo
    from inbox.models.tables.base import Account

    account = db.session.query(Account).get(ACCOUNT_ID)
    sender_info = SenderInfo(name=account.full_name,
                             email=account.email_address)
    to, subject, body = message
    to_addr = _parse_recipients(to)
    recipients = all_recipients(to_addr)
    email = create_email(sender_info, None, recipients, subject, body,
                         None)
    date = datetime.utcnow()

    # Save on remote
    remote_save_draft(account, account.drafts_folder.name, email.to_string(),
                      db.session, date)

    inbox_uid = email.headers['X-INBOX-ID']

    with crispin_client(account.id, account.provider) as c:
        criteria = ['DRAFT', 'NOT DELETED',
                    'HEADER X-INBOX-ID {0}'.format(inbox_uid)]

        c.conn.select_folder(account.drafts_folder.name, readonly=False)
        uids = c.conn.search(criteria)
        assert uids, 'Message missing from Drafts folder'

        # Delete on remote
        remote_delete_draft(account, account.drafts_folder.name, inbox_uid,
                            db.session)

        c.conn.select_folder(account.drafts_folder.name, readonly=False)
        uids = c.conn.search(criteria)
        assert not uids, 'Message still in Drafts folder'