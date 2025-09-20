# Actor proxies

With the basic building blocks provided by actors and futures,
we have everything we need to build more advanced abstractions.

Pykka provides a single abstraction on top of the basic actor model,
called "actor proxies".
You can use Pykka without proxies,
but we've found it to be a very convenient abstraction
when building [Mopidy](https://www.mopidy.com/).

## Create an actor and a proxy

Let's create an actor and start it:

```py
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
```

You can create a proxy from any reference to a running actor:

```py
proxy = actor_ref.proxy()
```

The proxy object will use introspection to figure out
what public attributes and methods the actor has,
and then mirror the full API of the actor.
Any attribute or method prefixed with underscore will be ignored,
which is the convention for keeping stuff private in Python.

## Accessing attributes and calling methods

When we access attributes or call methods on the proxy,
it will ask the actor to access the given attribute or call the given method,
and return the result to us.
All results are wrapped in "future" objects,
so you must use the [`Future.get()`][pykka.Future.get] method
to get the actual data:

```py
future = proxy.add(1, 3)
future.get()
# => 4

proxy.last_result.get()
# => 4
```

Since an actor only processes one message at the time and all messages
are kept in order,
you don't need to add the call to [`get()`][pykka.Future.get] just
to block processing until the actor has completed processing your last message:

```py
proxy.sub(5)
proxy.add(3)
proxy.last_result.get()
# => 2
```

Since assignment doesn't return anything,
it works just like on regular objects:

```py
proxy.last_result = 17
proxy.last_result.get()
# => 17
```

Under the hood,
the proxy does everything by sending messages to the actor
using the regular [`ActorRef.ask()`][pykka.ActorRef.ask] method
that we talked about previously.
By doing so,
it maintains the actor model restrictions.
The only "magic" happening here is some basic introspection
and automatic building of three different message types;
one for method calls,
one for attribute reads,
and one for attribute writes.

## Traversable attributes

Sometimes you'll want to access an actor attribute's own
methods or attributes through a proxy.
For this case,
Pykka supports "traversable attributes".
By marking an actor attribute as traversable,
Pykka will not return the attribute when accessed,
but wrap it in a new proxy which is returned instead.

To mark an attribute as traversable, simply mark it with the
[`pykka.traversable()`][pykka.traversable] function:

```py
import pykka

class AnActor(pykka.ThreadingActor):
    playback = pykka.traversable(Playback())

class Playback(object):
    def play(self):
        return True

proxy = AnActor.start().proxy()
play_success = proxy.playback.play().get()
```

You can access methods and attributes nested as deep as you like,
as long as all attributes on the path between the actor
and the method or attribute on the end
are marked as traversable.
