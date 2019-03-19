from __future__ import absolute_import

import sys

import eventlet
import eventlet.event
import eventlet.queue

from pykka import Actor, Future, Timeout


__all__ = ['EventletActor', 'EventletEvent', 'EventletFuture']


class EventletEvent(eventlet.event.Event):
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
            wait_timeout = eventlet.Timeout(timeout)

            try:
                with wait_timeout:
                    super(EventletEvent, self).wait()
            except eventlet.Timeout as t:
                if t is not wait_timeout:
                    raise
                return False
        else:
            self.event.wait()

        return True


class EventletFuture(Future):
    """
    :class:`EventletFuture` implements :class:`pykka.Future` for use with
    :class:`EventletActor`.
    """

    event = None

    def __init__(self):
        super(EventletFuture, self).__init__()
        self.event = eventlet.event.Event()

    def get(self, timeout=None):
        try:
            return super(EventletFuture, self).get(timeout=timeout)
        except NotImplementedError:
            pass

        if timeout is not None:
            wait_timeout = eventlet.Timeout(timeout)
            try:
                with wait_timeout:
                    return self.event.wait()
            except eventlet.Timeout as t:
                if t is not wait_timeout:
                    raise
                raise Timeout(t)
        else:
            return self.event.wait()

    def set(self, value=None):
        self.event.send(value)

    def set_exception(self, exc_info=None):
        assert exc_info is None or len(exc_info) == 3
        self.event.send_exception(*(exc_info or sys.exc_info()))


class EventletActor(Actor):
    """
    :class:`EventletActor` implements :class:`pykka.Actor` using the `eventlet
    <https://eventlet.net/>`_ library.

    This implementation uses eventlet green threads.
    """

    @staticmethod
    def _create_actor_inbox():
        return eventlet.queue.Queue()

    @staticmethod
    def _create_future():
        return EventletFuture()

    def _start_actor_loop(self):
        eventlet.greenthread.spawn(self._actor_loop)
