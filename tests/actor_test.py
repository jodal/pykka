import logging
import sys
import threading
import unittest
import uuid

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from tests import TestLogHandler


class AnActor(object):
    def __init__(self, pre_start_was_called, post_stop_was_called,
            on_failure_was_called):
        self.pre_start_was_called = pre_start_was_called
        self.post_stop_was_called = post_stop_was_called
        self.on_failure_was_called = on_failure_was_called

    def pre_start(self):
        self.pre_start_was_called.set()

    def post_stop(self):
        self.post_stop_was_called.set()

    def on_failure(self, *args):
        self.on_failure_was_called.set()

    def react(self, message):
        if message.get('command') == 'raise exception':
            return self.raise_exception()
        else:
            super(AnActor, self).react(message)


class ActorTest(object):
    def setUp(self):
        self.pre_start_was_called = self.event_class()
        self.post_stop_was_called = self.event_class()
        self.on_failure_was_called = self.event_class()

        self.actor_ref = self.AnActor.start(self.pre_start_was_called,
            self.post_stop_was_called, self.on_failure_was_called)
        self.actor_proxy = self.actor_ref.proxy()

        self.log_handler = TestLogHandler(logging.DEBUG)
        self.root_logger = logging.getLogger()
        self.root_logger.addHandler(self.log_handler)

    def tearDown(self):
        self.log_handler.close()
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

    def test_pre_start_is_called_before_first_message_is_processed(self):
        self.pre_start_was_called.wait()
        self.assertTrue(self.pre_start_was_called.is_set())

    def test_post_stop_is_called_when_actor_is_stopped(self):
        self.assertFalse(self.post_stop_was_called.is_set())
        self.actor_ref.stop()
        self.post_stop_was_called.wait()
        self.assertTrue(self.post_stop_was_called.is_set())

    def test_unexpected_messages_are_logged(self):
        self.actor_ref.send_request_reply({'unhandled': 'message'})
        self.assertEqual(1, len(self.log_handler.messages['warning']))
        log_record = self.log_handler.messages['warning'][0]
        self.assertEqual('Unexpected message received by %s' % self.actor_ref,
            log_record.getMessage().split(': ')[0])



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
