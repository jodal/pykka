import gevent.event


class ActorRef(object):
    """
    Reference to a running actor which may safely be passed around.

    You should never need to create :class:`ActorRef` instances yourself.
    :class:`ActorRef` instances are returned by :meth:`Actor.start` and the
    lookup methods in :class:`ActorRegistry`.
    """

    #: The actor URN is a universally unique identifier for the actor.
    #: It may be used for looking up a specific actor using
    #: :class:`ActorRegistry.get_by_urn`.
    actor_urn = None

    def __init__(self, actor):
        self.actor_urn = actor.actor_urn
        self.actor_class = actor.__class__
        self.actor_inbox = actor.actor_inbox

    def __repr__(self):
        return '<ActorRef for %s>' % str(self)

    def __str__(self):
        return '%(class)s (%(urn)s)' % {
            'urn': self.actor_urn,
            'class': self.actor_class.__name__,
        }

    def stop(self, block=True, timeout=None):
        """Send a message to the actor, asking it to stop."""
        self.send_request_reply({'command': 'stop'}, block, timeout)

    def send_one_way(self, message):
        """
        Send message to actor without waiting for any response.

        The message must be a picklable dict.
        """
        self.actor_inbox.put(message)

    def send_request_reply(self, message, block=True, timeout=None):
        """
        Send message to actor and wait for the reply.

        If ``block`` is :class:`False`, it will immediately return a
        :class:`gevent.event.AsyncResult` instead of blocking.

        If ``block`` is :class:`True`, the timeout should be given in seconds
        as a floating point number. By default, there is no timeout and it will
        wait for an reply forever.

        The message must be a picklable dict.
        """
        reply = gevent.event.AsyncResult()
        message['reply_to'] = reply
        self.send_one_way(message)
        if block:
            return reply.get(timeout=timeout)
        else:
            return reply
