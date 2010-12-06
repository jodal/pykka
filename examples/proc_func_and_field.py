#! /usr/bin/env python

import threading
import time

from pykka import Actor

class AnActor(Actor):
    name = 'AnActorThread'
    field = 'this is the value of AnActor.field'

    def proc(self):
        log('this was printed by AnActor.proc()')

    def func(self):
        time.sleep(0.5) # Block a bit to make it realistic
        return 'this was returned by AnActor.func()'

def run(actor):
    for i in range(5):
        # Method with side effect
        log('calling Ponger.proc() ...')
        actor.proc()

        # Method with return value
        log('calling Ponger.func() ...')
        result = actor.func() # Does not block, returns a future
        log('printing result ... (blocking)')
        log(result.get()) # Blocks until ready

        # Field reading
        log('reading Ponger.field ...')
        result = actor.field # Does not block, returns a future
        log('printing result ... (blocking)')
        log(result.get()) # Blocks until ready

        # Field writing
        log('writing Ponger.field ...')
        actor.field = 'new value' # Assignment does not block
        result = actor.field # Does not block, returns a future
        log('printing new field value ... (blocking)')
        log(result.get()) # Blocks until ready
    actor.stop()

def log(s):
    print "%s: %s" % (threading.current_thread().name, s)

if __name__ == '__main__':
    actor = AnActor().start()
    run(actor)
