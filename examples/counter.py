#! /usr/bin/env python

from pykka import Actor

class Adder(Actor):
    def add_one(self, i):
        print '%s: %d' % (self.name, i)
        return i + 1

class Counter(Actor):
    def __init__(self, adder):
        self.adder = adder

    def count_to(self, target):
        i = 0
        while i < target:
            print '%s: %d' % (self.name, i)
            i = self.adder.add_one(i + 1).get()

if __name__ == '__main__':
    adder = Adder.start()
    counter = Counter.start(adder)
    counter.count_to(10).wait()
    counter.stop()
    adder.stop()
