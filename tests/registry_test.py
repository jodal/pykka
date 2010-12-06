import unittest

from pykka import Actor, ActorRegistry

class ActorRegistrationTest(unittest.TestCase):
    def setUp(self):
        class AnActor(Actor):
            pass
        self.actor = AnActor().start()

    def tearDown(self):
        self.actor.stop()

    def test_actor_is_registered_when_started(self):
        self.assert_(self.actor in ActorRegistry.get_all())

    def test_actor_is_unregistered_when_stopped(self):
        self.assert_(self.actor in ActorRegistry.get_all())
        self.actor.stop().wait()
        self.assert_(self.actor not in ActorRegistry.get_all())

    def test_actor_may_be_registered_manually(self):
        ActorRegistry.unregister(self.actor)
        self.assert_(self.actor not in ActorRegistry.get_all())
        ActorRegistry.register(self.actor)
        self.assert_(self.actor in ActorRegistry.get_all())


class ActorLookupTest(unittest.TestCase):
    class AnActor(Actor): pass
    class BeeActor(Actor): pass

    def setUp(self):
        self.a_actors = [self.AnActor().start() for i in range(3)]
        self.b_actors = [self.BeeActor().start() for i in range(5)]

    def tearDown(self):
        map(lambda a: a.stop(), self.a_actors + self.b_actors)

    def test_actors_may_be_looked_up_class(self):
        result = ActorRegistry.get_by_class(self.AnActor)
        for a_actor in self.a_actors:
            self.assert_(a_actor in result)
        for b_actor in self.b_actors:
            self.assert_(b_actor not in result)

    def test_actors_may_be_looked_up_class_name(self):
        result = ActorRegistry.get_by_class_name('AnActor')
        for a_actor in self.a_actors:
            self.assert_(a_actor in result)
        for b_actor in self.b_actors:
            self.assert_(b_actor not in result)


class ActorStoppingTest(unittest.TestCase):
    def setUp(self):
        class AnActor(Actor): pass
        self.actors = [AnActor().start() for i in range(3)]

    def test_all_actors_can_be_stopped_through_registry(self):
        self.assertEquals(3, len(ActorRegistry.get_all()))
        futures = ActorRegistry.stop_all()
        map(lambda f: f.wait(), futures)
        self.assertEquals(0, len(ActorRegistry.get_all()))
