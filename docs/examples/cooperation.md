# Cooperating actors

This example shows how multiple actors can be set up to cooperate with each
other by passing either [`ActorRef`][pykka.ActorRef] or
[`ActorProxy`][pykka.ActorProxy] instances to actors, either at setup time as
arguments to [`start()`][pykka.Actor.start] or later through messages.

## Example

```title="examples/cooperation.py"
--8<-- "examples/cooperation.py"
```

## Output

```console
$ uv run examples/cooperation.py
Adder is adding 1 to 0
Bookkeeper got 1 back
Adder is adding 1 to 1
Bookkeeper got 2 back
Adder is adding 1 to 2
Bookkeeper got 3 back
Adder is adding 1 to 3
Bookkeeper got 4 back
Adder is adding 1 to 4
Bookkeeper got 5 back
```
