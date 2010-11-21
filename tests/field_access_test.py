import unittest

from pykka import Actor

class FieldAccessTest(unittest.TestCase):
    def setUp(self):
        class ActorWithField(Actor):
            foo = 'bar'
        self.actor = ActorWithField().start()

    def tearDown(self):
        self.actor.stop()

    def test_actor_field_can_be_read_using_get_postfix(self):
        self.assertEqual('bar', self.actor.foo.get())
