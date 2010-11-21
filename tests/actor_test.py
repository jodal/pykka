import unittest

from pykka import Actor

class ActorInterruptTest(unittest.TestCase):
    def setUp(self):
        class ActorWithInterrupt(Actor):
            def _event_loop(self):
                raise KeyboardInterrupt
        self.actor = ActorWithInterrupt()

    def test_issuing_keyboard_interrupt_stops_process(self):
        try:
            self.actor.run()
            self.fail('Should throw SystemExit exception')
        except SystemExit:
            pass
