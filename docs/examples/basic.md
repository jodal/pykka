# Basic actor

This example shows:

- how to define an actor by creating a class that subclasses
  [`ThreadingActor`][pykka.ThreadingActor] and defines the
  [`on_receive()`][pykka.Actor.on_receive] method,
- how the actor can store internal state, here done by modifying
  `self._stored_messages`,
- how to start and stop and actor, using [`start()`][pykka.Actor.start] and
  [`stop()`][pykka.ActorRef.stop], and
- how to interact with the actor from the outside, using
  [`tell()`][pykka.ActorRef.tell] and [`ask()`][pykka.ActorRef.ask].

## Example

```title="examples/basic.py"
--8<-- "examples/basic.py"
```

## Output

```console
$ uv run examples/basic.py
[{'no': 'Norway', 'se': 'Sweden'}, {'a': 3, 'b': 4, 'c': 5}]
```
