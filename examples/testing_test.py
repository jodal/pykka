from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from testing import ProducerActor

if TYPE_CHECKING:
    from collections.abc import Generator
    from unittest.mock import Mock

    from pytest_mock import MockerFixture

    from pykka import ActorProxy


@pytest.fixture
def consumer_mock(mocker: MockerFixture) -> Any:
    return mocker.Mock()


@pytest.fixture
def producer(consumer_mock: Mock) -> Generator[ActorProxy[ProducerActor]]:
    # Step 1: The actor under test is wired up with
    # its dependencies and is started.
    proxy = ProducerActor.start(consumer_mock).proxy()

    yield proxy

    # Step 4: The actor is stopped to clean up before the next test.
    proxy.stop()


def test_producer_actor(
    consumer_mock: Mock,
    producer: ActorProxy[ProducerActor],
) -> None:
    # Step 2: Interact with the actor.
    # We call .get() on the last future returned by the actor to wait
    # for the actor to process all messages before asserting anything.
    producer.produce().get()

    # Step 3: Assert that the return values or actor state is as expected.
    consumer_mock.consume.assert_called_once_with({"item": 1, "new": True})
