import unittest

from pykka import Actor

class MethodCallTest(unittest.TestCase):
    def setUp(self):
        class ActorWithMethods(Actor):
            foo = 'bar'
            def functional_hello(self, s):
                return 'Hello, %s!' % s
            def set_foo(self, s):
                self.foo = s
        self.actor = ActorWithMethods().start()

    def tearDown(self):
        self.actor.stop()

    def test_functional_method_call_returns_correct_value(self):
        self.assertEqual('Hello, world!',
            self.actor.functional_hello('world').get())
        self.assertEqual('Hello, moon!',
            self.actor.functional_hello('moon').get())

    def test_side_effect_of_method_is_observable(self):
        self.assertEqual('bar', self.actor.foo.get())
        self.actor.set_foo('baz')
        self.assertEqual('baz', self.actor.foo.get())
