import time
import unittest

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
        self.assert_(result.startswith('<'))
        self.assert_(result.endswith('>'))

    def test_repr_reveals_that_this_is_a_ref(self):
        self.assert_('ActorRef' in repr(self.ref))

    def test_repr_contains_actor_class_name(self):
        self.assert_('AnActor' in repr(self.ref))

    def test_repr_contains_actor_urn(self):
        self.assert_(self.ref.actor_urn in repr(self.ref))

    def test_str_contains_actor_class_name(self):
        self.assert_('AnActor' in str(self.ref))

    def test_str_contains_actor_urn(self):
        self.assert_(self.ref.actor_urn in str(self.ref))

    def test_is_alive_returns_true_for_running_actor(self):
        self.assertTrue(self.ref.is_alive())

    def test_is_alive_returns_false_for_dead_actor(self):
        self.ref.stop()
        self.assertFalse(self.ref.is_alive())

    def test_stop_returns_true_if_actor_is_stopped(self):
        self.assertTrue(self.ref.stop())

    def test_stop_does_not_stop_already_dead_actor(self):
        self.ref.stop()
        try:
            self.assertFalse(self.ref.stop())
        except ActorDeadError:
            self.fail('Should never raise ActorDeadError')

    def test_tell_delivers_message_to_actors_custom_on_receive(self):
        self.ref.tell({'command': 'a custom message'})
        self.assertEqual(
            {'command': 'a custom message'}, self.received_message.get())

    def test_tell_fails_if_actor_is_stopped(self):
        self.ref.stop()
        try:
            self.ref.tell({'command': 'a custom message'})
            self.fail('Should raise ActorDeadError')
        except ActorDeadError as exception:
            self.assertEqual('%s not found' % self.ref, str(exception))

    def test_ask_blocks_until_response_arrives(self):
        result = self.ref.ask({'command': 'ping'})
        self.assertEqual('pong', result)

    def test_ask_can_timeout_if_blocked_too_long(self):
        try:
            self.ref.ask({'command': 'ping'}, timeout=0)
            self.fail('Should raise Timeout exception')
        except Timeout:
            pass

    def test_ask_can_return_future_instead_of_blocking(self):
        future = self.ref.ask({'command': 'ping'}, block=False)
        self.assertEqual('pong', future.get())

    def test_ask_fails_if_actor_is_stopped(self):
        self.ref.stop()
        try:
            self.ref.ask({'command': 'ping'})
            self.fail('Should raise ActorDeadError')
        except ActorDeadError as exception:
            self.assertEqual('%s not found' % self.ref, str(exception))

    def test_ask_nonblocking_fails_future_if_actor_is_stopped(self):
        self.ref.stop()
        future = self.ref.ask({'command': 'ping'}, block=False)
        try:
            future.get()
            self.fail('Should raise ActorDeadError')
        except ActorDeadError as exception:
            self.assertEqual('%s not found' % self.ref, str(exception))


def ConcreteRefTest(actor_class, future_class, sleep_function):
    class C(RefTest, unittest.TestCase):

        class AnActor(AnActor, actor_class):

            def sleep(self, seconds):
                sleep_function(seconds)

    C.__name__ = '%sRefTest' % (actor_class.__name__,)
    C.future_class = future_class
    return C

ThreadingActorRefTest = ConcreteRefTest(
    ThreadingActor, ThreadingFuture, time.sleep)

try:
    import gevent
    from pykka.gevent import GeventActor, GeventFuture

    GeventActorRefTest = ConcreteRefTest(
        GeventActor, GeventFuture, gevent.sleep)
except ImportError:
    pass

try:
    import eventlet
    from pykka.eventlet import EventletActor, EventletFuture

    EventletActorRefTest = ConcreteRefTest(
        EventletActor, EventletFuture, eventlet.sleep)
except ImportError:
    pass
