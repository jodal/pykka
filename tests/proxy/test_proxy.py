import pytest

import pykka
from pykka import ActorDeadError, ActorProxy


class NestedObject(object):
    pass


@pytest.fixture(scope='module')
def actor_class(runtime):
    class ActorForProxying(runtime.actor_class):
        a_nested_object = pykka.traversable(NestedObject())
        a_class_attr = 'class_attr'

        def __init__(self):
            super(runtime.actor_class, self).__init__()
            self.an_instance_attr = 'an_instance_attr'

        def a_method(self):
            pass

    return ActorForProxying


@pytest.fixture
def proxy(actor_class):
    proxy = ActorProxy(actor_class.start())
    yield proxy
    proxy.stop()


def test_eq_to_self(proxy):
    assert proxy == proxy


def test_is_hashable(proxy):
    assert hash(proxy) == hash(proxy)


def test_eq_to_another_proxy_for_same_actor_and_attr_path(proxy):
    proxy2 = proxy.actor_ref.proxy()

    assert proxy == proxy2


def test_not_eq_to_proxy_with_different_attr_path(proxy):
    assert proxy != proxy.a_nested_object


def test_repr_is_wrapped_in_lt_and_gt(proxy):
    result = repr(proxy)

    assert result.startswith('<')
    assert result.endswith('>')


def test_repr_reveals_that_this_is_a_proxy(proxy):
    assert 'ActorProxy' in repr(proxy)


def test_repr_contains_actor_class_name(proxy):
    assert 'ActorForProxying' in repr(proxy)


def test_repr_contains_actor_urn(proxy):
    assert proxy.actor_ref.actor_urn in repr(proxy)


def test_repr_contains_attr_path(proxy):
    assert 'a_nested_object' in repr(proxy.a_nested_object)


def test_str_contains_actor_class_name(proxy):
    assert 'ActorForProxying' in str(proxy)


def test_str_contains_actor_urn(proxy):
    assert proxy.actor_ref.actor_urn in str(proxy)


def test_dir_on_proxy_lists_attributes_of_the_actor(proxy):
    result = dir(proxy)

    assert 'a_class_attr' in result
    assert 'an_instance_attr' in result
    assert 'a_method' in result


def test_dir_on_proxy_lists_private_attributes_of_the_proxy(proxy):
    result = dir(proxy)

    assert '__class__' in result
    assert '__dict__' in result
    assert '__getattr__' in result
    assert '__setattr__' in result


def test_refs_proxy_method_returns_a_proxy(actor_class):
    proxy_from_ref_proxy = actor_class.start().proxy()

    assert isinstance(proxy_from_ref_proxy, ActorProxy)

    proxy_from_ref_proxy.stop().get()


def test_proxy_constructor_raises_exception_if_actor_is_dead(actor_class):
    actor_ref = actor_class.start()
    actor_ref.stop()

    with pytest.raises(ActorDeadError) as exc_info:
        ActorProxy(actor_ref)

    assert str(exc_info.value) == '{} not found'.format(actor_ref)


def test_actor_ref_may_be_retrieved_from_proxy_if_actor_is_dead(proxy):
    proxy.actor_ref.stop()

    assert not proxy.actor_ref.is_alive()


def test_actor_proxy_does_not_expose_proxy_to_self(runtime, log_handler):
    class Actor(runtime.actor_class):
        def __init__(self):
            super(Actor, self).__init__()
            self.self_proxy = self.actor_ref.proxy()
            self.foo = 'bar'

    actor_ref = Actor.start()
    try:
        proxy = actor_ref.proxy()

        assert proxy.foo.get() == 'bar'
        with pytest.raises(
            AttributeError, match="has no attribute 'self_proxy'"
        ):
            proxy.self_proxy.foo.get()
    finally:
        actor_ref.stop()

    log_handler.wait_for_message('warning')
    with log_handler.lock:
        assert len(log_handler.messages['warning']) == 2
        log_record = log_handler.messages['warning'][0]

    assert (
        "attribute 'self_proxy' is a proxy to itself. "
        "Consider making it private by renaming it to '_self_proxy'."
    ) in log_record.getMessage()
