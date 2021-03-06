from collections.abc import Callable

import pytest


@pytest.fixture
def actor_class(runtime):
    class ActorForMocking(runtime.actor_class):
        _a_rw_property = "a_rw_property"

        @property
        def a_rw_property(self):
            return self._a_rw_property

        @a_rw_property.setter
        def a_rw_property(self, value):
            self._a_rw_property = value

        def a_method(self):
            raise Exception("This method should be mocked")

    return ActorForMocking


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_actor_with_noncallable_mock_property_works(actor_class, stop_all, mocker):
    mock = mocker.NonCallableMock()
    mock.__get__ = mocker.Mock(return_value="mocked property value")
    assert not isinstance(mock, Callable)

    actor_class.a_rw_property = mock
    proxy = actor_class.start().proxy()

    # When using NonCallableMock to fake the property, the value still behaves
    # as a property when access through the proxy.
    assert proxy.a_rw_property.get() == "mocked property value"

    assert mock.__get__.call_count == 1


def test_actor_with_callable_mock_property_does_not_work(actor_class, stop_all, mocker):
    mock = mocker.Mock()
    mock.__get__ = mocker.Mock(return_value="mocked property value")
    assert isinstance(mock, Callable)

    actor_class.a_rw_property = mock
    proxy = actor_class.start().proxy()

    # XXX Because Mock and MagicMock are callable by default, they cause the
    # property to be wrapped in a `CallableProxy`. Thus, the property no
    # longer behaves as a property when mocked and accessed through a proxy.
    with pytest.raises(AttributeError) as exc_info:
        assert proxy.a_rw_property.get()

    assert "'CallableProxy' object has no attribute 'get'" in str(exc_info.value)


def test_actor_with_mocked_method_works(actor_class, stop_all, mocker):
    mock = mocker.MagicMock(return_value="mocked method return")
    mocker.patch.object(actor_class, "a_method", new=mock)
    proxy = actor_class.start().proxy()

    assert proxy.a_method().get() == "mocked method return"

    assert mock.call_count == 1
