import pytest
from producer import ProducerActor


@pytest.fixture()
def consumer_mock(mocker):
    return mocker.Mock()


@pytest.fixture()
def producer(consumer_mock):
    # Step 1: The actor under test is wired up with
    # its dependencies and is started.
    proxy = ProducerActor.start(consumer_mock).proxy()

    yield proxy

    # Step 4: The actor is stopped to clean up before the next test.
    proxy.stop()


def test_producer_actor(consumer_mock, producer):
    # Step 2: Interact with the actor.
    # We call .get() on the last future returned by the actor to wait
    # for the actor to process all messages before asserting anything.
    producer.produce().get()

    # Step 3: Assert that the return values or actor state is as expected.
    consumer_mock.consume.assert_called_once_with({"item": 1, "new": True})
