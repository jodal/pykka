import logging
import sys
import unittest
import uuid

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from tests import TestLogHandler


class AnActor(object):
    def __init__(self):
        self.pre_start_was_executed = False

    def pre_start(self):
        self.pre_start_was_executed = True

    def post_stop(self):
        pass

    def react(self, message):
        if message.get('command') == 'get pre_start_was_executed':
            return self.pre_start_was_executed
        else:
            super(AnActor, self).react(message)


class ActorTest(object):
    def setUp(self):
        self.unstarted_actor = self.AnActor()
        self.actor_ref = self.AnActor.start()
        self.actor_proxy = self.actor_ref.proxy()
        self.actors = [self.AnActor.start() for _ in range(3)]
        self.log_handler = TestLogHandler(logging.DEBUG)
        self.root_logger = logging.getLogger()
        self.root_logger.addHandler(self.log_handler)

    def tearDown(self):
        self.log_handler.close()
        ActorRegistry.stop_all()

    def test_unexpected_messages_are_logged(self):
        self.actor_ref.send_request_reply({'unhandled': 'message'})
        self.assertEqual(1, len(self.log_handler.messages['warning']))
        log_record = self.log_handler.messages['warning'][0]
        self.assertEqual('Unexpected message received by %s' % self.actor_ref,
            log_record.getMessage().split(': ')[0])

    def test_actor_has_an_uuid4_based_urn(self):
        self.assertEqual(4, uuid.UUID(self.actors[0].actor_urn).version)

    def test_actor_has_unique_uuid(self):
        self.assertNotEqual(self.actors[0].actor_urn, self.actors[1].actor_urn)
        self.assertNotEqual(self.actors[1].actor_urn, self.actors[2].actor_urn)
        self.assertNotEqual(self.actors[2].actor_urn, self.actors[0].actor_urn)

    def test_str_on_raw_actor_contains_actor_class_name(self):
        self.assert_('AnActor' in str(self.unstarted_actor))

    def test_str_on_raw_actor_contains_actor_urn(self):
        self.assert_(self.unstarted_actor.actor_urn
            in str(self.unstarted_actor))

    def test_pre_start_is_executed_before_first_message_is_processed(self):
        self.assertFalse(self.unstarted_actor.pre_start_was_executed)
        self.assertTrue(self.actor_ref.send_request_reply(
            {'command': 'get pre_start_was_executed'}))

    def test_post_stop_is_executed_when_actor_is_stopped(self):
        pass  # What's a good way of testing this?


class ThreadingActorTest(ActorTest, unittest.TestCase):
    class AnActor(AnActor, ThreadingActor):
        pass


if sys.version_info < (3,):
    from pykka.gevent import GeventActor

    class GeventActorTest(ActorTest, unittest.TestCase):
        class AnActor(AnActor, GeventActor):
            pass
