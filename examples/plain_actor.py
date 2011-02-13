#! /usr/bin/env python

from pykka import Actor

class PlainActor(Actor):
    def __init__(self):
        self.stored_messages = []

    def react(self, message):
        if message.get('command') == 'print':
            print self.stored_messages
        else:
            self.stored_messages.append(message)

if __name__ == '__main__':
    actor = PlainActor().start()
    actor.send_one_way({'no': 'Norway', 'se': 'Sweden'})
    actor.send_one_way({'a': 3, 'b': 4, 'c': 5})
    actor.send_request_reply({'command': 'print'})
