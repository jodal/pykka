# Actor with proxy

## Example

```title="examples/typed_actor.py"
--8<-- "examples/typed_actor.py"
```

## Output

```text
MainThread: calling AnActor.proc() ...
MainThread: calling AnActor.func() ...
MainThread: printing result ... (blocking)
AnActor-1: this was printed by AnActor.proc()
MainThread: this was returned by AnActor.func() after a delay
MainThread: reading AnActor.field ...
MainThread: printing result ... (blocking)
MainThread: this is the value of AnActor.field
MainThread: writing AnActor.field ...
MainThread: printing new field value ... (blocking)
MainThread: new value
MainThread: calling AnActor.proc() ...
MainThread: calling AnActor.func() ...
MainThread: printing result ... (blocking)
AnActor-1: this was printed by AnActor.proc()
MainThread: this was returned by AnActor.func() after a delay
MainThread: reading AnActor.field ...
MainThread: printing result ... (blocking)
MainThread: new value
MainThread: writing AnActor.field ...
MainThread: printing new field value ... (blocking)
MainThread: new value
MainThread: calling AnActor.proc() ...
MainThread: calling AnActor.func() ...
AnActor-1: this was printed by AnActor.proc()
MainThread: printing result ... (blocking)
MainThread: this was returned by AnActor.func() after a delay
MainThread: reading AnActor.field ...
MainThread: printing result ... (blocking)
MainThread: new value
MainThread: writing AnActor.field ...
MainThread: printing new field value ... (blocking)
MainThread: new value
```
