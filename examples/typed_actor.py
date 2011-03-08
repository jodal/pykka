#! /usr/bin/env python

from pykka.actor import ThreadingActor

import threading
import time

class AnActor(ThreadingActor):
    field = 'this is the value of AnActor.field'

    def proc(self):
        log('this was printed by AnActor.proc()')

    def func(self):
        time.sleep(0.5) # Block a bit to make it realistic
        return 'this was returned by AnActor.func() after a delay'

def log(s):
    print "%s: %s" % (threading.current_thread().name, s)

if __name__ == '__main__':
    actor = AnActor.start().proxy()
    for i in range(3):
        # Method with side effect
        log('calling AnActor.proc() ...')
        actor.proc()

        # Method with return value
        log('calling AnActor.func() ...')
        result = actor.func() # Does not block, returns a future
        log('printing result ... (blocking)')
        log(result.get()) # Blocks until ready

        # Field reading
        log('reading AnActor.field ...')
        result = actor.field # Does not block, returns a future
        log('printing result ... (blocking)')
        log(result.get()) # Blocks until ready

        # Field writing
        log('writing AnActor.field ...')
        actor.field = 'new value' # Assignment does not block
        result = actor.field # Does not block, returns a future
        log('printing new field value ... (blocking)')
        log(result.get()) # Blocks until ready
    actor.stop()
