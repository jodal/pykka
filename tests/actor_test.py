import unittest
import uuid

from pykka.actor import ThreadingActor
from pykka.gevent import GeventActor


class ActorTest(object):
    def setUp(self):
        self.unstarted_actor = self.AnActor()
        self.actor = self.AnActor.start()
        self.actors = [self.AnActor.start() for _ in range(3)]

    def tearDown(self):
        for actor in self.actors:
            actor.stop()

    def test_sending_unexpected_message_raises_not_implemented_error(self):
        try:
            self.actor.send_request_reply({'unhandled': 'message'})
            self.fail('Should throw NotImplementedError')
        except NotImplementedError:
            pass

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


class GeventActorTest(ActorTest, unittest.TestCase):
    class AnActor(GeventActor): pass


class ThreadingActorTest(ActorTest, unittest.TestCase):
    class AnActor(ThreadingActor): pass
