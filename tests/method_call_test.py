import os
import sys
import unittest

from pykka.actor import ThreadingActor


class ActorWithMethods(object):
    foo = 'bar'

    def functional_hello(self, s):
        return 'Hello, %s!' % s

    def set_foo(self, s):
        self.foo = s

    def raise_keyboard_interrupt(self):
        raise KeyboardInterrupt


class ActorExtendableAtRuntime(object):
    def add_method(self, name):
        setattr(self, name, lambda: 'returned by ' + name)


class MethodCallTest(object):
    def setUp(self):
        self.proxy = self.ActorWithMethods.start().proxy()
        self.proxy_extendable = self.ActorExtendableAtRuntime().start().proxy()

    def tearDown(self):
        self.proxy.stop()
        self.proxy_extendable.stop()

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

    def test_can_call_method_that_was_added_at_runtime(self):
        self.proxy_extendable.add_method('foo')
        self.assertEqual('returned by foo', self.proxy_extendable.foo().get())


class ThreadingMethodCallTest(MethodCallTest, unittest.TestCase):
    class ActorWithMethods(ActorWithMethods, ThreadingActor):
        pass

    class ActorExtendableAtRuntime(ActorExtendableAtRuntime, ThreadingActor):
        pass


if sys.version_info < (3,) and 'TRAVIS' not in os.environ:
    from pykka.gevent import GeventActor

    class GeventMethodCallTest(MethodCallTest, unittest.TestCase):
        class ActorWithMethods(ActorWithMethods, GeventActor):
            pass

        class ActorExtendableAtRuntime(ActorExtendableAtRuntime, GeventActor):
            pass
