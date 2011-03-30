import sys
import threading
import unittest
import uuid

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry


class AnActor(object):
    def __init__(self, on_start_was_called, on_stop_was_called,
            on_failure_was_called):
        self.on_start_was_called = on_start_was_called
        self.on_stop_was_called = on_stop_was_called
        self.on_failure_was_called = on_failure_was_called

    def on_start(self):
        self.on_start_was_called.set()

    def on_stop(self):
        self.on_stop_was_called.set()

    def on_failure(self, *args):
        self.on_failure_was_called.set()

    def on_receive(self, message):
        if message.get('command') == 'raise exception':
            raise Exception('foo')
        elif message.get('command') == 'raise KeyboardInterrupt':
            raise KeyboardInterrupt()
        else:
            super(AnActor, self).on_receive(message)


class ActorTest(object):
    def setUp(self):
        self.on_start_was_called = self.event_class()
        self.on_stop_was_called = self.event_class()
        self.on_failure_was_called = self.event_class()

        self.actor_ref = self.AnActor.start(self.on_start_was_called,
            self.on_stop_was_called, self.on_failure_was_called)
        self.actor_proxy = self.actor_ref.proxy()

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_actor_has_an_uuid4_based_urn(self):
        self.assertEqual(4, uuid.UUID(self.actor_ref.actor_urn).version)

    def test_actor_has_unique_uuid(self):
        event = self.event_class()
        actors = [self.AnActor.start(event, event, event) for _ in range(3)]

        self.assertNotEqual(actors[0].actor_urn, actors[1].actor_urn)
        self.assertNotEqual(actors[1].actor_urn, actors[2].actor_urn)
        self.assertNotEqual(actors[2].actor_urn, actors[0].actor_urn)

    def test_str_on_raw_actor_contains_actor_class_name(self):
        event = self.event_class()
        unstarted_actor = self.AnActor(event, event, event)
        self.assert_('AnActor' in str(unstarted_actor))

    def test_str_on_raw_actor_contains_actor_urn(self):
        event = self.event_class()
        unstarted_actor = self.AnActor(event, event, event)
        self.assert_(unstarted_actor.actor_urn in str(unstarted_actor))

    def test_on_start_is_called_before_first_message_is_processed(self):
        self.on_start_was_called.wait()
        self.assertTrue(self.on_start_was_called.is_set())

    def test_on_stop_is_called_when_actor_is_stopped(self):
        self.assertFalse(self.on_stop_was_called.is_set())
        self.actor_ref.stop()
        self.on_stop_was_called.wait()
        self.assertTrue(self.on_stop_was_called.is_set())

    def test_on_failure_is_called_when_exception_cannot_be_returned(self):
        self.assertFalse(self.on_failure_was_called.is_set())
        self.actor_ref.send_one_way({'command': 'raise exception'})
        self.on_failure_was_called.wait()
        self.assertTrue(self.on_failure_was_called.is_set())
        self.assertFalse(self.on_stop_was_called.is_set())

    def test_actor_is_stopped_when_unhandled_exceptions_are_raised(self):
        self.assertFalse(self.on_failure_was_called.is_set())
        self.actor_ref.send_one_way({'command': 'raise exception'})
        self.on_failure_was_called.wait()
        self.assertEqual(0, len(ActorRegistry.get_all()))

    def test_all_actors_are_stopped_on_keyboard_interrupt(self):
        start_event = self.event_class()
        stop_event = self.event_class()
        fail_event = self.event_class()
        another_actor = self.AnActor.start(start_event, stop_event, fail_event)

        self.assertEqual(2, len(ActorRegistry.get_all()))
        self.assertFalse(self.on_stop_was_called.is_set())
        self.actor_ref.send_one_way({'command': 'raise KeyboardInterrupt'})
        self.on_stop_was_called.wait()
        self.assert_(1 >= len(ActorRegistry.get_all()))
        stop_event.wait()
        self.assertEqual(0, len(ActorRegistry.get_all()))


class ThreadingActorTest(ActorTest, unittest.TestCase):
    event_class = threading.Event

    class AnActor(AnActor, ThreadingActor):
        pass


if sys.version_info < (3,):
    import gevent.event

    from pykka.gevent import GeventActor

    class GeventActorTest(ActorTest, unittest.TestCase):
        event_class = gevent.event.Event

        class AnActor(AnActor, GeventActor):
            pass
