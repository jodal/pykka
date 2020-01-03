import pykka


class ProducerActor(pykka.ThreadingActor):
    def __init__(self, consumer):
        super().__init__()
        self.consumer = consumer

    def produce(self):
        new_item = {"item": 1, "new": True}
        self.consumer.consume(new_item)
