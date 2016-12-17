import unittest

from pykka import ActorDeadError, ActorProxy, ThreadingActor


class SomeObject(object):
    cat = 'bar.cat'
    pykka_traversable = False


class AnActor(object):
    bar = SomeObject()
    bar.pykka_traversable = True

    foo = 'foo'

    def __init__(self):
        super(AnActor, self).__init__()
        self.cat = 'quox'

    def func(self):
        pass


class ProxyTest(object):

    def setUp(self):
        self.proxy = ActorProxy(self.AnActor.start())

    def tearDown(self):
        try:
            self.proxy.stop()
        except ActorDeadError:
            pass

    def test_repr_is_wrapped_in_lt_and_gt(self):
        result = repr(self.proxy)
        self.assertTrue(result.startswith('<'))
        self.assertTrue(result.endswith('>'))

    def test_repr_reveals_that_this_is_a_proxy(self):
        self.assertTrue('ActorProxy' in repr(self.proxy))

    def test_repr_contains_actor_class_name(self):
        self.assertTrue('AnActor' in repr(self.proxy))

    def test_repr_contains_actor_urn(self):
        self.assertTrue(self.proxy.actor_ref.actor_urn in repr(self.proxy))

    def test_repr_contains_attr_path(self):
        self.assertTrue('bar' in repr(self.proxy.bar))

    def test_str_contains_actor_class_name(self):
        self.assertTrue('AnActor' in str(self.proxy))

    def test_str_contains_actor_urn(self):
        self.assertTrue(self.proxy.actor_ref.actor_urn in str(self.proxy))

    def test_dir_on_proxy_lists_attributes_of_the_actor(self):
        result = dir(self.proxy)
        self.assertTrue('foo' in result)
        self.assertTrue('cat' in result)
        self.assertTrue('func' in result)

    def test_dir_on_proxy_lists_private_attributes_of_the_proxy(self):
        result = dir(self.proxy)
        self.assertTrue('__class__' in result)
        self.assertTrue('__dict__' in result)
        self.assertTrue('__getattr__' in result)
        self.assertTrue('__setattr__' in result)

    def test_refs_proxy_method_returns_a_proxy(self):
        proxy_from_ref_proxy = self.AnActor.start().proxy()
        self.assertTrue(isinstance(proxy_from_ref_proxy, ActorProxy))
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


def ConcreteProxyTest(actor_class):
    class C(ProxyTest, unittest.TestCase):

        class AnActor(AnActor, actor_class):
            pass
    C.__name__ = '%sProxyTest' % actor_class.__name__
    return C


ThreadingActorProxyTest = ConcreteProxyTest(ThreadingActor)


try:
    from pykka.gevent import GeventActor
    GeventActorProxyTest = ConcreteProxyTest(GeventActor)
except ImportError:
    pass


try:
    from pykka.eventlet import EventletActor
    EventletActorProxyTest = ConcreteProxyTest(EventletActor)
except ImportError:
    pass
