import warnings
from collections import namedtuple


class Envelope(object):
    """
    Envelope to add metadata to a message.

    This is an internal type and is not part of the public API.

    :param message: the message to send
    :type message: any
    :param reply_to: the future to reply to if there is a response
    :type reply_to: :class:`pykka.Future`
    """

    # Using slots speeds up envelope creation with ~20%
    __slots__ = ['message', 'reply_to']

    def __init__(self, message, reply_to=None):
        self.message = message
        self.reply_to = reply_to

    def __repr__(self):
        return 'Envelope(message={!r}, reply_to={!r})'.format(
            self.message, self.reply_to
        )


# Internal actor messages
ActorStop = namedtuple('ActorStop', [])

# Internal proxy messages
ProxyCall = namedtuple('ProxyCall', ['attr_path', 'args', 'kwargs'])
ProxyGetAttr = namedtuple('ProxyGetAttr', ['attr_path'])
ProxySetAttr = namedtuple('ProxySetAttr', ['attr_path', 'value'])


def upgrade_internal_message(message):
    """Filter that upgrades dict-based internal messages to the new format.

    This is needed for a transitional period because Mopidy < 3 uses
    the old internal message format directly, and maybe others.
    """

    if not isinstance(message, dict):
        return message
    if not message.get('command', '').startswith('pykka_'):
        return message

    warnings.warn(
        'Pykka received a dict-based internal message. '
        'This is deprecated and will be unsupported in the future. '
        'Message: {!r}'.format(message),
        DeprecationWarning,
    )

    command = message.get('command')
    if command == 'pykka_stop':
        return ActorStop()
    elif command == 'pykka_call':
        return ProxyCall(
            attr_path=message['attr_path'],
            args=message['args'],
            kwargs=message['kwargs'],
        )
    elif command == 'pykka_getattr':
        return ProxyGetAttr(attr_path=message['attr_path'])
    elif command == 'pykka_setattr':
        return ProxySetAttr(
            attr_path=message['attr_path'], value=message['value']
        )
    else:
        raise ValueError('Unknown internal message: {!r}'.format(message))
