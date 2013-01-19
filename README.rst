=====
Pykka
=====

Pykka is a Python implementation of the `actor model
<http://en.wikipedia.org/wiki/Actor_model>`_. The actor model introduces some
simple rules to control the sharing of state and cooperation between execution
units, which makes it easier to build concurrent applications.


Rules of the actor model
========================

- An actor is an execution unit that executes concurrently with other actors.

- An actor does not share state with anybody else, but it can have its own
  state.

- An actor can only communicate with other actors by sending and receiving
  messages. It can only send messages to actors whose address it has.

- When an actor receives a message it may take actions like:

  - altering its own state, e.g. so that it can react differently to a
    future message,
  - sending messages to other actors, or
  - starting new actors.

  None of the actions are required, and they may be applied in any order.

- An actor only processes one message at a time. In other words, a single actor
  does not give you any concurrency, and it does not need to use locks
  internally to protect its own state.


Two implementations
===================

Pykka's actor API comes with to two different implementations:

- Threads: Each ``ThreadingActor`` is executed by a regular thread, i.e.
  ``threading.Thread``. As handles for future results, it uses
  ``ThreadingFuture`` which is a thin wrapper around a ``Queue.Queue``. It has
  no dependencies outside Python itself. ``ThreadingActor`` plays well
  together with non-actor threads.

- gevent: Each ``GeventActor`` is executed by a gevent greenlet. `gevent
  <http://www.gevent.org/>`_ is a coroutine-based Python networking library
  built on top of a libevent (in 0.13) or libev (in 1.0) event loop.
  ``GeventActor`` is generally faster than ``ThreadingActor``, but as of gevent
  0.13 it doesn't work in processes with other threads, which limits when it
  can be used. With gevent 1.0, which is currently available as a release
  candidate, this is no longer an issue. Pykka works with both gevent 0.13 and
  1.0.

Pykka has an extensive test suite, and is tested on CPython 2.6, 2.7, and 3.2+,
as well as PyPy. gevent is currently not available for CPython 3 or PyPy.


A basic actor
=============

In its most basic form, a Pykka actor is a class with an
``on_receive(message)`` method::

    import pykka

    class Greeter(pykka.ThreadingActor):
        def on_receive(self, message):
            print('Hi there!')

To start an actor, you call the class' method ``start()``, which starts the
actor and returns an actor reference which can be used to communicate with the
running actor::

    actor_ref = Greeter.start()

If you need to pass arguments to the actor upon creation, you can pass them to
the ``start()`` method, and receive them using the regular ``__init__()``
method::

    import pykka

    class Greeter(pykka.ThreadingActor):
        def __init__(self, greeting='Hi there!'):
            super(Greeter, self).__init__()
            self.greeting = greeting

        def on_receive(self, message):
            print(self.greeting)

    actor_ref = Greeter.start(greeting='Hi you!')

It can be useful to know that the init method is run in the execution context
that starts the actor. There are also hooks for running code in the actor's own
execution context when the actor starts, when it stops, and when an unhandled
exception is raised. Check out the full API docs for the details.

To stop an actor, you can either call ``stop()`` on the ``actor_ref``::

    actor_ref.stop()

Or, if an actor wants to stop itself, it can simply do so::

    self.stop()

Once an actor has been stopped, it cannot be restarted.


Sending messages
----------------

To send a message to the actor, you can either use the ``tell()`` method or the
``ask()`` method on the ``actor_ref`` object. ``tell()`` will fire of a message
without waiting for an answer. In other words, it will never block. ``ask()``
will by default block until an answer is returned, potentially forever. If you
provide a ``timeout`` keyword argument to ``ask()``, you can specify for how
long it should wait for an answer. If you want an answer, but don't need it
right away because you have other stuff you can do first, you can pass
``block=False``, and ``ask()`` will immediately return a "future" object.

The message itself must always be a dict, but you're mostly free to use
whatever dict keys you want to.

Summarized in code::

    actor_ref.tell({'msg': 'Hi!'})
    # => Returns nothing. Will never block.

    answer = actor_ref.ask({'msg': 'Hi?'})
    # => May block forever waiting for an answer

    answer = actor_ref.ask({'msg': 'Hi?'}, timeout=3)
    # => May wait 3s for an answer, then raises exception if no answer.

    future = actor_ref.ask({'msg': 'Hi?'}, block=False)
    # => Will return a future object immediately.
    answer = future.get()
    # => May block forever waiting for an answer
    answer = future.get(timeout=0.1)
    # => May wait 0.1s for an answer, then raises exception if no answer.

For performance reasons, Pykka **does not** clone the dict you send before
delivering it to the receiver. You are yourself responsible for either using
immutable data structures or to ``copy.deepcopy()`` the data you're sending off
to other actors.


Replying to messages
--------------------

If a message is sent using ``actor_ref.ask()`` an extra field, ``reply_to`` is
added to the message dict, containing an unresolved future. To reply to the
sender of the message, simply ``set()`` the answer on the ``reply_to`` future::

    import pykka

    class Greeter(pykka.ThreadingActor):
        def on_receive(self, message):
            if 'reply_to' in message:
                message['reply_to'].set('Hi there!')

    actor_ref = Greeter.start()

    answer = actor_ref.ask('Hi?')
    print(answer)
    # => 'Hi there!'


Actor proxies
=============

With the basic building blocks provided by actors and futures, we got
everything we need to build more advanced abstractions. Pykka provides a single
abstraction on top of the basic actor model, named "actor proxies". You can use
Pykka without proxies, but we've found it to be a very convenient abstraction
when builing `Mopidy <http://www.mopidy.com/>`_.

Let's create an actor and start it::

    import pykka

    class Calculator(pykka.ThreadingActor):
        def __init__(self):
            super(Calculator, self).__init__()
            self.last_result = None

        def add(self, a, b=None):
            if b is not None:
                self.last_result = a + b
            else:
                self.last_result += a
            return self.last_result

        def sub(self, a, b=None):
            if b is not None:
                self.last_result = a - b
            else:
                self.last_result -= a
            return self.last_result

    actor_ref = Calculator.start()

You can create a proxy from any reference to a running actor::

    proxy = actor_ref.proxy()

The proxy object will use introspection to figure out what public attributes
and methods the actor has, and then mirror the full API of the actor. Any
attribute or method prefixed with underscore will be ignored, which is the
convention for keeping stuff private in Python.

When we access attributes or call methods on the proxy, it will ask the actor
to access the given attribute or call the given method, and return the result
to us. All results are wrapped in "future" objects, so you must use the
``get()`` method to get the actual data::

    future = proxy.add(1, 3)
    future.get()
    # => 4

    proxy.last_result.get()
    # => 4

Since an actor only processes one message at the time and all messages are kept
in order, you don't need to add the call to ``get()`` just to block
processing until the actor has completed processing your last message::

    proxy.sub(5)
    proxy.add(3)
    proxy.last_result.get()
    # => 2

Since assignment doesn't return anything, it works just like on regular
objects::

    proxy.last_result = 17
    proxy.last_result.get()
    # => 17

Under the hood, the proxy does everything by sending messages to the actor
using the regular ``actor_ref.ask()`` method we talked about previously.
By doing so, it maintains the actor model restrictions. The only "magic"
happening here is some basic introspection and automatic building of three
different message types; one for method calls, one for attribute reads, and one
for attribute writes.


Traversable attributes on proxies
---------------------------------

Sometimes you'll want to access an actor attribute's methods or attributes
through a proxy. For this case, Pykka supports "traversable attributes". By
marking an actor attribute as traversable, Pykka will not return the attribute
when accessed, but wrap it in a new proxy which is returned instead.

To mark an attribute as traversable, simply set the ``pykka_traversable``
attribute to ``True``::

    import pykka

    class AnActor(pykka.ThreadingActor):
        playback = Playback()

    class Playback(object):
        pykka_traversable = True

        def play(self):
            # ...
            return True

    proxy = AnActor.start().proxy()
    play_success = proxy.playback.play().get()

You can access methods and attributes nested as deep as you like, as long as
all attributes on the path between the actor and the method or attribute on the
end is marked as traversable.


Examples
========

See the ``examples/`` dir in `Pykka's Git repo
<https://github.com/jodal/pykka/>`_ for some runnable examples.


What Pykka is not
=================

Much of the naming of concepts and methods in Pykka is taken from the `Akka
<http://akka.io/>`_ project which implements actors on the JVM. Though, Pykka
does not aim to be a Python port of Akka, and supports far fewer features.

Notably, Pykka **does not** support the following features:

- Supervision: Linking actors, supervisors, or supervisor groups.

- Remoting: Communicating with actors running on other hosts.

- Routers: Pykka does not come with a set of predefined message routers, though
  you may make your own actors for routing messages.


Installation
============

Install Pykka's dependencies:

- Python 2.6, 2.7, or 3.2+. Note that gevent is not available on Python 3.

- Optionally, `gevent <http://www.gevent.org/>`_, if you want to use gevent
  based actors from ``pykka.gevent``.

To install Pykka you can use pip::

    pip install pykka

To upgrade your Pykka installation to the latest released version::

    pip install --upgrade pykka

To install the latest development snapshot::

    pip install pykka==dev


License
=======

Pykka is licensed under the `Apache License, Version 2.0
<http://www.apache.org/licenses/LICENSE-2.0>`_.


Project resources
=================

- `Documentation <http://www.pykka.org/>`_
- `Source code <https://github.com/jodal/pykka>`_
- `Issue tracker <https://github.com/jodal/pykka/issues>`_
- `CI server <https://travis-ci.org/jodal/pykka>`_
- `Download development snapshot <https://github.com/jodal/pykka/tarball/master#egg=pykka-dev>`_

.. image:: https://secure.travis-ci.org/jodal/pykka.png?branch=master
