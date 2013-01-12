import threading
import unittest
import uuid
import time

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

try:
    import gevent.event
    from pykka.gevent import GeventActor
    HAS_GEVENT = True
except ImportError:
    HAS_GEVENT = False


class AnActor(object):
    def __init__(self, **events):
        super(AnActor, self).__init__()
        self.on_start_was_called = events['on_start_was_called']
        self.on_stop_was_called = events['on_stop_was_called']
        self.on_failure_was_called = events['on_failure_was_called']
        self.actor_was_registered_before_on_start_was_called = events[
            'actor_was_registered_before_on_start_was_called']
        self.greetings_was_received = events['greetings_was_received']

    def on_start(self):
        self.on_start_was_called.set()
        if ActorRegistry.get_by_urn(self.actor_urn) is not None:
            self.actor_was_registered_before_on_start_was_called.set()

    def on_stop(self):
        self.on_stop_was_called.set()

    def on_failure(self, *args):
        self.on_failure_was_called.set()

    def on_receive(self, message):
        if message.get('command') == 'raise exception':
            raise Exception('foo')
        elif message.get('command') == 'raise base exception':
            raise BaseException()
        elif message.get('command') == 'stop twice':
            self.stop()
            self.stop()
        elif message.get('command') == 'message self then stop':
            self.actor_ref.tell({'command': 'greetings'})
            self.stop()
        elif message.get('command') == 'greetings':
            self.greetings_was_received.set()
        else:
            super(AnActor, self).on_receive(message)


class EarlyStoppingActor(object):
    def __init__(self, on_stop_was_called):
        super(EarlyStoppingActor, self).__init__()
        self.on_stop_was_called = on_stop_was_called

    def on_start(self):
        self.stop()

    def on_stop(self):
        self.on_stop_was_called.set()


class EarlyFailingActor(object):
    def __init__(self, on_start_was_called):
        super(EarlyFailingActor, self).__init__()
        self.on_start_was_called = on_start_was_called

    def on_start(self):
        try:
            raise RuntimeError('on_start failure')
        finally:
            self.on_start_was_called.set()


class LateFailingActor(object):
    def __init__(self, on_stop_was_called):
        super(LateFailingActor, self).__init__()
        self.on_stop_was_called = on_stop_was_called

    def on_start(self):
        self.stop()

    def on_stop(self):
        try:
            raise RuntimeError('on_stop failure')
        finally:
            self.on_stop_was_called.set()


class FailingOnFailureActor(object):
    def __init__(self, on_failure_was_called):
        super(FailingOnFailureActor, self).__init__()
        self.on_failure_was_called = on_failure_was_called

    def on_receive(self, message):
        if message.get('command') == 'raise exception':
            raise Exception('on_receive failure')
        else:
            super(FailingOnFailureActor, self).on_receive(message)

    def on_failure(self, *args):
        try:
            raise RuntimeError('on_failure failure')
        finally:
            self.on_failure_was_called.set()


class ActorTest(object):
    def setUp(self):
        self.on_start_was_called = self.event_class()
        self.on_stop_was_called = self.event_class()
        self.on_failure_was_called = self.event_class()
        self.actor_was_registered_before_on_start_was_called = (
            self.event_class())
        self.greetings_was_received = self.event_class()

        self.actor_ref = self.AnActor.start(
            on_start_was_called=self.on_start_was_called,
            on_stop_was_called=self.on_stop_was_called,
            on_failure_was_called=self.on_failure_was_called,
            actor_was_registered_before_on_start_was_called=(
                self.actor_was_registered_before_on_start_was_called),
            greetings_was_received=self.greetings_was_received)
        self.actor_proxy = self.actor_ref.proxy()

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_actor_has_an_uuid4_based_urn(self):
        self.assertEqual(4, uuid.UUID(self.actor_ref.actor_urn).version)

    def test_actor_has_unique_uuid(self):
        event = self.event_class()
        actors = [
            self.AnActor.start(
                on_start_was_called=event,
                on_stop_was_called=event,
                on_failure_was_called=event,
                actor_was_registered_before_on_start_was_called=event,
                greetings_was_received=event)
            for _ in range(3)]

        self.assertNotEqual(actors[0].actor_urn, actors[1].actor_urn)
        self.assertNotEqual(actors[1].actor_urn, actors[2].actor_urn)
        self.assertNotEqual(actors[2].actor_urn, actors[0].actor_urn)

    def test_str_on_raw_actor_contains_actor_class_name(self):
        event = self.event_class()
        unstarted_actor = self.AnActor(
            on_start_was_called=event,
            on_stop_was_called=event,
            on_failure_was_called=event,
            actor_was_registered_before_on_start_was_called=event,
            greetings_was_received=event)
        self.assert_('AnActor' in str(unstarted_actor))

    def test_str_on_raw_actor_contains_actor_urn(self):
        event = self.event_class()
        unstarted_actor = self.AnActor(
            on_start_was_called=event,
            on_stop_was_called=event,
            on_failure_was_called=event,
            actor_was_registered_before_on_start_was_called=event,
            greetings_was_received=event)
        self.assert_(unstarted_actor.actor_urn in str(unstarted_actor))

    def test_init_can_be_called_with_arbitrary_arguments(self):
        self.SuperInitActor(1, 2, 3, foo='bar')

    def test_on_start_is_called_before_first_message_is_processed(self):
        self.on_start_was_called.wait(5)
        self.assertTrue(self.on_start_was_called.is_set())

    def test_on_start_is_called_after_the_actor_is_registered(self):
        # NOTE: If the actor is registered after the actor is started, this
        # test may still occasionally pass, as it is dependant on the exact
        # timing of events. When the actor is first registered and then
        # started, this test should always pass.
        self.on_start_was_called.wait(5)
        self.assertTrue(self.on_start_was_called.is_set())
        self.actor_was_registered_before_on_start_was_called.wait(0.1)
        self.assertTrue(
            self.actor_was_registered_before_on_start_was_called.is_set())

    def test_on_start_can_stop_actor_before_receive_loop_is_started(self):
        # NOTE: This test will pass even if the actor is allowed to start the
        # receive loop, but it will cause the test suite to hang, as the actor
        # thread is blocking on receiving messages to the actor inbox forever.
        # If one made this test specifically for ThreadingActor, one could add
        # an assertFalse(actor_thread.is_alive()), which would cause the test
        # to fail properly.
        stop_event = self.event_class()
        another_actor = self.EarlyStoppingActor.start(stop_event)
        stop_event.wait(5)
        self.assertTrue(stop_event.is_set())
        self.assertFalse(another_actor.is_alive())

    def test_on_start_failure_causes_actor_to_stop(self):
        # Actor should not be alive if on_start fails.
        start_event = self.event_class()
        actor = self.EarlyFailingActor.start(start_event)
        start_event.wait(5)
        time.sleep(0.01)
        self.assertFalse(actor.is_alive())

    def test_on_stop_is_called_when_actor_is_stopped(self):
        self.assertFalse(self.on_stop_was_called.is_set())
        self.actor_ref.stop()
        self.on_stop_was_called.wait(5)
        self.assertTrue(self.on_stop_was_called.is_set())

    def test_on_stop_failure_causes_actor_to_stop(self):
        stop_event = self.event_class()
        actor = self.LateFailingActor.start(stop_event)
        stop_event.wait(5)
        self.assertFalse(actor.is_alive())

    def test_on_failure_is_called_when_exception_cannot_be_returned(self):
        self.assertFalse(self.on_failure_was_called.is_set())
        self.actor_ref.tell({'command': 'raise exception'})
        self.on_failure_was_called.wait(5)
        self.assertTrue(self.on_failure_was_called.is_set())
        self.assertFalse(self.on_stop_was_called.is_set())

    def test_on_failure_failure_causes_actor_to_stop(self):
        failure_event = self.event_class()
        actor = self.FailingOnFailureActor.start(failure_event)
        actor.tell({'command': 'raise exception'})
        failure_event.wait(5)
        self.assertFalse(actor.is_alive())

    def test_actor_is_stopped_when_unhandled_exceptions_are_raised(self):
        self.assertFalse(self.on_failure_was_called.is_set())
        self.actor_ref.tell({'command': 'raise exception'})
        self.on_failure_was_called.wait(5)
        self.assertTrue(self.on_failure_was_called.is_set())
        self.assertEqual(0, len(ActorRegistry.get_all()))

    def test_all_actors_are_stopped_on_base_exception(self):
        start_event = self.event_class()
        stop_event = self.event_class()
        fail_event = self.event_class()
        registered_event = self.event_class()
        greetings_event = self.event_class()
        self.AnActor.start(
            on_start_was_called=start_event,
            on_stop_was_called=stop_event,
            on_failure_was_called=fail_event,
            actor_was_registered_before_on_start_was_called=registered_event,
            greetings_was_received=greetings_event)

        self.assertEqual(2, len(ActorRegistry.get_all()))
        self.assertFalse(self.on_stop_was_called.is_set())
        self.actor_ref.tell({'command': 'raise base exception'})
        self.on_stop_was_called.wait(5)
        self.assertTrue(self.on_stop_was_called.is_set())
        self.assert_(1 >= len(ActorRegistry.get_all()))
        stop_event.wait(5)
        self.assertTrue(stop_event.is_set())
        self.assertEqual(0, len(ActorRegistry.get_all()))

    def test_actor_can_call_stop_on_self_multiple_times(self):
        self.actor_ref.ask({'command': 'stop twice'})

    def test_actor_processes_all_messages_before_stop_on_self_stops_it(self):
        self.actor_ref.ask({'command': 'message self then stop'})

        self.greetings_was_received.wait(5)
        self.assertTrue(self.greetings_was_received.is_set())

        self.on_stop_was_called.wait(5)

        self.assertEqual(0, len(ActorRegistry.get_all()))


class ThreadingActorTest(ActorTest, unittest.TestCase):
    event_class = threading.Event

    class AnActor(AnActor, ThreadingActor):
        pass

    class EarlyStoppingActor(EarlyStoppingActor, ThreadingActor):
        pass

    class EarlyFailingActor(EarlyFailingActor, ThreadingActor):
        pass

    class LateFailingActor(LateFailingActor, ThreadingActor):
        pass

    class FailingOnFailureActor(FailingOnFailureActor, ThreadingActor):
        pass

    class SuperInitActor(ThreadingActor):
        pass

    class DaemonActor(ThreadingActor):
        use_daemon_thread = True

    def test_actor_thread_is_named_after_pykka_actor_class(self):
        alive_threads = threading.enumerate()
        alive_thread_names = [t.name for t in alive_threads]
        named_correctly = [
            name.startswith(AnActor.__name__) for name in alive_thread_names]
        self.assert_(any(named_correctly))

    def test_actor_thread_is_not_daemonic_by_default(self):
        alive_threads = threading.enumerate()
        actor_threads = [
            t for t in alive_threads if t.name.startswith('AnActor')]
        self.assertEqual(1, len(actor_threads))
        self.assertFalse(actor_threads[0].daemon)

    def test_actor_thread_is_daemonic_if_use_daemon_thread_flag_is_set(self):
        actor_ref = self.DaemonActor.start()
        alive_threads = threading.enumerate()
        actor_threads = [
            t for t in alive_threads if t.name.startswith('DaemonActor')]
        self.assertEqual(1, len(actor_threads))
        self.assertTrue(actor_threads[0].daemon)
        actor_ref.stop()


if HAS_GEVENT:
    class GeventActorTest(ActorTest, unittest.TestCase):
        event_class = gevent.event.Event

        class AnActor(AnActor, GeventActor):
            pass

        class EarlyStoppingActor(EarlyStoppingActor, GeventActor):
            pass

        class EarlyFailingActor(EarlyFailingActor, GeventActor):
            pass

        class LateFailingActor(LateFailingActor, GeventActor):
            pass

        class FailingOnFailureActor(FailingOnFailureActor, GeventActor):
            pass

        class SuperInitActor(GeventActor):
            pass
