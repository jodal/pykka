import pytest


@pytest.fixture(scope="module")
def actor_class(runtime):
    class ActorA(runtime.actor_class):
        cat = "dog"

        def __init__(self, events):
            super().__init__()
            self.events = events

        def on_stop(self):
            self.events.on_stop_was_called.set()

        def on_failure(self, *args):
            self.events.on_failure_was_called.set()

        def functional_hello(self, s):
            return f"Hello, {s}!"

        def set_cat(self, s):
            self.cat = s

        def raise_exception(self):
            raise Exception("boom!")

        def talk_with_self(self):
            return self.actor_ref.proxy().functional_hello("from the future")

    return ActorA


@pytest.fixture
def proxy(actor_class, events):
    proxy = actor_class.start(events).proxy()
    yield proxy
    proxy.stop()


def test_functional_method_call_returns_correct_value(proxy):
    assert proxy.functional_hello("world").get() == "Hello, world!"
    assert proxy.functional_hello("moon").get() == "Hello, moon!"


def test_side_effect_of_method_call_is_observable(proxy):
    assert proxy.cat.get() == "dog"

    future = proxy.set_cat("eagle")

    assert future.get() is None
    assert proxy.cat.get() == "eagle"


def test_side_effect_of_deferred_method_call_is_observable(proxy):
    assert proxy.cat.get() == "dog"

    result = proxy.set_cat.defer("eagle")

    assert result is None
    assert proxy.cat.get() == "eagle"


def test_exception_in_method_reraised_by_future(proxy, events):
    assert not events.on_failure_was_called.is_set()

    future = proxy.raise_exception()
    with pytest.raises(Exception) as exc_info:
        future.get()

    assert str(exc_info.value) == "boom!"
    assert not events.on_failure_was_called.is_set()


def test_exception_in_deferred_method_call_triggers_on_failure(proxy, events):
    assert not events.on_failure_was_called.is_set()

    result = proxy.raise_exception.defer()

    assert result is None
    events.on_failure_was_called.wait(5)
    assert events.on_failure_was_called.is_set()
    assert not events.on_stop_was_called.is_set()


def test_call_to_unknown_method_raises_attribute_error(proxy):
    with pytest.raises(AttributeError) as exc_info:
        proxy.unknown_method()

    result = str(exc_info.value)

    assert result.startswith("<ActorProxy for ActorA")
    assert result.endswith("has no attribute 'unknown_method'")


def test_deferred_call_to_unknown_method_raises_attribute_error(proxy):
    with pytest.raises(AttributeError) as exc_info:
        proxy.unknown_method.defer()

    result = str(exc_info.value)

    assert result.startswith("<ActorProxy for ActorA")
    assert result.endswith("has no attribute 'unknown_method'")


def test_can_proxy_itself_for_offloading_work_to_the_future(proxy):
    outer_future = proxy.talk_with_self()
    inner_future = outer_future.get(timeout=1)

    result = inner_future.get(timeout=1)

    assert result == "Hello, from the future!"
