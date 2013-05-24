import mock
import unittest

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

class ActorRegistryTest(object):
    def setUp(self):
        self.ref = self.AnActor.start()
        self.a_actors = [self.AnActor.start() for _ in range(3)]
        self.b_actors = [self.BeeActor.start() for _ in range(5)]
        self.a_actor_0_urn = self.a_actors[0].actor_urn

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

    def test_actor_may_be_unregistered_multiple_times_without_error(self):
        ActorRegistry.unregister(self.ref)
        self.assert_(self.ref not in ActorRegistry.get_all())
        ActorRegistry.unregister(self.ref)
        self.assert_(self.ref not in ActorRegistry.get_all())
        ActorRegistry.register(self.ref)
        self.assert_(self.ref in ActorRegistry.get_all())

    def test_all_actors_can_be_stopped_through_registry(self):
        self.assertEquals(9, len(ActorRegistry.get_all()))
        ActorRegistry.stop_all(block=True)
        self.assertEquals(0, len(ActorRegistry.get_all()))

    @mock.patch.object(ActorRegistry, 'get_all')
    def test_stop_all_stops_last_started_actor_first_if_blocking(
            self, mock_method):
        stopped_actors = []
        started_actors = [mock.Mock(name=i) for i in range(3)]
        started_actors[0].stop.side_effect = lambda *a, **kw: \
            stopped_actors.append(started_actors[0])
        started_actors[1].stop.side_effect = lambda *a, **kw: \
            stopped_actors.append(started_actors[1])
        started_actors[2].stop.side_effect = lambda *a, **kw: \
            stopped_actors.append(started_actors[2])
        ActorRegistry.get_all.return_value = started_actors

        ActorRegistry.stop_all(block=True)

        self.assertEqual(stopped_actors[0], started_actors[2])
        self.assertEqual(stopped_actors[1], started_actors[1])
        self.assertEqual(stopped_actors[2], started_actors[0])

    def test_actors_may_be_looked_up_by_class(self):
        result = ActorRegistry.get_by_class(self.AnActor)
        for a_actor in self.a_actors:
            self.assert_(a_actor in result)
        for b_actor in self.b_actors:
            self.assert_(b_actor not in result)

    def test_actors_may_be_looked_up_by_superclass(self):
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

    def test_broadcast_sends_message_to_all_actors_if_no_target(self):
        ActorRegistry.broadcast({'command': 'foo'})
        for actor_ref in ActorRegistry.get_all():
            received_messages = actor_ref.proxy().received_messages.get()
            self.assert_({'command': 'foo'} in received_messages)

    def test_broadcast_sends_message_to_all_actors_of_given_class(self):
        ActorRegistry.broadcast({'command': 'foo'}, target_class=self.AnActor)
        for actor_ref in ActorRegistry.get_by_class(self.AnActor):
            received_messages = actor_ref.proxy().received_messages.get()
            self.assert_({'command': 'foo'} in received_messages)
        for actor_ref in ActorRegistry.get_by_class(self.BeeActor):
            received_messages = actor_ref.proxy().received_messages.get()
            self.assert_({'command': 'foo'} not in received_messages)

    def test_broadcast_sends_message_to_all_actors_of_given_class_name(self):
        ActorRegistry.broadcast({'command': 'foo'}, target_class='AnActor')
        for actor_ref in ActorRegistry.get_by_class(self.AnActor):
            received_messages = actor_ref.proxy().received_messages.get()
            self.assert_({'command': 'foo'} in received_messages)
        for actor_ref in ActorRegistry.get_by_class(self.BeeActor):
            received_messages = actor_ref.proxy().received_messages.get()
            self.assert_({'command': 'foo'} not in received_messages)


class AnActor(object):
    received_messages = None

    def __init__(self):
        super(AnActor, self).__init__()
        self.received_messages = []

    def on_receive(self, message):
        self.received_messages.append(message)


class BeeActor(object):
    received_messages = None

    def __init__(self):
        super(BeeActor, self).__init__()
        self.received_messages = []

    def on_receive(self, message):
        self.received_messages.append(message)


def ConcreteRegistryTest(actor_class):
    class C(ActorRegistryTest, unittest.TestCase):
        class AnActor(AnActor, actor_class):
            pass

        class BeeActor(BeeActor, actor_class):
            pass

    C.__name__ = '%sRegistryTest' % (actor_class.__name__,)
    return C

ThreadingActorRegistryTest = ConcreteRegistryTest(ThreadingActor)


try:
    from pykka.gevent import GeventActor

    GeventActorRegistryTest = ConcreteRegistryTest(GeventActor)
except ImportError:
    pass

try:
    from pykka.eventlet import EventletActor

    EventletActorRegistryTest = ConcreteRegistryTest(EventletActor)
except ImportError:
    pass
