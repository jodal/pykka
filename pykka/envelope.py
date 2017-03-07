from __future__ import absolute_import


class Envelope(object):

    def __init__(self, message, sender):
        self.message = message
        self.sender = sender
