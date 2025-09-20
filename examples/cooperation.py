#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pykka",
# ]
# ///

import pykka


class Adder(pykka.ThreadingActor):
    def add_one(self, i: int) -> int:
        print(f"Adder is adding 1 to {i}")
        return i + 1


class Bookkeeper(pykka.ThreadingActor):
    def __init__(self, adder: pykka.ActorProxy[Adder]) -> None:
        super().__init__()
        self.adder = adder

    def count_to(self, target: int) -> None:
        i = 0
        while i < target:
            i = self.adder.add_one(i).get()
            print(f"Bookkeeper got {i} back")


if __name__ == "__main__":
    # Start the adder actor
    adder = Adder.start().proxy()

    # Start the bookkeeper actor, passing it the adder actor's proxy
    bookkeeper = Bookkeeper.start(adder).proxy()

    # Ask the bookkeeper to count to 5
    bookkeeper.count_to(5).get()

    # Stop all running actors using the ActorRegistry
    pykka.ActorRegistry.stop_all()
