#!/usr/bin/env python3

import logging
import os
import signal
import time

import pykka
import pykka.debug


class DeadlockActorA(pykka.ThreadingActor):
    def foo(self, b):
        logging.debug("This is foo calling bar")
        return b.bar().get()


class DeadlockActorB(pykka.ThreadingActor):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def bar(self):
        logging.debug("This is bar calling foo; BOOM!")
        return self.a.foo().get()


if __name__ == "__main__":
    print("Setting up logging to get output from signal handler...")
    logging.basicConfig(level=logging.DEBUG)

    print("Registering signal handler...")
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    print("Starting actors...")
    a = DeadlockActorA.start().proxy()
    b = DeadlockActorB.start(a).proxy()

    print("Now doing something stupid that will deadlock the actors...")
    a.foo(b)

    time.sleep(0.01)  # Yield to actors, so we get output in a readable order

    pid = os.getpid()
    print("Making main thread relax; not block, not quit")
    print(f"1) Use `kill -SIGUSR1 {pid:d}` to log thread tracebacks")
    print(f"2) Then `kill {pid:d}` to terminate the process")
    while True:
        time.sleep(1)
