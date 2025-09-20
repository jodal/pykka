#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pykka",
# ]
# ///

import threading
import time
from typing import cast

from pykka import ActorProxy, ThreadingActor
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method


def log(msg: str) -> None:
    thread_name = threading.current_thread().name
    print(f"{thread_name}: {msg}")


class FooActor(ThreadingActor):
    field = "this is the value of FooActor.field"

    def bar(self) -> None:
        log("this was printed by FooActor.bar()")

    def baz(self) -> str:
        time.sleep(0.5)  # Block a bit to make it realistic
        return "this was returned by FooActor.baz() after a delay"


class FooProxy(ActorMemberMixin, ActorProxy[FooActor]):
    field = proxy_field(FooActor.field)
    bar = proxy_method(FooActor.bar)
    baz = proxy_method(FooActor.baz)


if __name__ == "__main__":
    # Start the actor and get a proxy to it
    proxy = cast("FooProxy", FooActor.start().proxy())

    # Method with side effect
    log("calling FooActor.bar() ...")
    proxy.bar()

    # Method with return value
    log("calling FooActor.baz() ...")
    # Does not block, returns a future:
    result = proxy.baz()
    log("printing result ... (blocking)")
    # Blocks until ready:
    log(result.get())

    # Field reading
    log("reading FooActor.field ...")
    # Does not block, returns a future:
    result = proxy.field
    log("printing result ... (blocking)")
    # Blocks until ready:
    log(result.get())

    # Field writing
    log("writing FooActor.field ...")
    # Assignment does not block:
    proxy.field = "new value"  # type: ignore[assignment]
    # Does not block, returns a future:
    result = proxy.field
    log("printing new field value ... (blocking)")
    # Blocks until ready:
    log(result.get())

    # Stop the actor
    proxy.stop()
