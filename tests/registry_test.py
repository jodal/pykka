import unittest

from pykka import Actor, ActorRegistry

class AnActor(Actor):
    pass


class BeeActor(Actor):
    pass


class ActorRegistrationTest(unittest.TestCase):
    def setUp(self):
        self.ref = AnActor.start()

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_actor_is_registered_when_started(self):
        self.assert_(self.ref in ActorRegistry.get_all())

    def test_actor_is_unregistered_when_stopped(self):
        self.assert_(self.ref in ActorRegistry.get_all())
        self.ref.stop()
        self.assert_(self.ref not in ActorRegistry.get_all())

    def test_actor_may_be_registered_manually(self):
        ActorRegistry.unregister(self.ref)
        self.assert_(self.ref not in ActorRegistry.get_all())
        ActorRegistry.register(self.ref)
        self.assert_(self.ref in ActorRegistry.get_all())


class ActorLookupTest(unittest.TestCase):
    def setUp(self):
        self.a_actors = [AnActor.start() for i in range(3)]
        self.b_actors = [BeeActor.start() for i in range(5)]
        self.a_actor_0_urn = self.a_actors[0].actor_urn

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_actors_may_be_looked_up_by_class(self):
        result = ActorRegistry.get_by_class(AnActor)
        for a_actor in self.a_actors:
            self.assert_(a_actor in result)
        for b_actor in self.b_actors:
            self.assert_(b_actor not in result)

    def test_actors_may_be_looked_up_by_class_name(self):
        result = ActorRegistry.get_by_class_name('AnActor')
        for a_actor in self.a_actors:
            self.assert_(a_actor in result)
        for b_actor in self.b_actors:
            self.assert_(b_actor not in result)

    def test_actors_may_be_looked_up_by_urn(self):
        result = ActorRegistry.get_by_urn(self.a_actor_0_urn)
        self.assertEqual(self.a_actors[0], result)

    def test_get_by_urn_returns_none_if_not_found(self):
        result = ActorRegistry.get_by_urn('urn:foo:bar')
        self.assertEqual(None, result)


class ActorStoppingTest(unittest.TestCase):
    def setUp(self):
        self.actors = [AnActor.start() for i in range(3)]

    def test_all_actors_can_be_stopped_through_registry(self):
        self.assertEquals(3, len(ActorRegistry.get_all()))
        ActorRegistry.stop_all(block=True)
        self.assertEquals(0, len(ActorRegistry.get_all()))
