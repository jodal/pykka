Pykka
=====

Pykka is a concurrency abstraction which makes actors look like regular
objects.

It lets you call methods on an actor like you would on a regular object, but it
runs the code in the actor's own thread. Similarily, when you access the
actor's fields, they are read in the actor's thread, serialized and copied to
the reading thread.

Both method calling and attribute reads returns futures which ensures that the
calling thread does not block before the value from the object's thread is
actually used.

Pykka is similar to typed actors in the Akka framework.


What can it do?
---------------

Given the following code::

    from pykka import Actor

    class Adder(Actor):
        def add_one(self, i):
            print '%s: %d' % (self.name, i)
            return i + 1

    class Counter(Actor):
        def count_to(self, target):
            i = 0
            while i < target:
                print '%s: %d' % (self.name, i)
                i = self.other.add_one(i + 1).get()

    if __name__ == '__main__':
        adder = Adder().start()
        counter = Counter(other=adder).start()
        counter.count_to(10).get() # Block until finished
        counter.stop()
        adder.stop()

We get the following output::

    $ PYTHONPATH=. python examples/counter.py
    Thread-2: 0
    Thread-1: 1
    Thread-2: 2
    Thread-1: 3
    Thread-2: 4
    Thread-1: 5
    Thread-2: 6
    Thread-1: 7
    Thread-2: 8
    Thread-1: 9

See the ``examples/`` dir for more runnable examples.


License
-------

Pykka is licensed under the Apache License, Version 2.0. See ``LICENSE`` for
the full license text.
