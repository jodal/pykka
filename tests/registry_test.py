import unittest

import pykka

class ActorRegistrationTest(unittest.TestCase):
    def setUp(self):
        class AnActor(pykka.Actor): pass
        self.actor = AnActor.start()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_actor_is_registered_when_started(self):
        self.assert_(self.actor in pykka.ActorRegistry.get_all())

    def test_actor_is_unregistered_when_stopped(self):
        self.assert_(self.actor in pykka.ActorRegistry.get_all())
        self.actor.stop().wait()
        self.assert_(self.actor not in pykka.ActorRegistry.get_all())

    def test_actor_may_be_registered_manually(self):
        pykka.ActorRegistry.unregister(self.actor)
        self.assert_(self.actor not in pykka.ActorRegistry.get_all())
        pykka.ActorRegistry.register(self.actor)
        self.assert_(self.actor in pykka.ActorRegistry.get_all())


class ActorLookupTest(unittest.TestCase):
    class AnActor(pykka.Actor): pass
    class BeeActor(pykka.Actor): pass

    def setUp(self):
        self.a_actors = [self.AnActor.start() for i in range(3)]
        self.b_actors = [self.BeeActor.start() for i in range(5)]

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_actors_may_be_looked_up_class(self):
        result = pykka.ActorRegistry.get_by_class(self.AnActor)
        for a_actor in self.a_actors:
            self.assert_(a_actor in result)
        for b_actor in self.b_actors:
            self.assert_(b_actor not in result)

    def test_actors_may_be_looked_up_class_name(self):
        result = pykka.ActorRegistry.get_by_class_name('AnActor')
        for a_actor in self.a_actors:
            self.assert_(a_actor in result)
        for b_actor in self.b_actors:
            self.assert_(b_actor not in result)


class ActorStoppingTest(unittest.TestCase):
    def setUp(self):
        class AnActor(pykka.Actor): pass
        self.actors = [AnActor.start() for i in range(3)]

    def test_all_actors_can_be_stopped_through_registry(self):
        self.assertEquals(3, len(pykka.ActorRegistry.get_all()))
        pykka.wait_all(pykka.ActorRegistry.stop_all())
        self.assertEquals(0, len(pykka.ActorRegistry.get_all()))
