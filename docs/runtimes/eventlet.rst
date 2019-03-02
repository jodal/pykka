========
eventlet
========


Installation
============

To run Pykka on top of `eventlet <https://eventlet.net/>`_, you first need to
install the `eventlet package <https://pypi.org/project/eventlet/>`_ from PyPI::

    pip install eventlet


Code changes
============

Next, all actors must subclass :class:`pykka.eventlet.EventletActor` instead of
:class:`pykka.ThreadingActor`.

If you create any futures yourself, you must replace
:class:`pykka.ThreadingFuture` with :class:`pykka.eventlet.EventletFuture`.

With those changes in place, Pykka should run on top of eventlet.


API
===

.. automodule:: pykka.eventlet
    :members:
