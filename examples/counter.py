#! /usr/bin/env python

import pykka


class Adder(pykka.ThreadingActor):
    def add_one(self, i):
        print '%s is increasing %d' % (self, i)
        return i + 1


class Bookkeeper(pykka.ThreadingActor):
    def __init__(self, adder):
        self.adder = adder

    def count_to(self, target):
        i = 0
        while i < target:
            i = self.adder.add_one(i).get()
            print '%s got %d back' % (self, i)


if __name__ == '__main__':
    adder = Adder.start().proxy()
    bookkeeper = Bookkeeper.start(adder).proxy()
    bookkeeper.count_to(10).get()
    pykka.ActorRegistry.stop_all()
