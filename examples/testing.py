from typing import Any

import pykka


class ProducerActor(pykka.ThreadingActor):
    def __init__(self, consumer: pykka.ActorProxy[Any]) -> None:
        super().__init__()
        self.consumer = consumer

    def produce(self) -> None:
        new_item = {"item": 1, "new": True}
        self.consumer.consume(new_item)
