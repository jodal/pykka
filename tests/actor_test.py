import unittest
import uuid

from pykka import Actor


class ActorReactTest(unittest.TestCase):
    def setUp(self):
        class ActorWithoutCustomReact(Actor):
            pass
        self.actor = ActorWithoutCustomReact()

    def test_sending_unexpected_message_raises_not_implemented_error(self):
        try:
            self.actor._react({'unhandled': 'message'})
            self.fail('Should throw NotImplementedError')
        except NotImplementedError:
            pass


class ActorUrnTest(unittest.TestCase):
    def setUp(self):
        class AnActor(Actor):
            pass
        self.actors = [AnActor.start() for _ in range(3)]

    def tearDown(self):
        for actor in self.actors:
            actor.stop()

    def test_actor_has_an_uuid4_based_urn(self):
        self.assertEqual(4, uuid.UUID(self.actors[0].actor_urn).version)

    def test_actor_has_unique_uuid(self):
        self.assertNotEqual(self.actors[0].actor_urn, self.actors[1].actor_urn)
        self.assertNotEqual(self.actors[1].actor_urn, self.actors[2].actor_urn)
        self.assertNotEqual(self.actors[2].actor_urn, self.actors[0].actor_urn)


class ActorStrTest(unittest.TestCase):
    def setUp(self):
        class AnActor(Actor):
            pass
        self.unstarted_actor = AnActor()

    def test_str_on_proxy_contains_actor_class_name(self):
        self.assert_('AnActor' in str(self.unstarted_actor))

    def test_str_on_proxy_contains_actor_urn(self):
        self.assert_(self.unstarted_actor.actor_urn
            in str(self.unstarted_actor))
