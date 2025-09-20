# Deadlock debugging

This is a complete example of how to use
[`log_thread_tracebacks()`][pykka.debug.log_thread_tracebacks]
as a signal handler to debug deadlocks.

## Setting up a deadlock

To illustrate how to debug a deadlock,
we can use the following script to set up a deadlock situation.

```title="examples/deadlock.py"
--8<-- "examples/deadlock.py"
```

Running the script outputs the following:

```console
❯ uv run examples/deadlock.py
Setting up logging to get output from signal handler...
Registering signal handler...
Starting actors...
DEBUG:pykka:Registered ActorA (urn:uuid:09d5a2ab-6d1b-4fb6-aa7f-9b3d519b2378)
DEBUG:pykka:Starting ActorA (urn:uuid:09d5a2ab-6d1b-4fb6-aa7f-9b3d519b2378)
DEBUG:pykka:Registered ActorB (urn:uuid:9b4c697c-fe1c-44eb-b596-bf4dd8e3c4e9)
DEBUG:pykka:Starting ActorB (urn:uuid:9b4c697c-fe1c-44eb-b596-bf4dd8e3c4e9)
Now doing something stupid that will deadlock the actors...
DEBUG:__main__:This is foo calling bar
DEBUG:__main__:This is bar calling foo; BOOM!
Making main thread relax; not block, not quit
1) Use `kill -SIGUSR1 1953031` to log thread tracebacks
2) Then `kill 1953031` to terminate the process
```

## How to debug the deadlock

The two actors are now deadlocked waiting for each other,
while the main thread is idling, ready to process any signals.

To debug the deadlock,
send the `SIGUSR1` signal to the process,
which has process ID 1953031 in this example:

```console
$ kill -SIGUSR1 1953031
$
```

This makes the main thread log the current traceback for each thread.
The logging output shows that
the two actors are both waiting for data from the other actor:

```console hl_lines="15 35"
CRITICAL:pykka:Current state of ActorB-2 (_actor_loop) (ident: 140349254620864):
  File "threading.py", line 1043, in _bootstrap
    self._bootstrap_inner()
  File "threading.py", line 1081, in _bootstrap_inner
    self._context.run(self.run)
  File "threading.py", line 1023, in run
    self._target(*self._args, **self._kwargs)
  File "pykka/_actor.py", line 229, in _actor_loop
    self._actor_loop_running()
  File "pykka/_actor.py", line 242, in _actor_loop_running
    response = self._handle_receive(envelope.message)
  File "pykka/_actor.py", line 352, in _handle_receive
    return callee(*message.args, **message.kwargs)
  File "examples/deadlock.py", line 35, in bar
    return self.a.foo().get()
  File "pykka/_threading.py", line 69, in get
    self._condition.wait(timeout=remaining)
  File "threading.py", line 369, in wait
    waiter.acquire()

CRITICAL:pykka:Current state of ActorA-1 (_actor_loop) (ident: 140349263013568):
  File "threading.py", line 1043, in _bootstrap
    self._bootstrap_inner()
  File "threading.py", line 1081, in _bootstrap_inner
    self._context.run(self.run)
  File "threading.py", line 1023, in run
    self._target(*self._args, **self._kwargs)
  File "pykka/_actor.py", line 229, in _actor_loop
    self._actor_loop_running()
  File "pykka/_actor.py", line 242, in _actor_loop_running
    response = self._handle_receive(envelope.message)
  File "pykka/_actor.py", line 352, in _handle_receive
    return callee(*message.args, **message.kwargs)
  File "examples/deadlock.py", line 25, in foo
    return b.bar().get()
  File "pykka/_threading.py", line 69, in get
    self._condition.wait(timeout=remaining)
  File "threading.py", line 369, in wait
    waiter.acquire()

CRITICAL:pykka:Current state of MainThread (ident: 140349271754624):
  File "examples/deadlock.py", line 59, in <module>
    time.sleep(1)
  File "pykka/debug.py", line 62, in log_thread_tracebacks
    stack = "".join(traceback.format_stack(frame))
```
