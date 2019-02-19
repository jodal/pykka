import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
GT_PY34 = sys.version_info > (3, 4)

if PY2:
    import Queue as queue  # noqa
    from collections import Callable, Iterable  # noqa

    string_types = basestring  # noqa

    def reraise(tp, value, tb=None):
        exec('raise tp, value, tb')


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


if PY3:

    # Return inside a generator is a syntax error on python2
    # so we need to dynamically load it
    from pykka.compat.await_dunder_future_py3 import await_dunder_future  # noqa

else:

    await_dunder_future = None


if GT_PY34:
    from pykka.compat.await_keyword_py3 import await_keyword  # noqa
else:

    await_keyword = None
