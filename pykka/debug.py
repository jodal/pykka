import logging as _logging
import sys as _sys
import threading as _threading
import traceback as _traceback


_logger = _logging.getLogger('pykka')


def log_thread_tracebacks(*args, **kwargs):
    """Logs at ``INFO`` level a traceback for each running thread.

    This can be a convenient tool for debugging deadlocks.

    The function accepts any arguments so that it can easily be used as e.g. a
    signal handler, but it does not use the arguments for anything.

    To use this function as a signal handler, setup logging with a
    :attr:`logging.INFO` threshold or lower and make your main thread register
    this with the :mod:`signal` module::

        import logging
        import signal

        import pykka.debug

        logging.basicConfig(level=logging.DEBUG)
        signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    If your application deadlocks, send the `SIGUSR1` signal to the process::

        kill -SIGUSR1 <pid of your process>

    Signal handler caveats:

    - The function *must* be registered as a signal handler by your main
      thread. If not, :func:`signal.signal` will raise a :exc:`ValueError`.

    - All signals in Python are handled by the main thread. Thus, the signal
      will only be handled, and the tracebacks logged, if your main thread is
      available to do some work. Making your main thread idle using
      :func:`time.sleep` is OK. The signal will awaken your main thread.
      Blocking your main thread on e.g.  :func:`Queue.Queue.get` or
      :meth:`pykka.Future.get` will break signal handling, and thus you won't
      be able to signal your process to print the thread tracebacks.

    The morale is: setup signals using your main thread, start your actors,
    then let your main thread relax for the rest of your application's life
    cycle.

    For a complete example of how to use this, see
    ``examples/deadlock_debugging.py`` in Pykka's source code.

    .. versionadded:: 1.1
    """

    thread_names = dict((t.ident, t.name) for t in _threading.enumerate())

    for ident, frame in _sys._current_frames().items():
        name = thread_names.get(ident, '?')
        stack = ''.join(_traceback.format_stack(frame))
        _logger.info(
            'Current state of %s (ident: %s):\n%s', name, ident, stack)
