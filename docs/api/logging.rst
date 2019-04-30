.. _logging:

=======
Logging
=======

Pykka uses Python's standard :mod:`logging` module for logging debug messages
and any unhandled exceptions in the actors. All log messages emitted by Pykka
are issued to the logger named ``pykka``, or a sub-logger of it.

Log levels
==========

Pykka logs at several different log levels, so that you can filter out the
parts you're not interested in:

:attr:`~logging.CRITICAL` (highest)
    This level is only used by the debug helpers in :mod:`pykka.debug`.

:attr:`~logging.ERROR`
    Exceptions raised by an actor that are not captured into a reply future
    are logged at this level.

:attr:`~logging.WARNING`
    Unhandled messages and other potential programming errors are logged at
    this level.

:attr:`~logging.INFO`
    Exceptions raised by an actor that are captured into a reply future
    are logged at this level. If the future result is used elsewhere, the
    exceptions is reraised there too. If the future result isn't used, the log
    message is the only trace of the exception happening.

    To catch bugs earlier, it is recommended to show log messages this level
    during development.

:attr:`~logging.DEBUG` (lowest)
    Every time an actor is started or stopped, and
    registered or unregistered in the actor registry, a message is logged at
    this level.

In summary, you probably want to always let log messages at
:attr:`~logging.WARNING` and higher through, while :attr:`~logging.INFO`
should also be kept on during development.

Log handlers
============

Out of the box, Pykka is set up with :class:`logging.NullHandler` as the only
log record handler. This is the recommended approach for logging in
libraries, so that the application developer using the library will have full
control over how the log messages from the library will be exposed to the
application's users.

In other words, if you want to see the log messages from Pykka anywhere, you
need to add a useful handler to the root logger or the logger named ``pykka``
to get any log output from Pykka.

The defaults provided by :func:`logging.basicConfig` is enough to get debug
log messages from Pykka::

    import logging
    logging.basicConfig(level=logging.DEBUG)

Recommended setup
=================

If your application is already using :mod:`logging`, and you want debug log
output from your own application, but not from Pykka, you can ignore debug log
messages from Pykka by increasing the threshold on the Pykka logger to
:attr:`~logging.INFO` level or higher::

    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('pykka').setLevel(logging.INFO)

Given that you've fixed all unhandled exceptions logged at the
:attr:`~logging.INFO` level during development, you probably want to disable
logging from Pykka at the :attr:`~logging.INFO` level in production to avoid
logging exceptions that are properly handled::

    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('pykka').setLevel(logging.WARNING)

For more details on how to use :mod:`logging`, please refer to the Python
standard library documentation.
