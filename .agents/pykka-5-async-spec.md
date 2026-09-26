# Pykka 5: async actors design spec

Status: design, ready for implementation.
Glossary: `CONTEXT.md`, kept outside the repo.

## Goal

Pykka 5 adds actors that run on async event loops: asyncio, and trio through
anyio.

- One process can run a mix of threading actors and async actors.
- Actors on different runtimes can send messages to each other with `tell()`,
  `ask()`, and proxies.
- Existing Pykka users continue to work without code changes. This includes
  projects that run their tests with warnings as errors.

## Non-goals

These are out of scope for Pykka 5:

- A process actor runtime. The design must only keep the door open; see
  [Keep the door open to processes](#keep-the-door-open-to-processes).
- Supervision: links, monitors, and restart strategies for child actors.
- Handler cancellation by callers (discussion #202).
- Bounded inboxes and backpressure.
- Timers (GitHub #44).

## Compatibility

- **Python 3.13 or later.** Mopidy, the main downstream user, already requires
  3.13. Every distribution release that can package Pykka 5 with its own anyio
  has 3.13 or later (Debian stable and testing, Ubuntu 26.04 LTS). Users on
  Python 3.11 and 3.12 can stay on Pykka 4. A later increase of the floor needs
  a specific technical reason, and the floor never goes above the Python in
  Debian stable.
- **anyio is a hard dependency.** It is added with the first slice that uses
  it (slice 7). Pykka imports it only when async code runs, so threading-only
  programs pay no import cost. The anyio minimum is the
  oldest version that has what the implementation uses, with a target of 4.8
  or older (Debian stable). A package with trio actors depends on trio itself.
- **Allowed breaks in 5.0:**
  - private things: the `_create_actor_inbox()`, `_create_future()`, and
    `_start_actor_loop()` hooks, `Envelope`, the `ActorInbox` protocol, and
    the names of all private internals, which get a `_pykka_` prefix (see
    [Names on actor classes](#names-on-actor-classes))
  - behavior that is wrong in async code: `await future` stops blocking the
    event loop
  - the Python floor
- **Intended behavior changes for existing code:**
  - `await future` no longer blocks the loop, so other tasks run while a
    caller waits (GitHub #99).
  - A wait for a reply from the actor itself raises `RuntimeError` at once
    instead of hanging (see [Message order](#message-order)).
  - `ask()` returns a plain `Future`, so `isinstance(f, ThreadingFuture)` is
    `False` for futures that Pykka makes.
  - Code that moves from `stop()` to `actor_stop()`: a second call does
    nothing, where `stop()` queues a second stop message, or raises
    `ActorDeadError` if the actor has stopped (see
    [Names on actor classes](#names-on-actor-classes)).

## Runtimes and backends

A **runtime** is the way an actor executes: the threading runtime or the async
runtime. A **backend** is the event loop library under the async runtime:
asyncio or trio.

- The async runtime uses anyio for all loop-side parts: tasks, task groups,
  events, and cancellation.
- anyio has no non-blocking send from a foreign thread, so a small internal
  shim sends from a thread to a loop with the native non-blocking call for
  each backend:
  - asyncio: `asyncio.get_running_loop()` and `loop.call_soon_threadsafe()`
  - trio: `trio.lowlevel.current_trio_token()` and `TrioToken.run_sync_soon()`.
    The callback must never raise, because an exception becomes
    `TrioInternalError`.
- One process can have many loops with both backends, each loop in its own
  thread.

## Actor classes

```python
class Player(pykka.AsyncioActor):     # or TrioActor, AnyioActor
    async def on_actor_start(self) -> None: ...

    async def play(self, uri: str) -> bool: ...

    def stop(self) -> None: ...            # a domain method, not Pykka's

    def get_position(self) -> float: ...   # plain methods are allowed


ref = Player.actor_start()
```

- `pykka.AsyncioActor`, `pykka.TrioActor`, and `pykka.AnyioActor` share the
  abstract base `pykka.AsyncActor`. The class that you subclass is the backend
  declaration. It is required, because a caller of `actor_start()` cannot know
  what a plug-in actor needs. An `AnyioActor` uses only anyio APIs and runs on
  any backend.
- A subclass inherits the backend. A class that mixes two backends, or that
  subclasses `AsyncActor` directly, raises an error when it is defined
  (`__init_subclass__`).
- **Hooks are always `async def`** in async actors: `on_actor_start()`,
  `on_actor_stop()`, `on_actor_failure()`, and `on_actor_receive()`.
  `AsyncActor` declares them that way, and a sync hook raises an error when
  the class is defined. A hook with no `await` in it is still a valid
  `async def`.
- **Migration piece by piece.** A `ThreadingActor` moves to async in three
  steps:
  1. Rename its hooks to the `on_actor_*()` names. This works on
     `ThreadingActor` in 5.0 and has nothing to do with async.
  2. Change the base class (for example to `AsyncioActor`), and add `async` to
     the hooks. Blocking calls in the actor (for example
     `other_ref.ask(msg)`) must become `await`s, because they raise inside
     async actors.
  3. Convert the other methods to `async def` one at a time. Plain methods
     stay allowed.

  Sync hooks were considered to make step 2 smaller, but after the hook rename
  they would only save the `async` keyword on at most four hooks. They would
  cost a `None | Awaitable[None]` return type in the base class and two ways to
  write the same hook.
- The sync hooks and the sync actor loop move from `Actor` to
  `ThreadingActor`. `Actor` keeps only what all runtimes share:
  `actor_start()` (and its alias `start()`), `actor_stop()`, `actor_ref`,
  `actor_urn`, and `actor_context`. Existing `ThreadingActor` subclasses are
  not affected.
- A proxy can call both `async def` and plain methods on an async actor. The
  actor awaits any method result that is a coroutine. Plain methods run on the
  loop directly, so a slow plain method stops the loop while it runs. Attribute
  reads and writes through the proxy work as today.
- `actor_start()` stays a sync call from anywhere, the same on all runtimes. It
  runs `__init__()` in the caller's thread (with the new actor's context as
  the current context), schedules the actor, and returns the `ActorRef` at
  once. `on_actor_start()` runs later in the actor's task.
  There is no async variant.

## Names on actor classes

Pykka's names on actor classes get prefixes, so that they do not conflict with
names in users' actor subclasses, as Pydantic 2 did with `model_` and
`__pydantic_`.

- **Private internals** get a `_pykka_` prefix, for example `_pykka_stop()`,
  `_pykka_actor_loop()`, and `_pykka_handle_receive()`. Today a user's private
  helper `_stop()` silently replaces Pykka's internal `_stop()`. Name mangling
  (`__stop`) is not used, because `ThreadingActor` and `AsyncActor` override
  some internals.
- **`actor_start()`** is the main classmethod, and all Pykka docs, docstrings,
  examples, and tests use it. `start` stays as an alias with **no**
  deprecation, so existing code does not change. An actor may define its own
  `start()`: it hides the alias in that class, and the actor is started with
  `actor_start()`. The docs say clearly that this is safe and supported. With
  mypy or ty, the user's `start()` needs `# type: ignore[override]`;
  basedpyright accepts it.
- **`actor_stop() -> None`** is the safe way for an actor to stop itself. It
  keeps the inbox order of today's `Actor.stop()`: the stop message goes to
  the end of the inbox, so messages that already wait are handled first.
  Mopidy depends on this. It does nothing if the actor is already stopping.
  This is a change: today's `stop()` queues a second stop message, or raises
  `ActorDeadError` if the actor has stopped. It returns nothing, because an actor
  cannot wait for its own stop (that is a self-wait). Stopping after the
  current message and dropping the rest (#46) is a separate feature, not in
  5.0. `stop()` is deprecated, so that `stop` becomes free
  for users' own methods, for example in a `Player` actor. Today's docs say
  that `stop()` is "equivalent to `ActorRef.stop(block=False)`", but that
  method returns a `Future[bool]` and does not raise for a dead actor.
- **Hooks** are `on_actor_start()`, `on_actor_stop()`, `on_actor_failure()`,
  and `on_actor_receive()`. The prefix makes it clear which callbacks are
  Pykka's, for example in Mopidy's Audio actor, which also gets callbacks from
  GStreamer. On `ThreadingActor`, the new hooks call the old ones by default
  (`on_actor_start()` calls `self.on_start()`), so old subclasses keep
  working. `AsyncActor` has only the new names.
- **Daemon threads** are set with a class keyword:
  `class Worker(pykka.ThreadingActor, daemon=True):`. `__init_subclass__`
  stores the value as `_pykka_daemon_thread`, so no public name goes into the
  user's class. The value is checked when the class is defined and is
  inherited by subclasses. `use_daemon_thread = True` keeps working, but it is
  deprecated.
- **Public attributes** keep their names: `actor_urn`, `actor_ref`,
  `actor_context`, and `actor_task_group` already have the `actor_` prefix.

## Actor systems and contexts

An **actor system** is the root of a tree of actor contexts, with its own
registry and teardown. It is the one thing that users set up. An **actor
context** is an actor's place in the tree (as `ActorContext` in Akka). It is
not Python's `contextvars.Context`.

```python
with pykka.ActorSystem() as system: ...                        # sync
async with pykka.ActorSystem() as system: ...                  # async, own loops
async with pykka.ActorSystem.on_current_loop() as system: ...  # share this loop
```

- **Default system.** Pykka makes a default system when the user does not make
  one. Programs that never make a system work as today.
- **`ActorSystem()`** makes a root context without a loop. Async actors in it
  get loop threads that Pykka makes.
- **`ActorSystem.on_current_loop()`** makes a new system whose root adopts the
  running loop (asyncio or trio; anyio detects the backend). Compatible actors
  that start in it run as tasks on this loop. A program with one thread, one
  loop, and many actors opens it once around `main()`. Code outside the block
  does not see those actors in lookups, but messages still work.
- **Loop options.** `pykka.ActorSystem(backend_options={"asyncio": {...}})`
  sets options for all loops that Pykka makes in the system, for each backend,
  for example `{"asyncio": {"use_uvloop": True}}` or asyncio debug mode. The
  program sets them, not actors or extensions: Mopidy, for example, could set
  them from its config. Pykka passes them to anyio's `BlockingPortalProvider`
  without checks. The default system and `on_current_loop()` have no options.
  anyio 4.8 takes `debug`, `loop_factory`, and `use_uvloop` for asyncio, and
  ignores all options for trio, so the docs say that trio options may have no
  effect.
- **Entering later.** A system can be made first and entered later with
  `with system:`.
- **Messages cross systems.** A ref is a ref. Isolation covers lookups and
  teardown, not messages.
- **Current context.** `actor_start()` finds the current context through a
  `ContextVar`, and the new actor's context is a child of it. Pykka sets the
  variable in actor threads and actor tasks.
- **`__init__()` runs in the new context.** `actor_start()` makes the new
  actor's context first, sets the `ContextVar` to it while `__init__()` runs,
  and then resets it. So an actor that starts helper actors in its
  `__init__()` becomes their parent. Without this, `__init__()` would run in
  the caller's context, and the helpers would become children of the caller.
- **Threads that user code starts** (`threading.Thread`,
  `ThreadPoolExecutor.submit()`) do not copy context variables, so they use the
  default system. The docs show two ways to get full isolation:
  - carry the context by hand: `contextvars.copy_context().run`, or
    `Thread(context=...)` on Python 3.14
  - run Python 3.14 or later with `-X thread_inherit_context=1` or
    `PYTHON_THREAD_INHERIT_CONTEXT=1`
- **No lifetime links.** A stopped actor does not affect the actors that it
  started, on any runtime, as today.

### Context contents

- A context holds `parent`, `children`, `actor_ref` (`None` for a root),
  `system`, and private loop fields.
- It holds the actor's `ActorRef`, not the actor, so a stopped actor instance
  can be freed at once. `ActorRef` and `ActorContext` stay separate objects:
  the ref is the small handle that is shared (and later serialized), and the
  context is in-process structure.
- When an actor stops while its children still run, its node stays in the tree
  (marked as stopped) until all its descendants have stopped.
- Public and read-only: `ActorContext.current()`, `ctx.parent`,
  `ctx.children`, `ctx.actor_ref`, `ctx.system`, `ctx.inbox_size`, and
  `Actor.actor_context`. Users never make an `ActorContext`.

### Loop choice on `actor_start()`

1. If the inherited loop matches the declared backend, the actor runs on it. An
   `AnyioActor` matches any loop.
2. Else the actor gets the loop of its nearest threading context for that
   backend. Pykka makes it on first need with anyio's
   `BlockingPortalProvider`: one loop thread for each (threading context,
   backend). The actor's children then inherit that loop.
3. An `AnyioActor` in a threading context uses a loop that the context already
   has. If there is none, the context gets an asyncio loop.
4. Each actor on a Pykka-made loop holds a lease. The loop thread exits when
   the last actor on it has stopped. A parent that stops does not stop its
   children.
5. A start from another thread uses `BlockingPortal.start_task_soon()`, which
   blocks the caller for a short time. A start from the loop thread uses the
   task group directly, because portal calls from the loop thread raise
   `RuntimeError`.

### System API

- `system.stop()` returns a `Future`: `system.stop().get()` in sync code,
  `await system.stop()` in async code. The exit of `with`/`async with` calls
  `stop()` and waits.
- The actors stop one at a time in reverse start order on all runtimes and
  loops. This is today's `stop_all()` rule, and it already stops every child
  before its parent.
- Then the loop threads that Pykka made for the system exit.
- An explicit system is closed after `stop()`: `actor_start()` in it raises an
  error. The default system never closes, so `stop()` on it (and
  `ActorRegistry.stop_all()`) stops its actors, and new actors can start
  afterwards, as today.
- `pykka.ActorSystem.current()` gives the system of the current context.
- Lookups replace `ActorRegistry`:

| `ActorRegistry` (deprecated) | `ActorSystem` |
|---|---|
| `get_all()` | `refs()` |
| `get_by_class(cls)` | `refs(cls)`, typed as `list[ActorRef[A]]` |
| `get_by_class_name(name)` | `refs(name)` |
| `get_by_urn(urn)` | `ref(urn)`, returns `None` if no actor has the URN |
| `broadcast(msg, target_class=None)` | `broadcast(msg, target=None)` |
| `stop_all()` | `stop()` |
| `register()`, `unregister()` | private |

- `system.broadcast(msg, target=None)` accepts `None` (all actors in the
  system), an actor class or a class name (passed to `refs()`), or an iterable
  of refs. It skips actors that have stopped, where today's
  `ActorRegistry.broadcast()` can raise `ActorDeadError` halfway through.
- Until removal, `ActorRegistry`'s classmethods act on the current system.

### Design rule

New APIs return a `Future` and do not come in sync/async pairs. `.get()` waits
in a thread, and `await` waits on a loop. `ActorRef.aask()` and
`ActorRef.astop()` are the only exception, because the old `ask()` and
`stop()` default to `block=True`.

## Futures

- **One type.** `pykka.Future` becomes the one concrete, thread-safe future
  class. The caller chooses how to wait when it waits:
  - `.get(timeout=...)` blocks the calling thread, as today.
  - `await future` waits on the caller's loop (asyncio or trio) without
    blocking and without a thread for each await. When the value is set, the
    future wakes each waiter directly on the same loop, or through the shim for
    other loops.
  - The value can be read many times, with either way of waiting.
- **`__await__`** is only the async path. Outside a running asyncio or trio
  loop it raises an error with a clear message, with no blocking fallback.
- **`__iter__`** keeps today's behavior (yield `None` once, then a blocking
  `get()`) as its own method, for `yield from future` in `@types.coroutine`
  generators. It is deprecated.
- **`ask()`** and proxy calls make a plain `Future`. The receiver no longer
  chooses the future type.
- **`ThreadingFuture`** stays as an empty subclass of `Future`, so that it can
  be deprecated separately.
- **`map()`, `filter()`, `join()`, and `reduce()`** stay lazy. The function
  runs where the value is read: in the calling thread for `.get()`, or in the
  awaiting task after a non-blocking await of the sources. The actor never runs
  the caller's function.
- **`set_get_hook()`** still works. An `await` on a future with a get hook
  runs the hook in a worker thread (`anyio.to_thread.run_sync()`). It is
  deprecated.
- **New `pykka.gather(futures) -> Future[list[T]]`.** It takes any iterable,
  also an empty one: `await pykka.gather(fs)` or `pykka.gather(fs).get()`. It
  replaces `get_all()`.
- **Cancellation.** A cancelled `await` (for example by `anyio.fail_after()`)
  only stops waiting. The future stays valid, and the actor still handles the
  message.
- **Async callers of `ActorRef`** use `await ref.aask(msg)` and
  `await ref.astop()`. They work for any receiver and take no `timeout`: async
  code uses cancel scopes. The sync `ask()` and `stop()` do not change.

## Inbox

- **One `Inbox` class for all runtimes:** a thread-safe queue (for example a
  `deque` and a lock) with one waiter slot for the receiving actor.
- **`put()`** is the same for every sender: a thread, a threading actor, a task
  on the same loop, or a task on another loop. It adds the envelope without
  waiting. It wakes the receiver only if the receiver waits: a threading actor
  through a `threading.Condition`, an async actor through an event on its loop
  (set directly on the same loop, or through the shim). A burst of messages to
  a busy actor costs no wake-ups.
- **Order.** Messages from one sender arrive in the order that it sent them.
- **Unbounded.** `tell()` never waits.
- **Risk.** The idle flag and the wake-up must be free of lost wake-ups. If
  that becomes hard to get right for async receivers, the fallback is an
  unbounded anyio memory object stream for async actors, with one shim call for
  each cross-thread message.
- **`actor_inbox`.** On threading actors and their refs it stays and still
  works, because the `Inbox` keeps queue-like names (`put`, `get`, `empty`,
  `qsize`). It is deprecated. Async actors never get a public inbox:
  `ActorRef.actor_inbox` on a ref to an async actor raises `AttributeError`.

## Message order

- **Strict order.** An async actor awaits each handler to the end before it
  takes the next message. No other handler changes the actor's state while a
  handler awaits, the same guarantee as for threading actors.
- **Background tasks.** Each async actor has an anyio task group from Pykka,
  `self.actor_task_group`. Its tasks run next to the handlers on the same loop
  and are cancelled when the actor stops. The pattern for slow work: start a
  task, and let it `tell()` the result back to the actor. An exception that no
  task catches fails the actor, the same as a failed `tell()` handler.
- **Self-wait.** An actor on any runtime that waits for a reply from itself
  raises `RuntimeError` at once, with a hint to call the method directly or to
  use `tell()`. This covers `aask()` and `ask(block=True)` to its own ref
  (checked before sending), and `await` or `.get()` on a future whose receiver
  is the current actor (checked when waiting; the message still gets handled
  later). For threading actors this turns a hang into an error.

## Blocking calls

Blocking calls are `Future.get()`, `ask(block=True)`, `stop(block=True)`,
`ActorRegistry.stop_all(block=True)`, and `gather(...).get()`.

- **Inside an async actor, on its loop thread:** they always raise
  `RuntimeError`, with a hint to use `await`.
- **Other code on a loop thread** (for example a Tornado or FastAPI handler
  that calls a threading actor): the call works as today. It raises at once if
  the reply must come from the same loop, which is a sure deadlock. A
  `DeprecationWarning` that points to `await` comes with the runtime warnings,
  at least six months after 5.0 (see [Deprecations](#deprecations)).
- **Detection.**
  - A loop thread is a thread that runs an asyncio or trio loop right now.
  - `ask()` and proxy calls tag their future with the receiver's loop, and
    derived futures carry the tags of their sources. Futures that users make
    have no tag.
  - Worker threads (`anyio.to_thread.run_sync()`) are not loop threads, so the
    check looks at the thread, not only at the context variable.
  - Indirect deadlocks through other threads are not detected. Timeouts are
    the protection, as today.

## Lifecycle and failure

- **Stop sequence:**
  1. The stop message waits in the inbox behind earlier messages.
  2. The actor is marked as stopped (unregistered, `is_alive()` is `False`).
  3. `on_actor_stop()` runs (and is awaited if it is `async def`) while the
     background tasks still run.
  4. The tasks that are left are cancelled, and Pykka waits for them.
  5. Messages left in the inbox are handled as today: each `ask()` gets
     `ActorDeadError`, and each `tell()` is dropped.
- **Failures, the same as threading actors:**
  - If `on_actor_start()` raises, Pykka logs the error and stops the actor,
    without `on_actor_failure()` or `on_actor_stop()`.
  - If a `tell()` handler or a background task raises, Pykka logs the error,
    calls `on_actor_failure()`, and stops the actor.
  - If an `ask()` handler raises, the exception goes to the caller, and the
    actor continues.
  - If `on_actor_stop()` or `on_actor_failure()` raises, Pykka logs the error
    and stops the actor.
- **Cancellation from outside.** When the task that holds the system is
  cancelled (Ctrl-C in trio, a test timeout), the actor stops at once: the
  handler in progress is cancelled (a waiting `ask()` gets `ActorDeadError`),
  `on_actor_stop()` runs in a shielded cancel scope with no time limit, the
  background tasks are cancelled, and the inbox is drained.
- **`BaseException`.** A cancellation exception (`asyncio.CancelledError`,
  `trio.Cancelled`) stops only the actor. Any other `BaseException` (for
  example `SystemExit`) stops the actor and then its system. For the default
  system, this is today's "stop all actors".
- **One teardown path.** On each runtime, every way that an actor can end must
  go through one teardown step, and only that step updates the actor's
  context node. The ways are: a clean stop, `on_actor_start()` raises, a
  `tell()` handler or a background task raises, a `BaseException`, and (async
  only) cancellation from outside, after the shielded `on_actor_stop()`. The
  teardown step marks the node as stopped, resets the `ContextVar`, and
  removes the node only if it has no running descendants. When a node is
  removed, the step checks its parent in the same way, up the tree. Today's
  threading loop already has this shape: every exit path ends in
  `_actor_loop_teardown()`.
- **`actor_stopped`** stays a `threading.Event` on all actors and refs. It is
  deprecated in favor of `ref.is_alive()` and the `Future` from
  `ActorRef.stop(block=False)`.

## Proxy typing

- `pykka.typing.proxy_method()` gets two overloads: a function that returns
  `Coroutine[Any, Any, T]` and a function that returns `T`. Both give
  `Method[P, Future[T]]`. Users write the same proxy classes as today.
- One `ActorMemberMixin` works for all actors, because the hooks give
  `Future[None]` either way. It uses the new names (`on_actor_*()` and
  `actor_stop()`), and it can no longer refer to the hooks on `Actor`, which
  move to `ThreadingActor`.
- A prototype gave the expected types on basedpyright (strict), mypy, and ty:
  `await player.play(...)` and `player.play(...).get()` are `bool` for
  `async def play(...) -> bool`, and `await gather([...])` is `list[float]`.

## Debug tools

- `pykka.debug.log_actor_tree()` sits next to `log_thread_tracebacks()` and has
  the same signal-handler form. It logs the tree of every system at `CRITICAL`
  level, one line for each actor: class, short URN, runtime and backend, thread
  or loop thread, stopped state, and inbox size. It reads a consistent snapshot
  under a lock.

  ```text
  ActorSystem default
  ├─ Core (a1b2c3) threading, thread Core-1, inbox 0
  │  └─ Http (d4e5f6) asyncio, loop thread pykka-asyncio-1, inbox 12
  └─ [stopped] Scanner (789abc) threading
     └─ Worker (def012) anyio/asyncio, loop thread pykka-asyncio-2, inbox 0
  ```

- Stacks of async tasks are not included. Python 3.14 has
  `python -m asyncio ps` and `pstree` for that.

## Deprecations

There are three levels:

1. **In 5.0:** `@warnings.deprecated(msg, category=None)`. Type checkers flag
   every use, and the docs mark the API, but there is no runtime warning.
2. **In a 5.x release at least six months after 5.0:** a runtime
   `DeprecationWarning`.
3. **In 6.0:** removal.

| Deprecated in 5.0 | Replacement |
|---|---|
| `ThreadingFuture` | `pykka.Future` |
| `get_all()` | `pykka.gather()` |
| `Future.set_get_hook()` | none |
| `Future.__iter__` | `await future` |
| `actor_inbox` (threading actors) | none; `ActorContext.inbox_size` for inspection |
| `actor_stopped` | `ActorRef.is_alive()`, `ActorRef.stop(block=False)` |
| `ActorRegistry` | `ActorSystem` (see [System API](#system-api)) |
| `Actor.stop()` | `Actor.actor_stop()` |
| `on_start()`, `on_stop()`, `on_failure()`, `on_receive()` | `on_actor_start()`, `on_actor_stop()`, `on_actor_failure()`, `on_actor_receive()` |
| `use_daemon_thread = True` | `class Worker(pykka.ThreadingActor, daemon=True)` |

`Actor.start()` is **not** deprecated. `actor_start()` is the main name, and
`start` stays as an alias.

Some deprecations cannot be level 1, because type checkers cannot see them:

- Blocking calls on a loop thread outside async actors, because type checkers
  cannot see threads.
- The old hook names and `use_daemon_thread`, because type checkers do not
  flag an override of a deprecated method or class attribute (tested on
  basedpyright, mypy, and ty). In 5.0 they are deprecated in the docs only.

For these, the runtime warning comes at level 2: for blocking calls when they
happen, and for hooks and `use_daemon_thread` from `__init_subclass__` when a
subclass defines them.

Each deprecated API gets a "Deprecated: Pykka 5.0" note with its replacement,
in the same style as the "Version added" notes. The migration guide has a
table from old to new APIs.

## Keep the door open to processes

Nothing is built for a process runtime now. New code must not make these
points worse:

1. **`Inbox.put()`** fits a process boundary. A remote sender needs a local
   buffer to keep "`tell()` never waits".
2. **`ActorRef`** must stay small and serializable (URN, class, address). Do
   not add public `ActorRef` attributes that need the actor in the same
   process. A remote `is_alive()` can only give the last known state.
3. **`Envelope`** stays private, so that `reply_to` can change from a local
   `Future` to a reply address later.
4. **Exceptions on futures** are stored as `exc_info` tuples, and tracebacks
   cannot be pickled. A process runtime needs exception serialization.
5. **`ActorProxy`** reads the live actor instance to find its attributes. Do
   not add more proxy behavior that needs the live instance.

## Quality gates

- **Runtimes.** The existing `runtime` fixture in `tests/conftest.py` gets
  `asyncio`, `trio`, and `anyio` actors (anyio on both backends), so the
  shared tests run on all five.
- **Mixed runtimes.** A caller × receiver matrix for `tell`, `ask`/`aask`,
  proxy calls, `gather()`, and stop:
  - callers: a plain thread, a threading actor, an asyncio task, a trio task
  - receivers: a threading actor and each kind of async actor
  - loops in other threads, and `ActorSystem.on_current_loop()`
- **Other tests.** The same-loop deadlock and self-wait checks, cancellation
  from outside, and system isolation with `PYTHON_THREAD_INHERIT_CONTEXT=1`.
- **Versions.** Python 3.13 and 3.14 with the latest dependencies, and a tox
  env `3.13-lowest` with `uv_resolution = "lowest-direct"` for the lowest
  supported versions.
- **Typing.** The proxy typing checks run as typing tests on basedpyright,
  mypy, and ty.
- **Performance.**
  - Before implementation starts, `tests/performance.py` becomes
    `benchmarks/threading_actors.py`, a pyperf benchmark of `tell`, `ask`,
    proxy calls, and start/stop with threading actors only. This is done
    (GitHub #263).
  - The benchmark runs by hand on one machine before each release, pinned to
    one CPU core (`--affinity`) and with `--rigorous`. On two cores, the time
    to wake a sleeping core changes the results by up to 3x.
  - Each run compares the last release from PyPI with the new code, one after
    the other with the same Python version. `benchmarks/README.md` has the
    commands. Results are not stored: timings from different machines, or
    from the same machine at different times, cannot be compared.
  - A result counts only if the spread of `ask` and the proxy cases is about
    1% or less.
  - The means of `ask` and the four proxy cases repeat within 0.5% between
    runs. A release is blocked if one of these five cases
    is more than 10% slower than in the last release.
  - `tell` and start/stop are only reported. The mean of `tell` changes by up
    to 13% between runs, and start/stop mostly measures how fast the kernel
    makes and joins a thread.
  - CI only checks that the benchmark runs.
  - Cross-runtime cases are measured and reported with no limit in 5.0. Later
    releases compare them with 5.0 in the same way.

## Implementation slices

Each slice can be merged and released on its own, and each keeps the full test
suite green. A slice depends only on the slices above it.

1. **Benchmark.** Turn `tests/performance.py` into the threading benchmark in
   `benchmarks/`. This must come first. This is done (GitHub #263).
2. **Python 3.13 floor and tooling.** Require Python 3.13, add the
   `3.13-lowest` tox env, and update the CI matrix.
3. **Unified `Future` for threads.** The thread-safe `Future`, `gather()`,
   `ThreadingFuture` as an empty subclass, lazy `map()`/`filter()`/`join()`/
   `reduce()` without get hooks, `__iter__` as its own method, and `ask()`
   making a plain `Future` (remove `_create_future()`). `await` is not changed
   yet.
4. **`Inbox`.** Replace `queue.Queue` for threading actors with the `Inbox`
   class and its waiter slot. Keep `actor_inbox` working.
5. **Actor context tree and actor systems (sync).** The `ContextVar`, contexts
   with parent and children, `ActorSystem` with `refs()`, `ref()`,
   `broadcast()`, `stop()`, `current()`, closing of explicit systems,
   `ActorRegistry` acting on the current system, the self-wait check, and
   `pykka.debug.log_actor_tree()`. This slice is useful without async. The
   `actor-context` branch (2026-06-08) is a starting point, with 15 tests. It
   needs these changes:
   - one root for each actor system, instead of one global `ROOT`
   - keep a stopped node while its descendants run (the branch removes it at
     once)
   - hold the `ActorRef` instead of a weak reference to the actor
   - set the new context while `__init__()` runs, with a test for actors that
     are started in `__init__()` (the branch makes the context after
     `__init__()`)
   - a public read-only view
   - the one teardown path from [Lifecycle and failure](#lifecycle-and-failure),
     with a test for each exit path: the node is marked as stopped, the
     `ContextVar` is reset, and the node is removed when its last descendant
     has stopped
6. **Class tree and names.** Move the sync hooks and the sync actor loop from
   `Actor` to `ThreadingActor`. Rename the private internals to `_pykka_*`.
   Add `actor_start()` (with `start` as an alias), `actor_stop()`, the
   `on_actor_*()` hooks with the shim to the old names, and the `daemon=True`
   class keyword. Adjust `ActorMemberMixin`.
7. **Async `await` on futures.** anyio as a lazy dependency (the first slice
   that uses it), the thread-to-loop shim for asyncio and trio,
   non-blocking `__await__`, loop-side waiters, get hooks in a worker thread,
   and `aask()`/`astop()` on `ActorRef`. After this slice, async code can
   await threading actors without blocking (GitHub #99).
8. **Async actors on the user's loop.** `AsyncActor`, `AsyncioActor`,
   `TrioActor`, `AnyioActor`, async hooks, coroutine methods through
   proxies, strict order, `actor_task_group`, the async `Inbox` waiter,
   `ActorSystem.on_current_loop()`, and the lifecycle, failure, and
   cancellation rules. The one teardown path gets the same exit-path tests as
   in slice 5, plus cancellation from outside.
9. **Pykka-made loop threads.** `BlockingPortalProvider` loops for each
   (threading context, backend), leases, the loop choice rules on
   `actor_start()`, starts across threads, and `backend_options` on
   `ActorSystem`.
10. **Blocking-call checks.** Loop-thread detection, loop tags on futures, the
    `RuntimeError` inside async actors, and the same-loop deadlock error.
11. **Proxy typing.** The `proxy_method()` overloads and the typing tests.
12. **Deprecations, level 1.** `@warnings.deprecated(..., category=None)` on
    everything in the deprecation table that type checkers can see, and the
    docs notes for all of it.
13. **Docs and migration guide.** Async actors, actor systems, loop sharing,
    loop options, test isolation, the three-step migration from threading to
    async, the new names (`actor_start()` in all examples, and a
    note that an actor's own `start()` is safe), the deprecation table, and an
    update of the runtimes page, which says today that Pykka does not support
    a mix of runtimes.
14. **Release checks.** Run the benchmark against Pykka 4.4.2 with the same
    Python version, and release 5.0.

After 5.0: runtime deprecation warnings (level 2) in a 5.x release at least six
months later, including the warning for blocking calls on a loop thread.
