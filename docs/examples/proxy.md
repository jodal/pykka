# Actor with proxy

This example shows how to define an actor by creating a class that subclasses
[`ThreadingActor`][pykka.ThreadingActor] and defines attributes and methods that
can be accessed through a proxy. This makes the actor almost as easy to use as a
regular class, with the only difference being that the method calls and
attribute accesses are asynchronous and return [futures][pykka.Future].

This actor does not override the [`on_receive()`][pykka.Actor.on_receive]
method, but it is entirely possible to combine the two approaches and use both
regular message passing to the [`on_receive()`][pykka.Actor.on_receive] method
and proxy-based access to methods and attributes on the same actor.

## Example

```title="examples/proxy.py"
--8<-- "examples/proxy.py"
```

## Output

```console
$ uv run examples/proxy.py
MainThread: calling AnActor.foo() ...
MainThread: calling AnActor.bar() ...
AnActor-1 (_actor_loop): this was printed by AnActor.foo()
MainThread: printing result ... (blocking)
MainThread: this was returned by AnActor.bar() after a delay
MainThread: reading AnActor.field ...
MainThread: printing result ... (blocking)
MainThread: this is the value of AnActor.field
MainThread: writing AnActor.field ...
MainThread: printing new field value ... (blocking)
MainThread: new value
```
