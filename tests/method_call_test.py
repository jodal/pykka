import unittest

import pytest

from pykka import ThreadingActor


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
        assert self.proxy.functional_hello('world').get() == 'Hello, world!'
        assert self.proxy.functional_hello('moon').get() == 'Hello, moon!'

    def test_side_effect_of_method_is_observable(self):
        assert self.proxy.cat.get() == 'dog'

        self.proxy.set_cat('eagle')

        assert self.proxy.cat.get() == 'eagle'

    def test_calling_unknown_method_raises_attribute_error(self):
        with pytest.raises(AttributeError) as exc_info:
            self.proxy.unknown_method()

        result = str(exc_info.value)

        assert result.startswith('<ActorProxy for ActorWithMethods')
        assert result.endswith('has no attribute "unknown_method"')

    def test_can_proxy_itself_for_offloading_work_to_the_future(self):
        outer_future = self.proxy.talk_with_self()
        inner_future = outer_future.get(timeout=1)

        result = inner_future.get(timeout=1)

        assert result == 'Hello, from the future!'


class DynamicMethodCallTest(object):
    def setUp(self):
        self.proxy = self.ActorExtendableAtRuntime.start().proxy()

    def tearDown(self):
        self.proxy.stop()

    def test_can_call_method_that_was_added_at_runtime(self):
        # We need to .get() after .add_method() to be sure that the method has
        # been added before we try to use it through the proxy.
        self.proxy.add_method('foo').get()

        assert self.proxy.foo().get() == 'returned by foo'

    def test_can_proxy_itself_and_use_attrs_added_at_runtime(self):
        # We don't need to .get() after .add_method() here, because the actor
        # will process the .add_method() call before processing the
        # .use_foo_through_self_proxy() call, which again will use the new
        # method, .foo().
        self.proxy.add_method('foo')
        outer_future = self.proxy.use_foo_through_self_proxy()
        inner_future = outer_future.get(timeout=1)
        result = inner_future.get(timeout=1)

        assert result == 'returned by foo'


class ThreadingStaticMethodCallTest(StaticMethodCallTest, unittest.TestCase):
    class ActorWithMethods(ActorWithMethods, ThreadingActor):
        pass


class ThreadingDynamicMethodCallTest(DynamicMethodCallTest, unittest.TestCase):
    class ActorExtendableAtRuntime(ActorExtendableAtRuntime, ThreadingActor):
        pass


try:
    from pykka.gevent import GeventActor

    class GeventStaticMethodCallTest(StaticMethodCallTest, unittest.TestCase):
        class ActorWithMethods(ActorWithMethods, GeventActor):
            pass

    class GeventDynamicMethodCallTest(DynamicMethodCallTest, unittest.TestCase):
        class ActorExtendableAtRuntime(ActorExtendableAtRuntime, GeventActor):
            pass


except ImportError:
    pass


try:
    from pykka.eventlet import EventletActor

    class EventletStaticMethodCallTest(StaticMethodCallTest, unittest.TestCase):
        class ActorWithMethods(ActorWithMethods, EventletActor):
            pass

    class EventletDynamicMethodCallTest(
        DynamicMethodCallTest, unittest.TestCase
    ):
        class ActorExtendableAtRuntime(ActorExtendableAtRuntime, EventletActor):
            pass


except ImportError:
    pass
