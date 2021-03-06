========
Runtimes
========

By default, Pykka builds on top of Python's regular threading concurrency
model, via the standard library modules :mod:`threading` and :mod:`queue`.

Pykka 2 and earlier shipped with some alternative implementations that ran on
top of :mod:`gevent` or :mod:`eventlet`. These alternative implementations
were removed in Pykka 3.

Note that Pykka does no attempt at supporting a mix of concurrency runtimes.
Such a future feature has briefly been discussed in issue :issue:`11`.

.. toctree::

    threading
