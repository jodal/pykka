import pytest


@pytest.fixture(scope='module')
def actor_class(runtime):
    class ActorA(runtime.actor_class):
        cat = 'dog'

        def functional_hello(self, s):
            return 'Hello, {}!'.format(s)

        def set_cat(self, s):
            self.cat = s

        def raise_keyboard_interrupt(self):
            raise KeyboardInterrupt

        def talk_with_self(self):
            return self.actor_ref.proxy().functional_hello('from the future')

    return ActorA


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_functional_method_call_returns_correct_value(proxy):
    assert proxy.functional_hello('world').get() == 'Hello, world!'
    assert proxy.functional_hello('moon').get() == 'Hello, moon!'


def test_side_effect_of_method_is_observable(proxy):
    assert proxy.cat.get() == 'dog'

    proxy.set_cat('eagle')

    assert proxy.cat.get() == 'eagle'


def test_calling_unknown_method_raises_attribute_error(proxy):
    with pytest.raises(AttributeError) as exc_info:
        proxy.unknown_method()

    result = str(exc_info.value)

    assert result.startswith('<ActorProxy for ActorA')
    assert result.endswith("has no attribute 'unknown_method'")


def test_can_proxy_itself_for_offloading_work_to_the_future(proxy):
    outer_future = proxy.talk_with_self()
    inner_future = outer_future.get(timeout=1)

    result = inner_future.get(timeout=1)

    assert result == 'Hello, from the future!'
