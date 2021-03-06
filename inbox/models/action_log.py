from sqlalchemy import Column, Integer, Text, ForeignKey, Enum, Index, String
from sqlalchemy.orm import relationship

from inbox.sqlalchemy_ext.util import JSON
from inbox.models.base import MailSyncBase
from inbox.models.namespace import Namespace

ADD_TAG_ACTIONS = {
    'inbox': 'unarchive',
    'archive': 'archive',
    'starred': 'star',
    'unread': 'mark_unread',
    'spam': 'mark_spam',
    'trash': 'mark_trash'
}

REMOVE_TAG_ACTIONS = {
    'inbox': 'archive',
    'archive': 'unarchive',
    'starred': 'unstar',
    'unread': 'mark_read',
    'spam': 'unmark_spam',
    'trash': 'unmark_trash'
}


class ActionError(Exception):
    def __init__(self, error, namespace_id):
        self.error = error
        self.namespace_id = namespace_id

    def __str__(self):
        return 'Error {0} for namespace_id {1}'.format(
            self.error, self.namespace_id)


def schedule_action_for_tag(tag_public_id, thread, db_session, tag_added):
    if tag_added:
        action = ADD_TAG_ACTIONS.get(tag_public_id)
    else:
        action = REMOVE_TAG_ACTIONS.get(tag_public_id)
    if action is not None:
        schedule_action(action, thread, thread.namespace_id, db_session)


def schedule_action(func_name, record, namespace_id, db_session, **kwargs):
    # Ensure that the record's id is non-null
    db_session.flush()

    # Ensure account is valid
    account = db_session.query(Namespace).get(namespace_id).account

    if account.sync_state == 'invalid':
        raise ActionError(error=403, namespace_id=namespace_id)

    # Check we don't already have a pending log entry for this action.
    # Some actions (e.g. client adds tag 'archive' and removes tag 'inbox')
    # translate to the same ActionLog entry.
    existing = db_session.query(account.actionlog_cls).filter_by(
        action=func_name,
        table_name=record.__tablename__,
        record_id=record.id,
        namespace_id=namespace_id,
        extra_args=kwargs,
        status='pending').first()

    if not existing:
        # Create the ActionLog entry
        log_entry = account.actionlog_cls.create(
            action=func_name,
            table_name=record.__tablename__,
            record_id=record.id,
            namespace_id=namespace_id,
            extra_args=kwargs)
        db_session.add(log_entry)


class ActionLog(MailSyncBase):
    namespace_id = Column(ForeignKey(Namespace.id, ondelete='CASCADE'),
                          nullable=False,
                          index=True)
    namespace = relationship('Namespace')

    action = Column(Text(40), nullable=False)
    record_id = Column(Integer, nullable=False)
    table_name = Column(Text(40), nullable=False)
    status = Column(Enum('pending', 'successful', 'failed'),
                    server_default='pending')
    retries = Column(Integer, server_default='0', nullable=False)

    extra_args = Column(JSON, nullable=True)

    @classmethod
    def create(cls, action, table_name, record_id, namespace_id, extra_args):
        return cls(action=action, table_name=table_name, record_id=record_id,
                   namespace_id=namespace_id, extra_args=extra_args)

    discriminator = Column('type', String(16))
    __mapper_args__ = {'polymorphic_identity': 'actionlog',
                       'polymorphic_on': discriminator}

Index('ix_actionlog_status_retries', ActionLog.status, ActionLog.retries)
