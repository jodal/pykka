import os
import sys
import unittest

from pykka import ActorDeadError
from pykka.actor import ThreadingActor
from pykka.proxy import ActorProxy
from pykka.registry import ActorRegistry


class SomeObject(object):
    baz = 'bar.baz'


class AnActor(object):
    bar = SomeObject()
    bar.pykka_traversable = True

    foo = 'foo'

    def __init__(self):
        self.baz = 'quox'

    def func(self):
        pass


class ProxyTest(object):
    def setUp(self):
        self.proxy = ActorProxy(self.AnActor.start())

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_repr_is_wrapped_in_lt_and_gt(self):
        result = repr(self.proxy)
        self.assert_(result.startswith('<'))
        self.assert_(result.endswith('>'))

    def test_repr_reveals_that_this_is_a_proxy(self):
        self.assert_('ActorProxy' in repr(self.proxy))

    def test_repr_contains_actor_class_name(self):
        self.assert_('AnActor' in repr(self.proxy))

    def test_repr_contains_actor_urn(self):
        self.assert_(self.proxy.actor_ref.actor_urn in repr(self.proxy))

    def test_repr_contains_attr_path(self):
        self.assert_('bar' in repr(self.proxy.bar))

    def test_str_contains_actor_class_name(self):
        self.assert_('AnActor' in str(self.proxy))

    def test_str_contains_actor_urn(self):
        self.assert_(self.proxy.actor_ref.actor_urn in str(self.proxy))

    def test_dir_on_proxy_lists_attributes_of_the_actor(self):
        result = dir(self.proxy)
        self.assert_('foo' in result)
        self.assert_('baz' in result)
        self.assert_('func' in result)

    def test_dir_on_proxy_lists_private_attributes_of_the_proxy(self):
        result = dir(self.proxy)
        self.assert_('__class__' in result)
        self.assert_('__dict__' in result)
        self.assert_('__getattr__' in result)
        self.assert_('__setattr__' in result)

    def test_refs_proxy_method_returns_a_proxy(self):
        proxy_from_ref_proxy = self.AnActor.start().proxy()
        self.assert_(isinstance(proxy_from_ref_proxy, ActorProxy))
        proxy_from_ref_proxy.stop().get()

    def test_proxy_constructor_raises_exception_if_actor_is_dead(self):
        actor_ref = self.AnActor.start()
        actor_ref.stop()
        try:
            ActorProxy(actor_ref)
            self.fail('Should raise ActorDeadError')
        except ActorDeadError as exception:
            self.assertEqual('%s not found' % actor_ref, str(exception))

    def test_actor_ref_may_be_retrieved_from_proxy_if_actor_is_dead(self):
        self.proxy.actor_ref.stop()
        self.assertFalse(self.proxy.actor_ref.is_alive())


class ThreadingProxyTest(ProxyTest, unittest.TestCase):
    class AnActor(AnActor, ThreadingActor):
        pass


if sys.version_info < (3,) and 'TRAVIS' not in os.environ:
    from pykka.gevent import GeventActor

    class GeventProxyTest(ProxyTest, unittest.TestCase):
        class AnActor(AnActor, GeventActor):
            pass
