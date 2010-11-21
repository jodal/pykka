#! /usr/bin/env python

from pykka import Actor

class Adder(Actor):
    def add_one(self, i):
        print '%s: %d' % (self.name, i)
        return i + 1

class Counter(Actor):
    def count_to(self, target):
        i = 0
        while i < target:
            print '%s: %d' % (self.name, i)
            i = self.other.add_one(i + 1).get()

if __name__ == '__main__':
    adder = Adder().start()
    counter = Counter(other=adder).start()
    counter.count_to(10).get() # Block until finished
    counter.stop()
    adder.stop()
