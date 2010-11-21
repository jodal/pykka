#! /usr/bin/env python

import time

from pykka import Actor

class Ponger(Actor):
    name = 'Ponger'
    field = 'this is the value of Ponger.field'

    def do(self):
        print '%s: this was printed by Ponger.do()' % self.name

    def get(self):
        time.sleep(0.2) # Block a bit to make it realistic
        return 'this was returned by Ponger.get()'

class Pinger(Actor):
    name = 'Pinger'

    def run(self):
        for i in range(5):
            # Method with side effect
            print '%s: calling Ponger.do() ...' % self.name
            self.ponger.do()

            # Method with return value
            print '%s: calling Ponger.get() ...' % self.name
            result = self.ponger.get() # Does not block, returns a future
            print '%s: printing result ... (blocking)' % self.name
            print '%s: %s' % (self.name, result.get()) # Blocks until ready

            # Field access
            print '%s: reading Ponger.field ...' % self.name
            result = self.ponger.field # Does not block, returns a future
            print '%s: printing result ... (blocking)' % self.name
            print '%s: %s' % (self.name, result.get()) # Blocks until ready
        self.ponger.stop()

if __name__ == '__main__':
    ponger = Ponger().start()
    pinger = Pinger(ponger=ponger).start()
