import warnings

import pytest

from pykka.messaging import (
    ActorStop,
    Envelope,
    ProxyCall,
    ProxyGetAttr,
    ProxySetAttr,
    upgrade_internal_message,
)


def test_envelope_repr():
    envelope = Envelope('message', reply_to=123)

    assert repr(envelope) == "Envelope(message='message', reply_to=123)"


@pytest.mark.parametrize(
    'old_format, new_format',
    [
        ({'command': 'pykka_stop'}, ActorStop()),
        (
            {
                'command': 'pykka_call',
                'attr_path': ['nested', 'method'],
                'args': [1],
                'kwargs': {'a': 'b'},
            },
            ProxyCall(
                attr_path=['nested', 'method'], args=[1], kwargs={'a': 'b'}
            ),
        ),
        (
            {'command': 'pykka_getattr', 'attr_path': ['nested', 'attr']},
            ProxyGetAttr(attr_path=['nested', 'attr']),
        ),
        (
            {
                'command': 'pykka_setattr',
                'attr_path': ['nested', 'attr'],
                'value': 'abcdef',
            },
            ProxySetAttr(attr_path=['nested', 'attr'], value='abcdef'),
        ),
    ],
)
def test_upgrade_internal_message(old_format, new_format):
    with warnings.catch_warnings(record=True) as w:
        assert upgrade_internal_message(old_format) == new_format

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert 'Pykka received a dict-based internal message.' in str(
            w[0].message
        )
