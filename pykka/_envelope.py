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
