import unittest

from pykka.actor import Actor

class FieldAccessTest(unittest.TestCase):
    def setUp(self):
        class ActorWithField(Actor):
            foo = 'bar'
        self.proxy = ActorWithField.start_proxy()

    def tearDown(self):
        self.proxy.stop()

    def test_actor_field_can_be_read_using_get_postfix(self):
        self.assertEqual('bar', self.proxy.foo.get())

    def test_actor_field_can_be_set_using_assignment(self):
        self.assertEqual('bar', self.proxy.foo.get())
        self.proxy.foo = 'baz'
        self.assertEqual('baz', self.proxy.foo.get())
