==========
Quickstart
==========

Pykka is a Python implementation of the `actor model
<https://en.wikipedia.org/wiki/Actor_model>`_. The actor model introduces some
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


The actor implementations
=========================

Pykka's actor API comes with the following implementations:

- Threads: Each :class:`~pykka.ThreadingActor` is executed by a regular
  thread, i.e. :class:`threading.Thread`. As handles for future results, it
  uses :class:`~pykka.ThreadingFuture` which is a thin wrapper around a
  :class:`queue.Queue`. It has no dependencies outside Python itself.
  :class:`~pykka.ThreadingActor` plays well together with non-actor threads.

Pykka 2 and earlier shipped with some alternative implementations that were
removed in Pykka 3:

- gevent: Each actor was executed by a `gevent <http://www.gevent.org/>`_
  greenlet.

- Eventlet: Each actor was executed by an `Eventlet <https://eventlet.net/>`_
  greenlet.


A basic actor
=============

In its most basic form, a Pykka actor is a class with an
:meth:`~pykka.Actor.on_receive` method::

    import pykka

    class Greeter(pykka.ThreadingActor):
        def on_receive(self, message):
            print('Hi there!')

To start an actor, you call the class' method :meth:`~pykka.Actor.start`,
which starts the actor and returns an actor reference which can be used to
communicate with the running actor::

    actor_ref = Greeter.start()

If you need to pass arguments to the actor upon creation, you can pass them to
the :meth:`~pykka.Actor.start` method, and receive them using the regular
``__init__()`` method::

    import pykka

    class Greeter(pykka.ThreadingActor):
        def __init__(self, greeting='Hi there!'):
            super().__init__()
            self.greeting = greeting

        def on_receive(self, message):
            print(self.greeting)

    actor_ref = Greeter.start(greeting='Hi you!')

It can be useful to know that the init method is run in the execution context
that starts the actor. There are also hooks for running code in the actor's own
execution context when the actor starts, when it stops, and when an unhandled
exception is raised. Check out the full API docs for the details.

To stop an actor, you can either call :meth:`~pykka.ActorRef.stop` on the
:class:`~pykka.ActorRef`::

    actor_ref.stop()

Or, if an actor wants to stop itself, it can simply do so::

    self.stop()

Once an actor has been stopped, it cannot be restarted.


Sending messages
----------------

To send a message to the actor, you can either use the
:meth:`~pykka.ActorRef.tell` method or the :meth:`~pykka.ActorRef.ask` method
on the ``actor_ref`` object. :meth:`~pykka.ActorRef.tell` will fire off a
message without waiting for an answer. In other words, it will never block.
:meth:`~pykka.ActorRef.ask` will by default block until an answer is
returned, potentially forever. If you provide a ``timeout`` keyword argument
to :meth:`~pykka.ActorRef.ask`, you can specify for how long it should wait
for an answer. If you want an answer, but don't need it right away because
you have other stuff you can do first, you can pass ``block=False``, and
:meth:`~pykka.ActorRef.ask` will immediately return a "future" object.

The message itself can be of any type, for example a dict or your own message
class type.

Summarized in code::

    actor_ref.tell('Hi!')
    # => Returns nothing. Will never block.

    answer = actor_ref.ask('Hi?')
    # => May block forever waiting for an answer

    answer = actor_ref.ask('Hi?', timeout=3)
    # => May wait 3s for an answer, then raises exception if no answer.

    future = actor_ref.ask('Hi?', block=False)
    # => Will return a future object immediately.
    answer = future.get()
    # => May block forever waiting for an answer
    answer = future.get(timeout=0.1)
    # => May wait 0.1s for an answer, then raises exception if no answer.

.. warning::

    For performance reasons, Pykka **does not** clone the message you send
    before delivering it to the receiver. You are yourself responsible for
    either using immutable data structures or to :func:`copy.deepcopy` the
    data you're sending off to other actors.


Replying to messages
--------------------

If a message is sent using ``actor_ref.ask()`` you can reply to the sender of
the message by simply returning a value from the
:meth:`~pykka.Actor.on_receive` method::

    import pykka

    class Greeter(pykka.ThreadingActor):
        def on_receive(self, message):
            return 'Hi there!'

    actor_ref = Greeter.start()

    answer = actor_ref.ask('Hi?')
    print(answer)
    # => 'Hi there!'

:class:`None` is a valid response so if you return :class:`None` explicitly,
or don't return at all, a response containing :class:`None` will be returned
to the sender.

From the point of view of the actor it doesn't matter whether the message was
sent using :meth:`~pykka.ActorRef.tell` or :meth:`~pykka.ActorRef.ask`. When
the sender doesn't expect a response the :meth:`~pykka.Actor.on_receive`
return value will be ignored.

The situation is similar in regard to exceptions: when
:meth:`~pykka.ActorRef.ask` is used and you raise an exception from within
:meth:`~pykka.Actor.on_receive` method, the exception will propagate to the
sender::

    import pykka

    class Raiser(pykka.ThreadingActor):
        def on_receive(self, message):
            raise Exception('Oops')

    actor_ref = Raiser.start()

    try:
        actor_ref.ask('How are you?')
    except Exception as e:
        print(repr(e))
        # => Exception('Oops')


Actor proxies
=============

With the basic building blocks provided by actors and futures, we got
everything we need to build more advanced abstractions. Pykka provides a single
abstraction on top of the basic actor model, named "actor proxies". You can use
Pykka without proxies, but we've found it to be a very convenient abstraction
when building `Mopidy <https://www.mopidy.com/>`_.

Let's create an actor and start it::

    import pykka

    class Calculator(pykka.ThreadingActor):
        def __init__(self):
            super().__init__()
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
:meth:`~pykka.Future.get` method to get the actual data::

    future = proxy.add(1, 3)
    future.get()
    # => 4

    proxy.last_result.get()
    # => 4

Since an actor only processes one message at the time and all messages are
kept in order, you don't need to add the call to :meth:`~pykka.Future.get`
just to block processing until the actor has completed processing your last
message::

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
using the regular :meth:`~pykka.ActorRef.ask` method we talked about previously.
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

To mark an attribute as traversable, simply mark it with the
:func:`~pykka.traversable` function::

    import pykka

    class AnActor(pykka.ThreadingActor):
        playback = pykka.traversable(Playback())

    class Playback(object):
        def play(self):
            return True

    proxy = AnActor.start().proxy()
    play_success = proxy.playback.play().get()

You can access methods and attributes nested as deep as you like, as long as
all attributes on the path between the actor and the method or attribute on the
end are marked as traversable.
