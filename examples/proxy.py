#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pykka",
# ]
# ///

import threading
import time

import pykka


def log(msg: str) -> None:
    thread_name = threading.current_thread().name
    print(f"{thread_name}: {msg}")


class AnActor(pykka.ThreadingActor):
    field = "this is the value of AnActor.field"

    def foo(self) -> None:
        log("this was printed by AnActor.foo()")

    def bar(self) -> str:
        time.sleep(0.5)  # Block a bit to make it realistic
        return "this was returned by AnActor.bar() after a delay"


if __name__ == "__main__":
    # Start the actor and get a proxy to it
    proxy = AnActor.start().proxy()

    # Method with side effect
    log("calling AnActor.foo() ...")
    proxy.foo()

    # Method with return value
    log("calling AnActor.bar() ...")
    result = proxy.bar()  # Does not block, returns a future
    log("printing result ... (blocking)")
    log(result.get())  # Blocks until ready

    # Field reading
    log("reading AnActor.field ...")
    result = proxy.field  # Does not block, returns a future
    log("printing result ... (blocking)")
    log(result.get())  # Blocks until ready

    # Field writing
    log("writing AnActor.field ...")
    proxy.field = "new value"  # Assignment does not block
    result = proxy.field  # Does not block, returns a future
    log("printing new field value ... (blocking)")
    log(result.get())  # Blocks until ready

    # Stop the actor
    proxy.stop()
