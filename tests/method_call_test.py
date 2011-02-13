import unittest

from pykka import Actor, ActorProxy

class ActorWithMethods(Actor):
    foo = 'bar'
    def functional_hello(self, s):
        return 'Hello, %s!' % s
    def set_foo(self, s):
        self.foo = s

class ActorExtendableAtRuntime(Actor):
    def add_method(self, name):
        setattr(self, name, lambda: 'returned by ' + name)


class MethodCallTest(unittest.TestCase):
    def setUp(self):
        self.proxy = ActorProxy(ActorWithMethods.start())

    def tearDown(self):
        self.proxy.stop()

    def test_functional_method_call_returns_correct_value(self):
        self.assertEqual('Hello, world!',
            self.proxy.functional_hello('world').get())
        self.assertEqual('Hello, moon!',
            self.proxy.functional_hello('moon').get())

    def test_side_effect_of_method_is_observable(self):
        self.assertEqual('bar', self.proxy.foo.get())
        self.proxy.set_foo('baz')
        self.assertEqual('baz', self.proxy.foo.get())

    def test_calling_unknown_method_raises_attribute_error(self):
        try:
            self.proxy.unknown_method()
            self.fail('Should raise AttributeError')
        except AttributeError as e:
            result = str(e)
            self.assert_(result.startswith('<ActorProxy for ActorWithMethods'))
            self.assert_(result.endswith('has no attribute "unknown_method"'))


class MethodAddedAtRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.proxy = ActorProxy(ActorExtendableAtRuntime().start())

    def tearDown(self):
        self.proxy.stop()

    def test_can_call_method_that_was_added_at_runtime(self):
        self.proxy.add_method('foo')
        self.assertEqual('returned by foo', self.proxy.foo().get())
