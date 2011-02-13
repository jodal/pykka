#! /usr/bin/env python

from pykka import Actor, ActorProxy

class Adder(Actor):
    def add_one(self, i):
        print '%s is increasing %d' % (self, i)
        return i + 1

class Bookkeeper(Actor):
    def __init__(self, adder):
        self.adder = adder

    def count_to(self, target):
        i = 0
        while i < target:
            i = self.adder.add_one(i).get()
            print '%s got %d back' % (self, i)

if __name__ == '__main__':
    adder = Adder.start_proxy()
    bookkeeper = Bookkeeper.start_proxy(adder)
    bookkeeper.count_to(10).wait()
