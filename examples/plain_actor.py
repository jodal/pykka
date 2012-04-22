#! /usr/bin/env python

from pykka.actor import ThreadingActor

class PlainActor(ThreadingActor):
    def __init__(self):
        self.stored_messages = []

    def on_receive(self, message):
        if message.get('command') == 'get_messages':
            return self.stored_messages
        else:
            self.stored_messages.append(message)

if __name__ == '__main__':
    actor = PlainActor.start()
    actor.tell({'no': 'Norway', 'se': 'Sweden'})
    actor.tell({'a': 3, 'b': 4, 'c': 5})
    print actor.ask({'command': 'get_messages'})
    actor.stop()
