from __future__ import absolute_import

import sys
import threading

from pykka import Actor, Future, Timeout, _compat


__all__ = ['ThreadingActor', 'ThreadingFuture']


class ThreadingFuture(Future):
    """
    :class:`ThreadingFuture` implements :class:`Future` for use with
    :class:`ThreadingActor <pykka.ThreadingActor>`.

    The future is implemented using a :class:`queue.Queue`.

    The future does *not* make a copy of the object which is :meth:`set()
    <pykka.Future.set>` on it. It is the setters responsibility to only pass
    immutable objects or make a copy of the object before setting it on the
    future.

    .. versionchanged:: 0.14
        Previously, the encapsulated value was a copy made with
        :func:`copy.deepcopy`, unless the encapsulated value was a future, in
        which case the original future was encapsulated.
    """

    def __init__(self):
        super(ThreadingFuture, self).__init__()
        self._queue = _compat.queue.Queue(maxsize=1)
        self._data = None

    def get(self, timeout=None):
        try:
            return super(ThreadingFuture, self).get(timeout=timeout)
        except NotImplementedError:
            pass

        try:
            if self._data is None:
                self._data = self._queue.get(True, timeout)
            if 'exc_info' in self._data:
                _compat.reraise(*self._data['exc_info'])
            else:
                return self._data['value']
        except _compat.queue.Empty:
            raise Timeout('{} seconds'.format(timeout))

    def set(self, value=None):
        self._queue.put({'value': value}, block=False)

    def set_exception(self, exc_info=None):
        assert exc_info is None or len(exc_info) == 3
        self._queue.put({'exc_info': exc_info or sys.exc_info()})


class ThreadingActor(Actor):
    """
    :class:`ThreadingActor` implements :class:`Actor` using regular Python
    threads.

    This implementation is slower than :class:`GeventActor
    <pykka.gevent.GeventActor>`, but can be used in a process with other
    threads that are not Pykka actors.
    """

    use_daemon_thread = False
    """
    A boolean value indicating whether this actor is executed on a thread that
    is a daemon thread (:class:`True`) or not (:class:`False`). This must be
    set before :meth:`pykka.Actor.start` is called, otherwise
    :exc:`RuntimeError` is raised.

    The entire Python program exits when no alive non-daemon threads are left.
    This means that an actor running on a daemon thread may be interrupted at
    any time, and there is no guarantee that cleanup will be done or that
    :meth:`pykka.Actor.on_stop` will be called.

    Actors do not inherit the daemon flag from the actor that made it. It
    always has to be set explicitly for the actor to run on a daemonic thread.
    """

    @staticmethod
    def _create_actor_inbox():
        return _compat.queue.Queue()

    @staticmethod
    def _create_future():
        return ThreadingFuture()

    def _start_actor_loop(self):
        thread = threading.Thread(target=self._actor_loop)
        thread.name = thread.name.replace('Thread', self.__class__.__name__)
        thread.daemon = self.use_daemon_thread
        thread.start()
