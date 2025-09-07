# Runtimes

By default, Pykka builds on top of Python's regular threading concurrency model,
via the standard library module [`threading`][threading].

Pykka 2 and earlier shipped with some alternative implementations that
ran on top of
[`gevent`](https://www.gevent.org/) or
[`eventlet`](https://eventlet.net/).
These alternative implementations were removed in Pykka 3.

Note that Pykka does no attempt at supporting a mix of concurrency runtimes.
