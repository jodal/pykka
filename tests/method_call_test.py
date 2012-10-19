import unittest

from pykka.actor import ThreadingActor

try:
    from pykka.gevent import GeventActor
    HAS_GEVENT = True
except ImportError:
    HAS_GEVENT = False


class ActorWithMethods(object):
    cat = 'dog'

    def functional_hello(self, s):
        return 'Hello, %s!' % s

    def set_cat(self, s):
        self.cat = s

    def raise_keyboard_interrupt(self):
        raise KeyboardInterrupt

    def talk_with_self(self):
        return self.actor_ref.proxy().functional_hello('from the future')


class ActorExtendableAtRuntime(object):
    def add_method(self, name):
        setattr(self, name, lambda: 'returned by ' + name)

    def use_foo_through_self_proxy(self):
        return self.actor_ref.proxy().foo()


class StaticMethodCallTest(object):
    def setUp(self):
        self.proxy = self.ActorWithMethods.start().proxy()

    def tearDown(self):
        self.proxy.stop()

    def test_functional_method_call_returns_correct_value(self):
        self.assertEqual(
            'Hello, world!',
            self.proxy.functional_hello('world').get())
        self.assertEqual(
            'Hello, moon!',
            self.proxy.functional_hello('moon').get())

    def test_side_effect_of_method_is_observable(self):
        self.assertEqual('dog', self.proxy.cat.get())
        self.proxy.set_cat('eagle')
        self.assertEqual('eagle', self.proxy.cat.get())

    def test_calling_unknown_method_raises_attribute_error(self):
        try:
            self.proxy.unknown_method()
            self.fail('Should raise AttributeError')
        except AttributeError as e:
            result = str(e)
            self.assert_(result.startswith('<ActorProxy for ActorWithMethods'))
            self.assert_(result.endswith('has no attribute "unknown_method"'))

    def test_can_proxy_itself_for_offloading_work_to_the_future(self):
        outer_future = self.proxy.talk_with_self()
        inner_future = outer_future.get(timeout=1)
        result = inner_future.get(timeout=1)
        self.assertEqual('Hello, from the future!', result)


class DynamicMethodCallTest(object):
    def setUp(self):
        self.proxy = self.ActorExtendableAtRuntime.start().proxy()

    def tearDown(self):
        self.proxy.stop()

    def test_can_call_method_that_was_added_at_runtime(self):
        # We need to .get() after .add_method() to be sure that the method has
        # been added before we try to use it through the proxy.
        self.proxy.add_method('foo').get()
        self.assertEqual('returned by foo', self.proxy.foo().get())

    def test_can_proxy_itself_and_use_attrs_added_at_runtime(self):
        # We don't need to .get() after .add_method() here, because the actor
        # will process the .add_method() call before processing the
        # .use_foo_through_self_proxy() call, which again will use the new
        # method, .foo().
        self.proxy.add_method('foo')
        outer_future = self.proxy.use_foo_through_self_proxy()
        inner_future = outer_future.get(timeout=1)
        result = inner_future.get(timeout=1)
        self.assertEqual('returned by foo', result)


class ThreadingStaticMethodCallTest(StaticMethodCallTest, unittest.TestCase):
    class ActorWithMethods(ActorWithMethods, ThreadingActor):
        pass


class ThreadingDynamicMethodCallTest(DynamicMethodCallTest, unittest.TestCase):
    class ActorExtendableAtRuntime(ActorExtendableAtRuntime, ThreadingActor):
        pass


if HAS_GEVENT:
    class GeventStaticMethodCallTest(StaticMethodCallTest, unittest.TestCase):
        class ActorWithMethods(ActorWithMethods, GeventActor):
            pass

    class GeventDynamicMethodCallTest(
            DynamicMethodCallTest, unittest.TestCase):
        class ActorExtendableAtRuntime(ActorExtendableAtRuntime, GeventActor):
            pass
