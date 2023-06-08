"""Debug helpers."""

import logging
import sys
import threading
import traceback
from typing import Any

__all__ = ["log_thread_tracebacks"]


logger = logging.getLogger("pykka")


def log_thread_tracebacks(*_args: Any, **_kwargs: Any) -> None:
    """Log a traceback for each running thread at :attr:`logging.CRITICAL` level.

    This can be a convenient tool for debugging deadlocks.

    The function accepts any arguments so that it can easily be used as e.g. a
    signal handler, but it does not use the arguments for anything.

    To use this function as a signal handler, setup logging with a
    :attr:`logging.CRITICAL` threshold or lower and make your main thread
    register this with the :mod:`signal` module::

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
      Blocking your main thread on e.g. :func:`queue.Queue.get` or
      :meth:`pykka.Future.get` will break signal handling, and thus you won't
      be able to signal your process to print the thread tracebacks.

    The morale is: setup signals using your main thread, start your actors,
    then let your main thread relax for the rest of your application's life
    cycle.

    .. versionadded:: 1.1
    """
    thread_names = {t.ident: t.name for t in threading.enumerate()}

    for ident, frame in sys._current_frames().items():  # noqa: SLF001
        name = thread_names.get(ident, "?")
        stack = "".join(traceback.format_stack(frame))
        logger.critical(f"Current state of {name} (ident: {ident}):\n{stack}")
