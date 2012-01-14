=====
Pykka
=====

The goal of Pykka is to provide easy to use concurrency abstractions for Python
by using the `actor model <http://en.wikipedia.org/wiki/Actor_model>`_.

Pykka provides an actor API with two different implementations:

- **ThreadingActor** is built on the Python Standard Library's `threading` and
  `Queue` modules, and has no dependencies outside Python itself. It plays well
  together with non-actor threads.

- **GeventActor** is built on the `gevent <http://www.gevent.org/>`_ library.
  gevent is a coroutine-based Python networking library that uses greenlet to
  provide a high-level synchronous API on top of libevent event loop. It is
  generally faster, but doesn't like playing with other threads.

Much of the naming in Pykka is inspired by the `Akka <http://akka.io/>`_
project which implements actors on the JVM. Though, Pykka does not aim to be a
Python port of Akka.


Project resources
=================

- `Documentation <http://pykka.readthedocs.org/>`_
- `Source code <http://github.com/jodal/pykka>`_
- `Issue tracker <http://github.com/jodal/pykka/issues>`_
- `Download development snapshot <http://github.com/jodal/pykka/tarball/master#egg=pykka-dev>`_
