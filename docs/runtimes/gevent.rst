======
gevent
======

.. deprecated:: 2.0.3

.. warning::
   gevent support is deprecated and will be removed in Pykka 3.0.


Installation
============

To run Pykka on top of `gevent <http://www.gevent.org/>`_, you first need to
install the `gevent package <https://pypi.org/project/gevent/>`_ from PyPI::

    pip install gevent


Code changes
============

Next, all actors must subclass :class:`pykka.gevent.GeventActor` instead of
:class:`pykka.ThreadingActor`.

If you create any futures yourself, you must replace
:class:`pykka.ThreadingFuture` with :class:`pykka.gevent.GeventFuture`.

With those changes in place, Pykka should run on top of gevent.


API
===

.. automodule:: pykka.gevent
    :members:
