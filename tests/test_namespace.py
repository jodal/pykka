def test_actor_dead_error_import():
    from pykka import ActorDeadError as ActorDeadError1
    from pykka.exceptions import ActorDeadError as ActorDeadError2

    assert ActorDeadError1 == ActorDeadError2


def test_timeout_import():
    from pykka import Timeout as Timeout1
    from pykka.exceptions import Timeout as Timeout2

    assert Timeout1 == Timeout2


def test_actor_import():
    from pykka import Actor as Actor1
    from pykka.actor import Actor as Actor2

    assert Actor1 == Actor2


def test_actor_ref_import():
    from pykka import ActorRef as ActorRef1
    from pykka.actor import ActorRef as ActorRef2

    assert ActorRef1 == ActorRef2


def test_threading_actor_import():
    from pykka import ThreadingActor as ThreadingActor1
    from pykka.threading import ThreadingActor as ThreadingActor2

    assert ThreadingActor1 == ThreadingActor2


def test_future_import():
    from pykka import Future as Future1
    from pykka.future import Future as Future2

    assert Future1 == Future2


def test_get_all_import():
    from pykka import get_all as get_all1
    from pykka.future import get_all as get_all2

    assert get_all1 == get_all2


def test_threading_future_import():
    from pykka import ThreadingFuture as ThreadingFuture1
    from pykka.threading import ThreadingFuture as ThreadingFuture2

    assert ThreadingFuture1 == ThreadingFuture2


def test_actor_proxy_import():
    from pykka import ActorProxy as ActorProxy1
    from pykka.proxy import ActorProxy as ActorProxy2

    assert ActorProxy1 == ActorProxy2


def test_actor_registry_import():
    from pykka import ActorRegistry as ActorRegistry1
    from pykka.registry import ActorRegistry as ActorRegistry2

    assert ActorRegistry1 == ActorRegistry2
