#!/usr/bin/env python3

import pykka


class Adder(pykka.ThreadingActor):
    def add_one(self, i):
        print(f"{self} is increasing {i}")
        return i + 1


class Bookkeeper(pykka.ThreadingActor):
    def __init__(self, adder):
        super().__init__()
        self.adder = adder

    def count_to(self, target):
        i = 0
        while i < target:
            i = self.adder.add_one(i).get()
            print(f"{self} got {i} back")


if __name__ == "__main__":
    adder = Adder.start().proxy()
    bookkeeper = Bookkeeper.start(adder).proxy()
    bookkeeper.count_to(10).get()
    pykka.ActorRegistry.stop_all()
