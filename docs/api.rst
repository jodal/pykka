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


Typed actors
============

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
