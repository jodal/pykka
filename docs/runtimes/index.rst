========
Runtimes
========

By default, Pykka builds on top of Python's regular threading concurrency
model, via the standard library modules :mod:`threading` and :mod:`queue`.

Alternatively, you may run Pykka on top of :mod:`gevent` or :mod:`eventlet`.

Note that Pykka does no attempt at supporting a mix of concurrency runtimes.
Such a future feature has briefly been discussed in issue :issue:`11`.

.. toctree::

    threading
    gevent
    eventlet
