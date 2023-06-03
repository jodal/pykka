#!/usr/bin/env python3

import pykka

GetMessages = object()


class PlainActor(pykka.ThreadingActor):
    def __init__(self):
        super().__init__()
        self.stored_messages = []

    def on_receive(self, message):
        if message is GetMessages:
            return self.stored_messages
        self.stored_messages.append(message)
        return None


if __name__ == "__main__":
    actor = PlainActor.start()
    actor.tell({"no": "Norway", "se": "Sweden"})
    actor.tell({"a": 3, "b": 4, "c": 5})
    print(actor.ask(GetMessages))
    actor.stop()
