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

See end of ``pykka.py`` for a code example. The code example results in
approximately the following output, where ``Pinger`` and ``Ponger`` are two
different objects and threads::

    Pinger: calling Ponger.do() ...
    Pinger: calling Ponger.get() ...
    Pinger: printing result ... (blocking)
    Ponger: this was printed by Ponger.do()
    Pinger: this was returned by Ponger.get()
    Pinger: reading Ponger.field ...
    Pinger: printing result ... (blocking)
    Pinger: this is the value of Ponger.field
    ...


License
-------

Pykka is licensed under the Apache License, Version 2.0. See ``LICENSE`` for
the full license text.
