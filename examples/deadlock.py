#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pykka",
# ]
# ///

from __future__ import annotations

import logging
import os
import signal
import time
from typing import Any

import pykka
import pykka.debug

log = logging.getLogger(__name__)


class ActorA(pykka.ThreadingActor):
    def foo(self, b: pykka.ActorProxy[ActorB]) -> Any:
        log.debug("This is foo calling bar")
        return b.bar().get()


class ActorB(pykka.ThreadingActor):
    def __init__(self, a: pykka.ActorProxy[ActorA]) -> None:
        super().__init__()
        self.a = a

    def bar(self) -> Any:
        log.debug("This is bar calling foo; BOOM!")
        return self.a.foo().get()


if __name__ == "__main__":
    print("Setting up logging to get output from signal handler...")
    logging.basicConfig(level=logging.DEBUG)

    print("Registering signal handler...")
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    print("Starting actors...")
    a = ActorA.start().proxy()
    b = ActorB.start(a).proxy()

    print("Now doing something stupid that will deadlock the actors...")
    a.foo(b)

    # Yield to actors, so we get output in a readable order
    time.sleep(0.01)

    pid = os.getpid()
    print("Making main thread relax; not block, not quit")
    print(f"1) Use `kill -SIGUSR1 {pid:d}` to log thread tracebacks")
    print(f"2) Then `kill {pid:d}` to terminate the process")
    while True:
        time.sleep(1)
