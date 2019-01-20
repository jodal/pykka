import unittest

import pytest

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

        assert result.startswith('<')
        assert result.endswith('>')

    def test_repr_reveals_that_this_is_a_proxy(self):
        assert 'ActorProxy' in repr(self.proxy)

    def test_repr_contains_actor_class_name(self):
        assert 'AnActor' in repr(self.proxy)

    def test_repr_contains_actor_urn(self):
        assert self.proxy.actor_ref.actor_urn in repr(self.proxy)

    def test_repr_contains_attr_path(self):
        assert 'bar' in repr(self.proxy.bar)

    def test_str_contains_actor_class_name(self):
        assert 'AnActor' in str(self.proxy)

    def test_str_contains_actor_urn(self):
        assert self.proxy.actor_ref.actor_urn in str(self.proxy)

    def test_dir_on_proxy_lists_attributes_of_the_actor(self):
        result = dir(self.proxy)

        assert 'foo' in result
        assert 'cat' in result
        assert 'func' in result

    def test_dir_on_proxy_lists_private_attributes_of_the_proxy(self):
        result = dir(self.proxy)

        assert '__class__' in result
        assert '__dict__' in result
        assert '__getattr__' in result
        assert '__setattr__' in result

    def test_refs_proxy_method_returns_a_proxy(self):
        proxy_from_ref_proxy = self.AnActor.start().proxy()

        assert isinstance(proxy_from_ref_proxy, ActorProxy)

        proxy_from_ref_proxy.stop().get()

    def test_proxy_constructor_raises_exception_if_actor_is_dead(self):
        actor_ref = self.AnActor.start()
        actor_ref.stop()

        with pytest.raises(ActorDeadError) as exc_info:
            ActorProxy(actor_ref)

        assert str(exc_info.value) == '%s not found' % actor_ref

    def test_actor_ref_may_be_retrieved_from_proxy_if_actor_is_dead(self):
        self.proxy.actor_ref.stop()

        assert not self.proxy.actor_ref.is_alive()


def ConcreteProxyTest(actor_class):
    class C(ProxyTest, unittest.TestCase):
        class AnActor(AnActor, actor_class):
            pass

    C.__name__ = '%sProxyTest' % actor_class.__name__
    return C


ThreadingActorProxyTest = ConcreteProxyTest(ThreadingActor)


try:
    from pykka.gevent import GeventActor
except ImportError:
    pass
else:
    GeventActorProxyTest = ConcreteProxyTest(GeventActor)


try:
    from pykka.eventlet import EventletActor
except ImportError:
    pass
else:
    EventletActorProxyTest = ConcreteProxyTest(EventletActor)
