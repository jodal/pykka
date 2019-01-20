import pytest

from pykka import ActorDeadError, Timeout


@pytest.fixture(scope='module')
def actor_class(runtime):
    class ActorA(runtime.actor_class):
        received_messages = None

        def __init__(self, received_message):
            super(runtime.actor_class, self).__init__()
            self.received_message = received_message

        def on_receive(self, message):
            if message.get('command') == 'ping':
                runtime.sleep_func(0.01)
                return 'pong'
            else:
                self.received_message.set(message)

    return ActorA


@pytest.fixture
def received_messages(runtime):
    return runtime.future_class()


@pytest.fixture
def ref(actor_class, received_messages):
    ref = actor_class.start(received_messages)
    yield ref
    ref.stop()


def test_repr_is_wrapped_in_lt_and_gt(ref):
    result = repr(ref)
    assert result.startswith('<')
    assert result.endswith('>')


def test_repr_reveals_that_this_is_a_ref(ref):
    assert 'ActorRef' in repr(ref)


def test_repr_contains_actor_class_name(ref):
    assert 'ActorA' in repr(ref)


def test_repr_contains_actor_urn(ref):
    assert ref.actor_urn in repr(ref)


def test_str_contains_actor_class_name(ref):
    assert 'ActorA' in str(ref)


def test_str_contains_actor_urn(ref):
    assert ref.actor_urn in str(ref)


def test_is_alive_returns_true_for_running_actor(ref):
    assert ref.is_alive()


def test_is_alive_returns_false_for_dead_actor(ref):
    ref.stop()

    assert not ref.is_alive()


def test_stop_returns_true_if_actor_is_stopped(ref):
    assert ref.stop()


def test_stop_does_not_stop_already_dead_actor(ref):
    assert ref.stop()
    assert not ref.stop()


def test_tell_delivers_message_to_actors_custom_on_receive(
    ref, received_messages
):
    ref.tell({'command': 'a custom message'})

    assert received_messages.get() == {'command': 'a custom message'}


def test_tell_fails_if_actor_is_stopped(ref):
    ref.stop()

    with pytest.raises(ActorDeadError) as exc_info:
        ref.tell({'command': 'a custom message'})

    assert str(exc_info.value) == '%s not found' % ref


def test_ask_blocks_until_response_arrives(ref):
    result = ref.ask({'command': 'ping'})

    assert result == 'pong'


def test_ask_can_timeout_if_blocked_too_long(ref):
    with pytest.raises(Timeout):
        ref.ask({'command': 'ping'}, timeout=0)


def test_ask_can_return_future_instead_of_blocking(ref):
    future = ref.ask({'command': 'ping'}, block=False)

    assert future.get() == 'pong'


def test_ask_fails_if_actor_is_stopped(ref):
    ref.stop()

    with pytest.raises(ActorDeadError) as exc_info:
        ref.ask({'command': 'ping'})

    assert str(exc_info.value) == '%s not found' % ref


def test_ask_nonblocking_fails_future_if_actor_is_stopped(ref):
    ref.stop()
    future = ref.ask({'command': 'ping'}, block=False)

    with pytest.raises(ActorDeadError) as exc_info:
        future.get()

    assert str(exc_info.value) == '%s not found' % ref
