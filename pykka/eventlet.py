from __future__ import absolute_import

import sys as _sys

import eventlet as _eventlet
import eventlet.event as _eventlet_event
import eventlet.queue as _eventlet_queue

from pykka import Timeout as _Timeout
from pykka.actor import Actor as _Actor
from pykka.future import Future as _Future


class EventletEvent(_eventlet_event.Event):
    """
    :class:`EventletEvent` adapts :class:`eventlet.event.Event` to
    :class:`threading.Event` interface.
    """

    def set(self):
        if self.ready():
            self.reset()
        self.send()

    def is_set(self):
        return self.ready()

    isSet = is_set

    def clear(self):
        if self.ready():
            self.reset()

    def wait(self, timeout):
        if timeout is not None:
            wait_timeout = _eventlet.Timeout(timeout)

            try:
                with wait_timeout:
                    super(EventletEvent, self).wait()
            except _eventlet.Timeout as t:
                if t is not wait_timeout:
                    raise
                return False
        else:
            self.event.wait()

        return True


class EventletFuture(_Future):
    """
    :class:`EventletFuture` implements :class:`pykka.Future` for use with
    :class:`EventletActor`.
    """

    event = None

    def __init__(self):
        super(EventletFuture, self).__init__()
        self.event = _eventlet_event.Event()

    def get(self, timeout=None):
        try:
            return super(EventletFuture, self).get(timeout=timeout)
        except NotImplementedError:
            pass

        if timeout is not None:
            wait_timeout = _eventlet.Timeout(timeout)
            try:
                with wait_timeout:
                    return self.event.wait()
            except _eventlet.Timeout as t:
                if t is not wait_timeout:
                    raise
                raise _Timeout(t)
        else:
            return self.event.wait()

    def set(self, value=None):
        self.event.send(value)

    def set_exception(self, exc_info=None):
        if isinstance(exc_info, BaseException):
            exc_info = (exc_info,)
        self.event.send_exception(*(exc_info or _sys.exc_info()))


class EventletActor(_Actor):
    """
    :class:`EventletActor` implements :class:`pykka.Actor` using the `eventlet
    <http://eventlet.net/>`_ library.

    This implementation uses eventlet green threads.
    """

    @staticmethod
    def _create_actor_inbox():
        return _eventlet_queue.Queue()

    @staticmethod
    def _create_future():
        return EventletFuture()

    def _start_actor_loop(self):
        _eventlet.greenthread.spawn(self._actor_loop)
