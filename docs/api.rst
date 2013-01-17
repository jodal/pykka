=========
Pykka API
=========

.. module:: pykka

.. attribute:: __version__

   Pykka's :pep:`386` and :pep:`396` compatible version number


Actors
======

.. autoexception:: pykka.ActorDeadError

.. autoclass:: pykka.Actor
    :members:

.. autoclass:: pykka.ThreadingActor
    :members:

.. autoclass:: pykka.ActorRef
    :members:


Proxies
=======

.. autoclass:: pykka.ActorProxy
    :members:


Futures
=======

.. autoexception:: pykka.Timeout

.. autoclass:: pykka.Future
    :members:

.. autoclass:: pykka.ThreadingFuture
    :members:

.. autofunction:: pykka.get_all


Registry
========

.. autoclass:: pykka.ActorRegistry
    :members:


Gevent support
==============

.. automodule:: pykka.gevent
    :members:


Logging
=======

Pykka uses Python's standard :mod:`logging` module for logging debug statements
and any unhandled exceptions in the actors. All log records emitted by Pykka
are issued to the logger named "pykka", or a sublogger of it.

Out of the box, Pykka is set up with :class:`logging.NullHandler` as the only
log record handler. This is the recommended approach for logging in
libraries, so that the application developer using the library will have full
control over how the log records from the library will be exposed to the
application's users. In other words, if you want to see the log records from
Pykka anywhere, you need to add a useful handler to the root logger or the
logger named "pykka" to get any log output from Pykka. The defaults provided by
:meth:`logging.basicConfig` is enough to get debug log statements out of
Pykka::

    import logging
    logging.basicConfig(level=logging.DEBUG)

If your application is already using :mod:`logging`, and you want debug log
output from your own application, but not from Pykka, you can ignore debug log
messages from Pykka by increasing the threshold on the Pykka logger to "info"
level or higher::

    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('pykka').setLevel(logging.INFO)

For more details on how to use :mod:`logging`, please refer to the Python
standard library documentation.


Debug helpers
=============

.. automodule:: pykka.debug
    :members:
