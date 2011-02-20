import gevent.event

class ActorRef(object):
    """
    Reference to a running actor which may safely be passed around.

    :class:`ActorRef` instances are returned by :meth:`Actor.start` and the
    lookup methods in :class:`ActorRegistry`. You should never need to create
    :class:`ActorRef` instances yourself.

    :param actor: the actor to wrap
    :type actor: :class:`Actor`
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

    def send_one_way(self, message):
        """
        Send message to actor without waiting for any response.

        Will generally not block, but if the underlying queue is full it will
        block until a free slot is available.

        :param message: message to send
        :type message: picklable dict

        :return: nothing
        """
        self.actor_inbox.put(message)

    def send_request_reply(self, message, block=True, timeout=None):
        """
        Send message to actor and wait for the reply.

        The message must be a picklable dict.
        If ``block`` is :class:`False`, it will immediately return a
        :class:`gevent.event.AsyncResult` instead of blocking.

        If ``block`` is :class:`True`, and ``timeout`` is :class:`None`, as
        default, the method will block until it gets a reply, potentially
        forever. If ``timeout`` is an integer or float, the method will wait
        for a reply for ``timeout`` seconds, and then raise
        :exc:`gevent.Timeout`.

        :param message: message to send
        :type message: picklable dict

        :param block: whether to block while waiting for a reply
        :type block: boolean

        :param timeout: seconds to wait before timeout if blocking
        :type timeout: float or :class:`None`

        :return: :class:`gevent.event.AsyncResult` or response
        """
        reply = gevent.event.AsyncResult()
        message['reply_to'] = reply
        self.send_one_way(message)
        if block:
            return reply.get(timeout=timeout)
        else:
            return reply

    def stop(self, block=True, timeout=None):
        """
        Send a message to the actor, asking it to stop.

        ``block`` and ``timeout`` works as for :meth:`send_request_reply`.
        """
        self.send_request_reply({'command': 'stop'}, block, timeout)
