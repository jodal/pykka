from __future__ import absolute_import

import sys as _sys

import gevent as _gevent
import gevent.event as _gevent_event
import gevent.queue as _gevent_queue

from pykka import Timeout as _Timeout
from pykka.actor import Actor as _Actor
from pykka.future import Future as _Future


class GeventFuture(_Future):
    """
    :class:`GeventFuture` implements :class:`pykka.Future` for use with
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
            return super(GeventFuture, self).get(timeout=timeout)
        except NotImplementedError:
            pass

        try:
            return self.async_result.get(timeout=timeout)
        except _gevent.Timeout as e:
            raise _Timeout(e)

    def set(self, value=None):
        assert not self.async_result.ready(), 'value has already been set'
        self.async_result.set(value)

    def set_exception(self, exc_info=None):
        if isinstance(exc_info, BaseException):
            exception = exc_info
        else:
            exc_info = exc_info or _sys.exc_info()
            exception = exc_info[1]
        self.async_result.set_exception(exception)


class GeventActor(_Actor):
    """
    :class:`GeventActor` implements :class:`pykka.Actor` using the `gevent
    <http://www.gevent.org/>`_ library. gevent is a coroutine-based Python
    networking library that uses greenlet to provide a high-level synchronous
    API on top of libevent event loop.

    This is a very fast implementation, but as of gevent 0.13.x it does not
    work in combination with other threads.
    """

    @staticmethod
    def _create_actor_inbox():
        return _gevent_queue.Queue()

    @staticmethod
    def _create_future():
        return GeventFuture()

    def _start_actor_loop(self):
        _gevent.Greenlet.spawn(self._actor_loop)
