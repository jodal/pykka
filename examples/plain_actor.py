#! /usr/bin/env python

from pykka.actor import Actor

class PlainActor(Actor):
    def __init__(self):
        self.stored_messages = []

    def react(self, message):
        if message.get('command') == 'get_messages':
            return self.stored_messages
        else:
            self.stored_messages.append(message)

if __name__ == '__main__':
    actor = PlainActor.start()
    actor.send_one_way({'no': 'Norway', 'se': 'Sweden'})
    actor.send_one_way({'a': 3, 'b': 4, 'c': 5})
    print actor.send_request_reply({'command': 'get_messages'})
