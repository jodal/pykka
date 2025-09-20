#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pykka",
# ]
# ///

from typing import Any

import pykka

# Define a unique message to request stored messages
GetMessages = object()


class BasicActor(pykka.ThreadingActor):
    def __init__(self) -> None:
        super().__init__()
        self._stored_messages: list[Any] = []

    def on_receive(self, message: Any) -> Any:
        if message is GetMessages:
            return self._stored_messages
        self._stored_messages.append(message)
        return None


if __name__ == "__main__":
    # Start the actor
    actor_ref = BasicActor.start()

    # Send some messages to the actor
    actor_ref.tell({"no": "Norway", "se": "Sweden"})
    actor_ref.tell({"a": 3, "b": 4, "c": 5})

    # Retrieve and print stored messages
    print(actor_ref.ask(GetMessages))

    # Stop the actor
    actor_ref.stop()
