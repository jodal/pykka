============
Introduction
============


The actor model
===============

An actor has the following characteristics:

- It does not share state with anybody else.

- It can have its own state.

- It can only communicate with other actors by sending and receiving
  messages.

- It can only send messages to actors whose address it has.

- When an actor receives a message it may take actions like:

  - altering its own state, e.g. so that it can react differently to a
    future message,
  - sending messages to other actors, or
  - starting new actors.

- None of the actions are required, and they may be applied in any order.

- It only processes one message at a time. In other words, a single actor
  does not give you any concurrency, and it does not need to use e.g. locks
  to protect its own state.

In Pykka, we have two different ways to use actors: plain actors and typed
actors.


Plain actors
============

Pykka's plain actors get all incoming messages delivered to the
:meth:`on_receive` method. This method can decide what action is needed in
response to the message. The messages are expected to be Python dictionaries,
containing anything that can be serialized.

.. literalinclude:: ../examples/plain_actor.py

We get the following output::

    $ PYTHONPATH=. python examples/plain_actor.py
    [{'se': 'Sweden', 'no': 'Norway'}, {'a': 3, 'c': 5, 'b': 4}]


Typed actors
============

If you wrap a plain actor in a :class:`pykka.proxy.ActorProxy`, Pykka let you
call methods on the actor like you would on a regular object, but it runs the
code in the actor. Similarly, when you access the actor's fields, they are read
in the actor, serialized and copied to the reader.

Both method calling and attribute reads immediately returns future objects.
This means that your code can continue while the result is calculated in some
other actor, and that you're code will not block until you actually use the
returned value.

Here is a small example of two actors wrapped in
:class:`pykka.proxy.ActorProxy` objects. It may look like they communicate with
each other by calling regular methods, but--under the hood--the calls are
serialized and sent to the other actor. Meanwhile, the first actor can continue
executing its own code.

.. literalinclude:: ../examples/counter.py

When we run the above example with Pykka on the :envvar:`PYTHONPATH`, we get
the following output::

    $ PYTHONPATH=. python examples/counter.py
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 0
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 1 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 1
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 2 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 2
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 3 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 3
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 4 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 4
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 5 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 5
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 6 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 6
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 7 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 7
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 8 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 8
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 9 back
    Adder (urn:uuid:35d5216f-332b-4c04-97bb-a02016ba4121) is increasing 9
    Bookkeeper (urn:uuid:fd8df21d-8a58-451b-a1b8-77bd19d868b8) got 10 back

See the ``examples/`` dir for more runnable examples.


Traversable attributes
----------------------

Sometimes you don't care about the attribute of an actor, but you want to
access the attributes of the attribute itself, or call methods on the
attribute. For this case, Pykka supports traversable attributes. By marking an
actor attribute as traversable, Pykka will not return the attribute when
accessed, but wrap it in a new :class:`pykka.proxy.ActorProxy`. When the
wrapped attribute is used, Pykka will get/set attributes or call methods on the
actor attribute, just as it normally would on the actor, if wrapped in an actor
proxy.

To mark an attribute as traversable, simply set the :attr:`pykka_traversable`
attribute to something, like e.g. :class:`True`::

    class AnActor(GeventActor):
        an_attribute = SomeOtherObject()
        an_attribute.pykka_traversable = True

You can mark the attributes of attributes of the actor as traversable, and so
on, as long as all objects in the path from the actor to the deepest nested
attribute is marked as traversable.


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
    logging.basicConfig()

If your application is already using :mod:`logging`, and you want debug log
output from your own application, but not from Pykka, you can ignore debug log
messages from Pykka by increasing the threshold on the Pykka logger to "info"
level or higher::

    import logging
    logging.getLogger('pykka').setLevel(logging.INFO)

For more details on how to use :mod:`logging`, please refer to the Python
standard library documentation.


License
=======

Pykka is licensed under the `Apache License, Version 2.0
<http://www.apache.org/licenses/LICENSE-2.0>`_.


Installation
============

Install Pykka's dependencies:

- Python 2.6 or greater. Python 3.x should work too if you don't use gevent.
- Optionally, `gevent <http://www.gevent.org/>`_, if you want to use gevent
  based actors from :mod:`pykka.gevent`.

To install Pykka you can use pip::

    pip install pykka

To upgrade your Pykka installation to the latest released version::

    pip install --upgrade pykka

To install the latest development snapshot::

    pip install pykka==dev
