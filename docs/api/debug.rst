=============
Debug helpers
=============

.. automodule:: pykka.debug
    :members:


Deadlock debugging
==================

This is a complete example of how to use
:func:`log_thread_tracebacks` to debug deadlocks:

.. literalinclude:: ../../examples/deadlock_debugging.py

Running the script outputs the following::

    Setting up logging to get output from signal handler...
    Registering signal handler...
    Starting actors...
    DEBUG:pykka:Registered DeadlockActorA (urn:uuid:60803d09-cf5a-46cc-afdc-0c813e2e6647)
    DEBUG:pykka:Starting DeadlockActorA (urn:uuid:60803d09-cf5a-46cc-afdc-0c813e2e6647)
    DEBUG:pykka:Registered DeadlockActorB (urn:uuid:626adc83-ae35-439c-866a-85a3e29fd42c)
    DEBUG:pykka:Starting DeadlockActorB (urn:uuid:626adc83-ae35-439c-866a-85a3e29fd42c)
    Now doing something stupid that will deadlock the actors...
    DEBUG:root:This is foo calling bar
    DEBUG:root:This is bar calling foo; BOOM!
    Making main thread relax; not block, not quit
    1) Use `kill -SIGUSR1 2284` to log thread tracebacks
    2) Then `kill 2284` to terminate the process

The two actors are now deadlocked waiting for each other while the main
thread is idling, ready to process any signals.

To debug the deadlock, send the ``SIGUSR1`` signal to the process, which has
PID 2284 in this example::

    kill -SIGUSR1 2284

This makes the main thread log the current traceback for each thread.
The logging output shows that the two actors are both waiting for data from the
other actor::

    CRITICAL:pykka:Current state of DeadlockActorB-2 (ident: 140151493752576):
    File "/usr/lib/python3.6/threading.py", line 884, in _bootstrap
        self._bootstrap_inner()
    File "/usr/lib/python3.6/threading.py", line 916, in _bootstrap_inner
        self.run()
    File "/usr/lib/python3.6/threading.py", line 864, in run
        self._target(*self._args, **self._kwargs)
    File ".../pykka/actor.py", line 195, in _actor_loop
        response = self._handle_receive(message)
    File ".../pykka/actor.py", line 297, in _handle_receive
        return callee(*message['args'], **message['kwargs'])
    File "examples/deadlock_debugging.py", line 25, in bar
        return self.a.foo().get()
    File ".../pykka/threading.py", line 47, in get
        self._data = self._queue.get(True, timeout)
    File "/usr/lib/python3.6/queue.py", line 164, in get
        self.not_empty.wait()
    File "/usr/lib/python3.6/threading.py", line 295, in wait
        waiter.acquire()

    CRITICAL:pykka:Current state of DeadlockActorA-1 (ident: 140151572883200):
    File "/usr/lib/python3.6/threading.py", line 884, in _bootstrap
        self._bootstrap_inner()
    File "/usr/lib/python3.6/threading.py", line 916, in _bootstrap_inner
        self.run()
    File "/usr/lib/python3.6/threading.py", line 864, in run
        self._target(*self._args, **self._kwargs)
    File ".../pykka/actor.py", line 195, in _actor_loop
        response = self._handle_receive(message)
    File ".../pykka/actor.py", line 297, in _handle_receive
        return callee(*message['args'], **message['kwargs'])
    File "examples/deadlock_debugging.py", line 15, in foo
        return b.bar().get()
    File ".../pykka/threading.py", line 47, in get
        self._data = self._queue.get(True, timeout)
    File "/usr/lib/python3.6/queue.py", line 164, in get
        self.not_empty.wait()
    File "/usr/lib/python3.6/threading.py", line 295, in wait
        waiter.acquire()

    CRITICAL:pykka:Current state of MainThread (ident: 140151593330496):
    File ".../examples/deadlock_debugging.py", line 49, in <module>
        time.sleep(1)
    File ".../pykka/debug.py", line 63, in log_thread_tracebacks
        stack = ''.join(traceback.format_stack(frame))
