import time
import unittest

import pytest

from pykka import ActorDeadError, ThreadingActor, ThreadingFuture, Timeout


class AnActor(object):
    def __init__(self, received_message):
        super(AnActor, self).__init__()
        self.received_message = received_message

    def on_receive(self, message):
        if message.get('command') == 'ping':
            self.sleep(0.01)
            return 'pong'
        else:
            self.received_message.set(message)


class RefTest(object):
    def setUp(self):
        self.received_message = self.future_class()
        self.ref = self.AnActor.start(self.received_message)

    def tearDown(self):
        self.ref.stop()

    def test_repr_is_wrapped_in_lt_and_gt(self):
        result = repr(self.ref)
        assert result.startswith('<')
        assert result.endswith('>')

    def test_repr_reveals_that_this_is_a_ref(self):
        assert 'ActorRef' in repr(self.ref)

    def test_repr_contains_actor_class_name(self):
        assert 'AnActor' in repr(self.ref)

    def test_repr_contains_actor_urn(self):
        assert self.ref.actor_urn in repr(self.ref)

    def test_str_contains_actor_class_name(self):
        assert 'AnActor' in str(self.ref)

    def test_str_contains_actor_urn(self):
        assert self.ref.actor_urn in str(self.ref)

    def test_is_alive_returns_true_for_running_actor(self):
        assert self.ref.is_alive()

    def test_is_alive_returns_false_for_dead_actor(self):
        self.ref.stop()

        assert not self.ref.is_alive()

    def test_stop_returns_true_if_actor_is_stopped(self):
        assert self.ref.stop()

    def test_stop_does_not_stop_already_dead_actor(self):
        assert self.ref.stop()
        assert not self.ref.stop()

    def test_tell_delivers_message_to_actors_custom_on_receive(self):
        self.ref.tell({'command': 'a custom message'})

        assert self.received_message.get() == {'command': 'a custom message'}

    def test_tell_fails_if_actor_is_stopped(self):
        self.ref.stop()

        with pytest.raises(ActorDeadError) as exc_info:
            self.ref.tell({'command': 'a custom message'})

        assert str(exc_info.value) == '%s not found' % self.ref

    def test_ask_blocks_until_response_arrives(self):
        result = self.ref.ask({'command': 'ping'})

        assert result == 'pong'

    def test_ask_can_timeout_if_blocked_too_long(self):
        with pytest.raises(Timeout):
            self.ref.ask({'command': 'ping'}, timeout=0)

    def test_ask_can_return_future_instead_of_blocking(self):
        future = self.ref.ask({'command': 'ping'}, block=False)

        assert future.get() == 'pong'

    def test_ask_fails_if_actor_is_stopped(self):
        self.ref.stop()

        with pytest.raises(ActorDeadError) as exc_info:
            self.ref.ask({'command': 'ping'})

        assert str(exc_info.value) == '%s not found' % self.ref

    def test_ask_nonblocking_fails_future_if_actor_is_stopped(self):
        self.ref.stop()
        future = self.ref.ask({'command': 'ping'}, block=False)

        with pytest.raises(ActorDeadError) as exc_info:
            future.get()

        assert str(exc_info.value) == '%s not found' % self.ref


def ConcreteRefTest(actor_class, future_class, sleep_function):
    class C(RefTest, unittest.TestCase):
        class AnActor(AnActor, actor_class):
            def sleep(self, seconds):
                sleep_function(seconds)

    C.__name__ = '%sRefTest' % (actor_class.__name__,)
    C.future_class = future_class
    return C


ThreadingActorRefTest = ConcreteRefTest(
    ThreadingActor, ThreadingFuture, time.sleep
)

try:
    import gevent
    from pykka.gevent import GeventActor, GeventFuture
except ImportError:
    pass
else:
    GeventActorRefTest = ConcreteRefTest(
        GeventActor, GeventFuture, gevent.sleep
    )

try:
    import eventlet
    from pykka.eventlet import EventletActor, EventletFuture
except ImportError:
    pass
else:
    EventletActorRefTest = ConcreteRefTest(
        EventletActor, EventletFuture, eventlet.sleep
    )
