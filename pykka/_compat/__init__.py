import sys


PY2 = sys.version_info[0] == 2

if PY2:
    import Queue as queue  # noqa
    from collections import Callable, Iterable  # noqa

    string_types = basestring  # noqa

    def reraise(tp, value, tb=None):
        exec('raise tp, value, tb')

    await_dunder_future = None
    await_keyword = None

else:
    import queue  # noqa
    from collections.abc import Callable, Iterable  # noqa

    string_types = (str,)

    def reraise(tp, value, tb=None):
        if value is None:
            value = tp()
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    # `async def` and return inside a generator are syntax errors on Python 2
    # so these must be hidden behind a conditional import.
    from pykka._compat.await_py3 import (  # noqa
        await_dunder_future,
        await_keyword,
    )
