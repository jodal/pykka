import warnings

import pytest

from pykka.messages import (
    ProxyCall,
    ProxyGetAttr,
    ProxySetAttr,
    _ActorStop,
    _upgrade_internal_message,
)


@pytest.mark.parametrize(
    'old_format, new_format',
    [
        ({'command': 'pykka_stop'}, _ActorStop()),
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
        assert _upgrade_internal_message(old_format) == new_format

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert 'Pykka received a dict-based internal message.' in str(
            w[0].message
        )
