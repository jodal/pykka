import pytest

from pykka import ActorRegistry

pytestmark = pytest.mark.usefixtures("stop_all")


class ActorBase:
    received_messages = None

    def __init__(self):
        super().__init__()
        self.received_messages = []

    def on_receive(self, message):
        self.received_messages.append(message)


@pytest.fixture(scope="module")
def actor_a_class(runtime):
    class ActorA(ActorBase, runtime.actor_class):
        pass

    return ActorA


@pytest.fixture(scope="module")
def actor_b_class(runtime):
    class ActorB(ActorBase, runtime.actor_class):
        pass

    return ActorB


@pytest.fixture
def actor_ref(actor_a_class):
    return actor_a_class.start()


@pytest.fixture
def a_actor_refs(actor_a_class):
    return [actor_a_class.start() for _ in range(3)]


@pytest.fixture
def b_actor_refs(actor_b_class):
    return [actor_b_class.start() for _ in range(5)]


def test_actor_is_registered_when_started(actor_ref):
    assert actor_ref in ActorRegistry.get_all()


def test_actor_is_unregistered_when_stopped(actor_ref):
    assert actor_ref in ActorRegistry.get_all()

    actor_ref.stop()

    assert actor_ref not in ActorRegistry.get_all()


def test_actor_may_be_registered_manually(actor_ref):
    ActorRegistry.unregister(actor_ref)
    assert actor_ref not in ActorRegistry.get_all()

    ActorRegistry.register(actor_ref)

    assert actor_ref in ActorRegistry.get_all()


def test_actor_may_be_unregistered_multiple_times_without_error(actor_ref):
    ActorRegistry.unregister(actor_ref)
    assert actor_ref not in ActorRegistry.get_all()

    ActorRegistry.unregister(actor_ref)
    assert actor_ref not in ActorRegistry.get_all()

    ActorRegistry.register(actor_ref)
    assert actor_ref in ActorRegistry.get_all()


def test_all_actors_can_be_stopped_through_registry(a_actor_refs, b_actor_refs):
    assert len(ActorRegistry.get_all()) == 8

    ActorRegistry.stop_all(block=True)

    assert len(ActorRegistry.get_all()) == 0


def test_stop_all_stops_last_started_actor_first_if_blocking(mocker):
    mocker.patch.object(ActorRegistry, "get_all")

    stopped_actors = []
    started_actors = [mocker.Mock(name=i) for i in range(3)]
    started_actors[0].stop.side_effect = lambda *a, **kw: stopped_actors.append(
        started_actors[0]
    )
    started_actors[1].stop.side_effect = lambda *a, **kw: stopped_actors.append(
        started_actors[1]
    )
    started_actors[2].stop.side_effect = lambda *a, **kw: stopped_actors.append(
        started_actors[2]
    )
    ActorRegistry.get_all.return_value = started_actors

    ActorRegistry.stop_all(block=True)

    assert stopped_actors[0] == started_actors[2]
    assert stopped_actors[1] == started_actors[1]
    assert stopped_actors[2] == started_actors[0]


def test_actors_may_be_looked_up_by_class(actor_a_class, a_actor_refs, b_actor_refs):
    result = ActorRegistry.get_by_class(actor_a_class)

    for a_actor in a_actor_refs:
        assert a_actor in result
    for b_actor in b_actor_refs:
        assert b_actor not in result


def test_actors_may_be_looked_up_by_superclass(
    actor_a_class, a_actor_refs, b_actor_refs
):
    result = ActorRegistry.get_by_class(actor_a_class)

    for a_actor in a_actor_refs:
        assert a_actor in result
    for b_actor in b_actor_refs:
        assert b_actor not in result


def test_actors_may_be_looked_up_by_class_name(
    actor_a_class, a_actor_refs, b_actor_refs
):
    result = ActorRegistry.get_by_class_name("ActorA")

    for a_actor in a_actor_refs:
        assert a_actor in result
    for b_actor in b_actor_refs:
        assert b_actor not in result


def test_actors_may_be_looked_up_by_urn(actor_ref):
    result = ActorRegistry.get_by_urn(actor_ref.actor_urn)

    assert result == actor_ref


def test_get_by_urn_returns_none_if_not_found():
    result = ActorRegistry.get_by_urn("urn:foo:bar")

    assert result is None


def test_broadcast_sends_message_to_all_actors_if_no_target(a_actor_refs, b_actor_refs):
    ActorRegistry.broadcast({"command": "foo"})

    running_actors = ActorRegistry.get_all()
    assert running_actors

    for actor_ref in running_actors:
        received_messages = actor_ref.proxy().received_messages.get()
        assert {"command": "foo"} in received_messages


def test_broadcast_sends_message_to_all_actors_of_given_class(
    actor_a_class, actor_b_class
):
    ActorRegistry.broadcast({"command": "foo"}, target_class=actor_a_class)

    for actor_ref in ActorRegistry.get_by_class(actor_a_class):
        received_messages = actor_ref.proxy().received_messages.get()
        assert {"command": "foo"} in received_messages

    for actor_ref in ActorRegistry.get_by_class(actor_b_class):
        received_messages = actor_ref.proxy().received_messages.get()
        assert {"command": "foo"} not in received_messages


def test_broadcast_sends_message_to_all_actors_of_given_class_name(
    actor_a_class, actor_b_class
):
    ActorRegistry.broadcast({"command": "foo"}, target_class="ActorA")

    for actor_ref in ActorRegistry.get_by_class(actor_a_class):
        received_messages = actor_ref.proxy().received_messages.get()
        assert {"command": "foo"} in received_messages

    for actor_ref in ActorRegistry.get_by_class(actor_b_class):
        received_messages = actor_ref.proxy().received_messages.get()
        assert {"command": "foo"} not in received_messages
