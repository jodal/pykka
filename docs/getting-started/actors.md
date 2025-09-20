# Message-processing actor

In its most basic form,
a Pykka actor is a class with
an [`on_receive(message)`][pykka.Actor.on_receive] method:

```py
import pykka

class Greeter(pykka.ThreadingActor):
    def on_receive(self, message):
        print("Hi there!")
```

## Starting an actor

To start an actor,
you call the class' [`start()`][pykka.Actor.start] method,
which starts the actor and returns an actor reference
which can be used to communicate with the running actor:

```py
actor_ref = Greeter.start()
```

If you need to pass arguments to the actor upon creation,
you can pass them to the [`start()`][pykka.Actor.start] method.
The actor receives the arguments using the regular `__init__()` method:

```py
import pykka

class Greeter(pykka.ThreadingActor):
    def __init__(self, greeting="Default greeting"):
        super().__init__()
        self.greeting = greeting

    def on_receive(self, message):
        print(self.greeting)

actor_ref = Greeter.start(greeting="Hi you!")
```

It can be useful to know that the `__init__()` method
is run in the execution context that starts the actor.
There are also hooks for running code in the actor's own execution context
when the actor [starts][pykka.Actor.on_start],
when it [stops][pykka.Actor.on_stop],
and when [an unhandled exception is raised][pykka.Actor.on_failure].
Check out the full API docs for the details.

## Stopping an actor

To stop an actor,
you can call [`stop()`][pykka.ActorRef.stop]
on the [`ActorRef`][pykka.ActorRef] object:

```py
actor_ref.stop()
```

If an actor wants to stop itself,
it can call [`stop()`][pykka.Actor.stop] on itself.
It will then exit as soon as it has finished processing
the messages currently queued in its inbox.

```py
self.stop()
```

Once an actor has been stopped, it cannot be restarted.

## Sending messages

To send a message to the actor, you can either use the
[`tell()`][pykka.ActorRef.tell] method or the
[`ask()`][pykka.ActorRef.ask] method on the
[`ActorRef`][pykka.ActorRef] object:

- [`tell(message)`][pykka.ActorRef.tell] will fire off a message without waiting for an
  answer. In other words, it will never block.
- [`ask(message)`][pykka.ActorRef.ask] will by default block until an answer is
  returned, potentially forever. If you provide a `timeout` keyword argument,
  you can specify for how long it should wait for an answer. If you want an
  answer, but don't need it right away because you have other stuff you can do
  first, you can use `ask(block=False)`, and it will immediately return a
  "future" object.

The message itself can be of any type, for example a dict or your own
message class type.

/// warning | Mutable messages
For performance reasons, Pykka **does not** clone the message you send
before delivering it to the receiver. You are yourself responsible for
either using immutable data structures or to
[`copy.deepcopy()`][copy.deepcopy] the data you're sending off to other
actors.
///

Summarized in code:

```py
actor_ref.tell("Hi!")
# => Returns nothing. Will never block.

answer = actor_ref.ask("Hi?")
# => May block forever waiting for an answer

answer = actor_ref.ask("Hi?", timeout=3)
# => May wait 3s for an answer, then raises exception if no answer.

future = actor_ref.ask("Hi?", block=False)
# => Will return a future object immediately.
answer = future.get()
# => May block forever waiting for an answer
answer = future.get(timeout=0.1)
# => May wait 0.1s for an answer, then raises exception if no answer.
```

## Replying to messages

If a message is sent using [`actor_ref.ask()`][pykka.ActorRef.ask] you can reply
to the sender of the message by simply returning a value from the
[`on_receive(message)`][pykka.Actor.on_receive] method:

```py
import pykka

class Greeter(pykka.ThreadingActor):
    def on_receive(self, message):
        return "Hi there!"

actor_ref = Greeter.start()

answer = actor_ref.ask("Hi?")
print(answer)
# => "Hi there!"
```

/// note | Returning `None`
`None` is a valid response,
so if you return `None` explicitly, or don't return at all,
a response containing `None` will be returned to the sender.
///

From the point of view of the actor it doesn't matter whether the
message was sent using [`tell()`][pykka.ActorRef.tell]
or [`ask()`][pykka.ActorRef.ask].
When the sender doesn't expect a response the
[`on_receive()`][pykka.Actor.on_receive] return value will be ignored.

The situation is similar in regard to exceptions:
when [`ask()`][pykka.ActorRef.ask] is used and you raise an exception from
within the [`on_receive()`][pykka.Actor.on_receive] method,
the exception will propagate to the sender:

```py
import pykka

class Raiser(pykka.ThreadingActor):
    def on_receive(self, message):
        raise Exception("Oops")

actor_ref = Raiser.start()

try:
    actor_ref.ask("How are you?")
except Exception as e:
    print(repr(e))
    # => Exception("Oops")
```
