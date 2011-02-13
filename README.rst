=====
Pykka
=====

Pykka implements the actor model for concurrent programming on top of the
`gevent <http://www.gevent.org/>`_ library, which again is based on greenlet
and libevent.

The goal of Pykka is to provide easy to use concurrency abstraction for Python.
And since Pykka is built on gevent, the performance should be quite all right
too.


Regular actors
==============

Regular actors get all incoming messages delivered to :meth:`Actor.react`.
This method can decide what action is needed in response to the message. The
messages are expected to be Python dictionaries, containing anything that can
be serialized.

::

    #! /usr/bin/env python

    from pykka import Actor

    class PlainActor(Actor):
        def __init__(self):
            self.stored_messages = []

        def react(self, message):
            if message.get('command') == 'print':
                print self.stored_messages
            else:
                self.stored_messages.append(message)

    if __name__ == '__main__':
        actor = PlainActor().start()
        actor.send_one_way({'no': 'Norway', 'se': 'Sweden'})
        actor.send_one_way({'a': 3, 'b': 4, 'c': 5})
        actor.send_request_reply({'command': 'print'})

We get the following output::

    $ PYTHONPATH=. examples/plain_actor.py
    [{'se': 'Sweden', 'no': 'Norway'}, {'a': 3, 'c': 5, 'b': 4}]


Proxy actors
============

If you wrap a plain actor in an :class:`ActorProxy`, Pykka let you call methods
on the actor like you would on a regular object, but it runs the code in the
actor. Similarly, when you access the actor's fields, they are read in the
actor, serialized and copied to the reader.

Both method calling and attribute reads immediately returns future objects.
This means that your code can continue while the result is calculated in some
other actor, and that you're code will not block until you actually use the
returned value.

Here is a small example of two actors wrapped in :class:`ActorProxy` objects.
They seemingly communicate with each other by calling regular methods, but,
under the hood, the calls are serialized and sent the other actor while the
first actor can continue executing.

::

    #! /usr/bin/env python

    from pykka import Actor, ActorProxy

    class Adder(Actor):
        def add_one(self, i):
            print '%s is increasing %d' % (self, i)
            return i + 1

    class Bookkeeper(Actor):
        def __init__(self, adder):
            self.adder = adder

        def count_to(self, target):
            i = 0
            while i < target:
                i = self.adder.add_one(i).get()
                print '%s got %d back' % (self, i)

    if __name__ == '__main__':
        adder = Adder.start_proxy()
        bookkeeper = Bookkeeper.start_proxy(adder)
        bookkeeper.count_to(10).wait()

We get the following output::

    $ PYTHONPATH=. examples/counter.py
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


License
=======

Pykka is licensed under the Apache License, Version 2.0. See ``LICENSE`` for
the full license text.


Installation
============

Install Pykka's dependencies:

- Python 2.6 or 2.7
- `gevent <http://www.gevent.org/>`_

To install Pykka you can use pip::

    pip install pykka

To upgrade your Pykka installation to the latest released version::

    pip install --upgrade pykka

To install the latest development snapshot::

    pip install pykka==dev


Project resources
=================

- `Documentation <http://jodal.github.com/pykka/>`_
- `Source code <http://github.com/jodal/pykka>`_
- `Issue tracker <http://github.com/jodal/pykka/issues>`_
- `Download development snapshot <http://github.com/jodal/pykka/tarball/master#egg=pykka-dev>`_
