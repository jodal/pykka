import unittest

from pykka.actor import Actor
from pykka.proxy import ActorProxy

class AnActor(Actor):
    pass


class ActorWithAttributesAndCallables(Actor):
    foo = 'bar'
    def __init__(self):
        self.baz = 'quox'
    def func(self):
        pass


class ProxyFromActorStartTest(unittest.TestCase):
    def setUp(self):
        self.proxy = AnActor.start_proxy()

    def tearDown(self):
        self.proxy.stop()

    def test_proxy_is_a_proxy(self):
        self.assert_(isinstance(self.proxy, ActorProxy))


class ProxyDirTest(unittest.TestCase):
    def setUp(self):
        self.proxy = ActorProxy(ActorWithAttributesAndCallables.start())

    def tearDown(self):
        self.proxy.stop()

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


class ProxyReprAndStrTest(unittest.TestCase):
    def setUp(self):
        self.proxy = ActorProxy(AnActor.start())

    def tearDown(self):
        self.proxy.stop()

    def test_repr_is_wrapped_in_lt_and_gt(self):
        result = repr(self.proxy)
        self.assert_(result.startswith('<'))
        self.assert_(result.endswith('>'))

    def test_repr_reveals_that_this_is_a_proxy(self):
        self.assert_('ActorProxy' in repr(self.proxy))

    def test_repr_contains_actor_class_name(self):
        self.assert_('AnActor' in repr(self.proxy))

    def test_repr_contains_actor_urn(self):
        self.assert_(self.proxy._actor_ref.actor_urn in repr(self.proxy))

    def test_str_contains_actor_class_name(self):
        self.assert_('AnActor' in str(self.proxy))

    def test_str_contains_actor_urn(self):
        self.assert_(self.proxy._actor_ref.actor_urn in str(self.proxy))
