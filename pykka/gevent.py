from __future__ import absolute_import

import gevent
import gevent.event
import gevent.queue

from pykka.actor import Actor
from pykka.future import Timeout, Future


class GeventFuture(Future):
    """
    :class:`GeventFuture` implements :class:`pykka.future.Future` for use with
    :class:`GeventActor`.

    It encapsulates a :class:`gevent.event.AsyncResult` object which may be
    used directly, though it will couple your code with gevent.
    """

    #: The encapsulated :class:`gevent.event.AsyncResult`
    async_result = None

    def __init__(self, async_result=None):
        super(GeventFuture, self).__init__()
        if async_result is not None:
            self.async_result = async_result
        else:
            self.async_result = gevent.event.AsyncResult()

    def get(self, timeout=None):
        try:
            return self.async_result.get(timeout=timeout)
        except gevent.Timeout as e:
            raise Timeout(e)

    def set(self, value=None):
        self.async_result.set(value)

    def set_exception(self, exception):
        self.async_result.set_exception(exception)


class GeventActor(Actor, gevent.Greenlet):
    """
    :class:`GeventActor` implements :class:`Actor` using the `gevent
    <http://www.gevent.org/>`_ library. gevent is a coroutine-based Python
    networking library that uses greenlet to provide a high-level
    synchronous API on top of libevent event loop.

    This is a very fast implementation, but it does not work in combination
    with other threads.
    """

    _superclass = gevent.Greenlet
    _future_class = GeventFuture

    def _new_actor_inbox(self):
        return gevent.queue.Queue()

    def react(self, message):
        raise NotImplementedError
