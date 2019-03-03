import pytest


@pytest.fixture(scope='module')
def actor_class(runtime):
    class ActorA(runtime.actor_class):
        an_attr = 'a value'

        def a_method(self):
            return 'a return value'

    return ActorA


@pytest.fixture
def actor_ref(actor_class):
    actor_ref = actor_class.start()
    yield actor_ref
    actor_ref.stop()


def test_proxy_call_via_legacy_message(actor_ref):
    with pytest.deprecated_call():
        result = actor_ref.ask(
            {
                'command': 'pykka_call',
                'attr_path': ['a_method'],
                'args': [],
                'kwargs': {},
            }
        )

    assert result == 'a return value'


def test_proxy_attr_via_legacy_message(actor_ref):
    with pytest.deprecated_call():
        result_before = actor_ref.ask(
            {'command': 'pykka_getattr', 'attr_path': ['an_attr']}
        )
        actor_ref.tell(
            {
                'command': 'pykka_setattr',
                'attr_path': ['an_attr'],
                'value': 'new value',
            }
        )
        result_after = actor_ref.ask(
            {'command': 'pykka_getattr', 'attr_path': ['an_attr']}
        )

    assert result_before == 'a value'
    assert result_after == 'new value'
