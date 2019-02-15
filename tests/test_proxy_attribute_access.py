import pytest

from pykka import compat


class NestedObject(object):
    pykka_traversable = True
    inner = 'nested.inner'


@pytest.fixture
def actor_class(runtime):
    class ActorA(runtime.actor_class):
        an_attr = 'an_attr'
        _private_attr = 'secret'
        nested = NestedObject()

        @property
        def a_ro_property(self):
            return 'a_ro_property'

        _a_rw_property = 'a_rw_property'

        @property
        def a_rw_property(self):
            return self._a_rw_property

        @a_rw_property.setter
        def a_rw_property(self, value):
            self._a_rw_property = value

        def a_method(self):
            raise Exception('This method should be mocked')

    return ActorA


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_actor_attr_can_be_read_using_get_postfix(proxy):
    assert proxy.an_attr.get() == 'an_attr'


def test_actor_attr_can_be_set_using_assignment(proxy):
    assert proxy.an_attr.get() == 'an_attr'

    proxy.an_attr = 'an_attr_2'

    assert proxy.an_attr.get() == 'an_attr_2'


def test_private_attr_access_raises_exception(proxy):
    with pytest.raises(AttributeError) as exc_info:
        proxy._private_attr.get()

    assert "has no attribute '_private_attr'" in str(exc_info.value)


def test_missing_attr_access_raises_exception(proxy):
    with pytest.raises(AttributeError) as exc_info:
        proxy.missing_attr.get()

    assert "has no attribute 'missing_attr'" in str(exc_info.value)


def test_actor_property_can_be_read_using_get_postfix(proxy):
    assert proxy.a_ro_property.get() == 'a_ro_property'
    assert proxy.a_rw_property.get() == 'a_rw_property'


def test_actor_property_can_be_set_using_assignment(proxy):
    proxy.a_rw_property = 'a_rw_property_2'

    assert proxy.a_rw_property.get() == 'a_rw_property_2'


def test_actor_read_only_property_cannot_be_set(proxy):
    with pytest.raises(AttributeError):
        proxy.a_ro_property = 'a_ro_property_2'


def test_actor_with_noncallable_mock_property_works(
    actor_class, stop_all, mocker
):
    mock = mocker.NonCallableMock()
    mock.__get__ = mocker.Mock(return_value='mocked property value')
    assert not isinstance(mock, compat.Callable)

    actor_class.a_rw_property = mock
    proxy = actor_class.start().proxy()

    # When using NonCallableMock to fake the property, the value still behaves
    # as a property when access through the proxy.
    assert proxy.a_rw_property.get() == 'mocked property value'

    assert mock.__get__.call_count == 1


def test_actor_with_callable_mock_property_does_not_work(
    actor_class, stop_all, mocker
):
    mock = mocker.Mock()
    mock.__get__ = mocker.Mock(return_value='mocked property value')
    assert isinstance(mock, compat.Callable)

    actor_class.a_rw_property = mock
    proxy = actor_class.start().proxy()

    # XXX Because Mock and MagicMock are callable by default, they cause the
    # property to be wrapped in a `_CallableProxy`. Thus, the property no
    # longer behaves as a property when mocked and accessed through a proxy.
    with pytest.raises(AttributeError) as exc_info:
        assert proxy.a_rw_property.get()

    assert "'_CallableProxy' object has no attribute 'get'" in str(
        exc_info.value
    )


def test_actor_with_mocked_method_works(actor_class, stop_all, mocker):
    mock = mocker.MagicMock(return_value='mocked method return')
    with mocker.patch.object(actor_class, 'a_method', new=mock):
        proxy = actor_class.start().proxy()

        assert proxy.a_method().get() == 'mocked method return'

    assert mock.call_count == 1


def test_actor_with_mock_created_by_patch_does_not_work(
    actor_class, stop_all, mocker
):
    with mocker.patch.object(
        actor_class, 'a_method', return_value='foo'
    ) as mock:
        proxy = actor_class.start().proxy()

        # The method is properly mocked, as seen from the return value
        assert proxy.a_method().get() == 'foo'

    # XXX But, with a mock created by the `mock.patch.object()` context
    # manager, we cannot inspect the calls. Patches welcome!
    assert mock.call_count == 0


def test_actor_property_is_not_accessed_when_creating_proxy(runtime):
    class Actor(runtime.actor_class):
        @property
        def a_property(self):
            # Imagine code with side effects or heavy resource usage here
            raise Exception('Proxy creation accessed property')

    actor_ref = Actor.start()
    try:
        actor_ref.proxy()
    finally:
        actor_ref.stop()


def test_attr_of_traversable_attr_can_be_read(proxy):
    assert proxy.nested.inner.get() == 'nested.inner'


def test_traversable_object_returned_from_property_is_not_traversed(runtime):
    class Actor(runtime.actor_class):
        @property
        def a_property(self):
            return NestedObject()

    actor_ref = Actor.start()
    try:
        proxy = actor_ref.proxy()

        # In Pykka < 2, it worked like this:
        # assert proxy.a_property.inner.get() == 'nested.inner'

        # In Pykka >=2, the property getter always returns a future:
        assert proxy.a_property.get().inner == 'nested.inner'
    finally:
        actor_ref.stop()
