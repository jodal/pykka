import unittest

from pykka import Actor, ActorRegistry

class RegistryTest(unittest.TestCase):
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
        self.actor.stop().get() # Block until stopped
        self.assert_(self.actor not in ActorRegistry.get_all())

    def test_actor_may_be_registered_manually(self):
        ActorRegistry.unregister(self.actor)
        self.assert_(self.actor not in ActorRegistry.get_all())
        ActorRegistry.register(self.actor)
        self.assert_(self.actor in ActorRegistry.get_all())
