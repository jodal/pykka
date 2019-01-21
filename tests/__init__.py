import pytest


try:
    import eventlet  # noqa
except ImportError:
    has_eventlet = pytest.mark.skipif(True, reason='eventlet required')
else:
    has_eventlet = pytest.mark.skipif(False, reason='eventlet required')


try:
    import gevent  # noqa
except ImportError:
    has_gevent = pytest.mark.skipif(True, reason='gevent required')
else:
    has_gevent = pytest.mark.skipif(False, reason='gevent required')
