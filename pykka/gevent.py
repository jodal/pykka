from __future__ import absolute_import

# pylint: disable = E0611, W0406
import gevent as _gevent
import gevent.event as _gevent_event
import gevent.queue as _gevent_queue
# pylint: enable = E0611, W0406

from pykka import Timeout as _Timeout
from pykka.actor import Actor as _Actor
from pykka.future import Future as _Future


class GeventFuture(_Future):
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
            self.async_result = _gevent_event.AsyncResult()

    def get(self, timeout=None):
        try:
            return self.async_result.get(timeout=timeout)
        except _gevent.Timeout as e:
            raise _Timeout(e)

    def set(self, value=None):
        self.async_result.set(value)

    def set_exception(self, exception):
        self.async_result.set_exception(exception)


class GeventActor(_Actor, _gevent.Greenlet):
    """
    :class:`GeventActor` implements :class:`pykka.actor.Actor` using the
    `gevent <http://www.gevent.org/>`_ library. gevent is a coroutine-based
    Python networking library that uses greenlet to provide a high-level
    synchronous API on top of libevent event loop.

    This is a very fast implementation, but it does not work in combination
    with other threads.
    """

    _superclass = _gevent.Greenlet
    _future_class = GeventFuture

    def _new_actor_inbox(self):
        return _gevent_queue.Queue()
