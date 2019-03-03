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
            if isinstance(message, dict) and message.get('command') == 'ping':
                runtime.sleep_func(0.01)
                return 'pong'
            else:
                self.received_message.set(message)

    return ActorA


@pytest.fixture
def received_messages(runtime):
    return runtime.future_class()


@pytest.fixture
def actor_ref(actor_class, received_messages):
    ref = actor_class.start(received_messages)
    yield ref
    ref.stop()


def test_repr_is_wrapped_in_lt_and_gt(actor_ref):
    result = repr(actor_ref)

    assert result.startswith('<')
    assert result.endswith('>')


def test_repr_reveals_that_this_is_a_ref(actor_ref):
    assert 'ActorRef' in repr(actor_ref)


def test_repr_contains_actor_class_name(actor_ref):
    assert 'ActorA' in repr(actor_ref)


def test_repr_contains_actor_urn(actor_ref):
    assert actor_ref.actor_urn in repr(actor_ref)


def test_str_contains_actor_class_name(actor_ref):
    assert 'ActorA' in str(actor_ref)


def test_str_contains_actor_urn(actor_ref):
    assert actor_ref.actor_urn in str(actor_ref)


def test_is_alive_returns_true_for_running_actor(actor_ref):
    assert actor_ref.is_alive()


def test_is_alive_returns_false_for_dead_actor(actor_ref):
    actor_ref.stop()

    assert not actor_ref.is_alive()


def test_stop_returns_true_if_actor_is_stopped(actor_ref):
    assert actor_ref.stop()


def test_stop_does_not_stop_already_dead_actor(actor_ref):
    assert actor_ref.stop()
    assert not actor_ref.stop()


def test_tell_delivers_message_to_actors_custom_on_receive(
    actor_ref, received_messages
):
    actor_ref.tell({'command': 'a custom message'})

    assert received_messages.get(timeout=1) == {'command': 'a custom message'}


@pytest.mark.parametrize(
    'message',
    [
        123,
        123.456,
        {'a': 'dict'},
        ('a', 'tuple'),
        ['a', 'list'],
        Exception('an exception'),
    ],
)
def test_tell_accepts_any_object_as_the_message(
    actor_ref, message, received_messages
):
    actor_ref.tell(message)

    assert received_messages.get(timeout=1) == message


def test_tell_fails_if_actor_is_stopped(actor_ref):
    actor_ref.stop()

    with pytest.raises(ActorDeadError) as exc_info:
        actor_ref.tell({'command': 'a custom message'})

    assert str(exc_info.value) == '{} not found'.format(actor_ref)


def test_ask_blocks_until_response_arrives(actor_ref):
    result = actor_ref.ask({'command': 'ping'})

    assert result == 'pong'


def test_ask_can_timeout_if_blocked_too_long(actor_ref):
    with pytest.raises(Timeout):
        actor_ref.ask({'command': 'ping'}, timeout=0)


def test_ask_can_return_future_instead_of_blocking(actor_ref):
    future = actor_ref.ask({'command': 'ping'}, block=False)

    assert future.get() == 'pong'


def test_ask_fails_if_actor_is_stopped(actor_ref):
    actor_ref.stop()

    with pytest.raises(ActorDeadError) as exc_info:
        actor_ref.ask({'command': 'ping'})

    assert str(exc_info.value) == '{} not found'.format(actor_ref)


def test_ask_nonblocking_fails_future_if_actor_is_stopped(actor_ref):
    actor_ref.stop()
    future = actor_ref.ask({'command': 'ping'}, block=False)

    with pytest.raises(ActorDeadError) as exc_info:
        future.get()

    assert str(exc_info.value) == '{} not found'.format(actor_ref)
