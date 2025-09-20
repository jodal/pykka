# The actor model

Pykka is a Python implementation of the actor model,
which is a model that treats message-passing "actors" as
the basic building blocks of concurrent computation.

You can learn more about the actor model in general at
[Wikipedia](https://en.wikipedia.org/wiki/Actor_model).

## Rules

The actor model introduces some simple rules to control the sharing of state
and cooperation between execution units,
which makes it easier to build concurrent applications.

- An actor is an execution unit that
  executes concurrently with other actors.

- An actor does not share state with anybody else,
  but it can have its own state.

- An actor can only communicate with other actors
  by sending and receiving messages.
  It can only send messages to actors whose address it has.

- When an actor receives a message it may take actions like:

    - altering its own state,
      e.g. so that it can react differently to a future message,
    - sending messages to other actors, or
    - starting new actors.

    None of the actions are required, and they may be applied in any
    order.

- An actor only processes one message at a time.
  In other words, a single actor does not give you any concurrency,
  and it does not need to use locks internally to protect its own state.
