import unittest


class NamespaceTest(unittest.TestCase):
    def test_actor_dead_error_import(self):
        from pykka import ActorDeadError as ActorDeadError1
        from pykka.exceptions import ActorDeadError as ActorDeadError2
        self.assertEqual(ActorDeadError1, ActorDeadError2)

    def test_timeout_import(self):
        from pykka import Timeout as Timeout1
        from pykka.exceptions import Timeout as Timeout2
        self.assertEqual(Timeout1, Timeout2)

    def test_actor_import(self):
        from pykka import Actor as Actor1
        from pykka.actor import Actor as Actor2
        self.assertEqual(Actor1, Actor2)

    def test_actor_ref_import(self):
        from pykka import ActorRef as ActorRef1
        from pykka.actor import ActorRef as ActorRef2
        self.assertEqual(ActorRef1, ActorRef2)

    def test_threading_actor_import(self):
        from pykka import ThreadingActor as ThreadingActor1
        from pykka.actor import ThreadingActor as ThreadingActor2
        self.assertEqual(ThreadingActor1, ThreadingActor2)

    def test_future_import(self):
        from pykka import Future as Future1
        from pykka.future import Future as Future2
        self.assertEqual(Future1, Future2)

    def test_get_all_import(self):
        from pykka import get_all as get_all1
        from pykka.future import get_all as get_all2
        self.assertEqual(get_all1, get_all2)

    def test_threading_future_import(self):
        from pykka import ThreadingFuture as ThreadingFuture1
        from pykka.future import ThreadingFuture as ThreadingFuture2
        self.assertEqual(ThreadingFuture1, ThreadingFuture2)

    def test_actor_proxy_import(self):
        from pykka import ActorProxy as ActorProxy1
        from pykka.proxy import ActorProxy as ActorProxy2
        self.assertEqual(ActorProxy1, ActorProxy2)

    def test_actor_registry_import(self):
        from pykka import ActorRegistry as ActorRegistry1
        from pykka.registry import ActorRegistry as ActorRegistry2
        self.assertEqual(ActorRegistry1, ActorRegistry2)
