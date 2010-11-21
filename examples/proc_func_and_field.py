#! /usr/bin/env python

import time

from pykka import Actor

class Ponger(Actor):
    name = 'Ponger'
    field = 'this is the value of Ponger.field'

    def proc(self):
        print '%s: this was printed by Ponger.do()' % self.name

    def func(self):
        time.sleep(0.5) # Block a bit to make it realistic
        return 'this was returned by Ponger.get()'

class Pinger(Actor):
    name = 'Pinger'

    def run(self):
        for i in range(5):
            # Method with side effect
            print '%s: calling Ponger.proc() ...' % self.name
            self.ponger.proc()

            # Method with return value
            print '%s: calling Ponger.func() ...' % self.name
            result = self.ponger.func() # Does not block, returns a future
            print '%s: printing result ... (blocking)' % self.name
            print '%s: %s' % (self.name, result.get()) # Blocks until ready

            # Field reading
            print '%s: reading Ponger.field ...' % self.name
            result = self.ponger.field # Does not block, returns a future
            print '%s: printing result ... (blocking)' % self.name
            print '%s: %s' % (self.name, result.get()) # Blocks until ready

            # Field writing
            print '%s: writing Ponger.field ...' % self.name
            self.ponger.field = 'new value' # Does not block
            result = self.ponger.field # Does not block, returns a future
            print '%s: printing new field value ... (blocking)' % self.name
            print '%s: %s' % (self.name, result.get()) # Blocks until ready
        self.ponger.stop()

if __name__ == '__main__':
    ponger = Ponger().start()
    pinger = Pinger(ponger=ponger).start()
