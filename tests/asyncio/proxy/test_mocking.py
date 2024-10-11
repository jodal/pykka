from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, NoReturn

import pytest

from pykka.asyncio import Actor

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from pykka.asyncio import ActorProxy
    from tests.asyncio.types import Runtime

pytestmark = pytest.mark.usefixtures("_stop_all")


class ActorForMocking(Actor):
    _a_rw_property: str = "a_rw_property"

    @property
    def a_rw_property(self) -> str:
        return self._a_rw_property

    @a_rw_property.setter
    def a_rw_property(self, value: str) -> None:
        self._a_rw_property = value

    def a_method(self) -> NoReturn:
        raise Exception("This method should be mocked")


@pytest.fixture()
def actor_class(runtime: Runtime) -> type[ActorForMocking]:
    class ActorForMockingImpl(ActorForMocking, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return ActorForMockingImpl


@pytest.fixture()
async def proxy(
    actor_class: ActorForMocking,
) -> AsyncGenerator[ActorProxy[ActorForMocking]]:
    proxy = actor_class.start().proxy()
    yield proxy
    await proxy.stop()


async def test_actor_with_noncallable_mock_property_works(
    actor_class: type[ActorForMocking],
    mocker: MockerFixture,
) -> None:
    mock = mocker.NonCallableMock()
    mock.__get__ = mocker.Mock(return_value="mocked property value")
    assert not callable(mock)

    actor_class.a_rw_property = mock  # type: ignore[method-assign]
    proxy = actor_class.start().proxy()

    # When using NonCallableMock to fake the property, the value still behaves
    # as a property when access through the proxy.
    assert await proxy.a_rw_property.get() == "mocked property value"

    assert mock.__get__.call_count == 1


async def test_actor_with_callable_mock_property_does_not_work(
    actor_class: type[ActorForMocking],
    mocker: MockerFixture,
) -> None:
    mock = mocker.Mock()
    mock.__get__ = mocker.Mock(return_value="mocked property value")
    assert callable(mock)

    actor_class.a_rw_property = mock  # type: ignore[method-assign]
    proxy = actor_class.start().proxy()

    # Because Mock and MagicMock are callable by default, they cause the
    # property to be wrapped in a `CallableProxy`. Thus, the property no
    # longer behaves as a property when mocked and accessed through a proxy.
    with pytest.raises(AttributeError) as exc_info:
        assert await proxy.a_rw_property.get()

    assert "'CallableProxy' object has no attribute 'get'" in str(exc_info.value)


async def test_actor_with_mocked_method_works(
    actor_class: type[ActorForMocking],
    mocker: MockerFixture,
) -> None:
    mock = mocker.MagicMock(return_value="mocked method return")
    mocker.patch.object(actor_class, "a_method", new=mock)
    proxy = actor_class.start().proxy()

    assert await proxy.a_method().get() == "mocked method return"

    assert mock.call_count == 1
