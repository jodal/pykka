import sys

import eventlet
import eventlet.event
import eventlet.queue
from eventlet.greenthread import GreenThread

from pykka import Actor, Future, Scheduler, Timeout

__all__ = [
    "EventletActor",
    "EventletEvent",
    "EventletFuture",
    "EventletScheduler",
]


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

    def clear(self):
        if self.ready():
            self.reset()

    def wait(self, timeout=None):
        if timeout is not None:
            wait_timeout = eventlet.Timeout(timeout)

            try:
                with wait_timeout:
                    super().wait()
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
        super().__init__()
        self.event = eventlet.event.Event()

    def get(self, timeout=None):
        try:
            return super().get(timeout=timeout)
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


class EventletScheduler(Scheduler):
    """
    A basic Pykka Scheduler service based on Akka Scheduler behaviour.

    Its main purpose is to `tell` a message to an actor after a specified
    delay or to do it periodically. It isn't a long-term scheduler
    and is expected to be used for retransmitting messages or to schedule
    periodic startup of an actor-based data processing pipeline.

    Eventlet scheduler is based on eventlet.greenthread.GreenThread.
    """

    @staticmethod
    def _get_timer(delay, func, *args) -> GreenThread:
        """
        Creates a GreenThread to schedule function execution.

        Args:
            delay: Delay before function execution.
            func: Function to execute.
            args: Function arguments.
        Returns: GreenThread object.
        """
        timer = eventlet.spawn_after(delay, func, *args)
        return timer
