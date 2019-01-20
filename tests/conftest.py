import threading
import time
from collections import namedtuple

import pytest

from pykka import ActorRegistry, ThreadingActor, ThreadingFuture


Runtime = namedtuple(
    'Runtime',
    ['name', 'actor_class', 'event_class', 'future_class', 'sleep_func'],
)


RUNTIMES = {
    'threading': pytest.param(
        Runtime(
            name='threading',
            actor_class=ThreadingActor,
            event_class=threading.Event,
            future_class=ThreadingFuture,
            sleep_func=time.sleep,
        ),
        id='threading',
    )
}

try:
    import gevent
    import gevent.event
    from pykka.gevent import GeventActor, GeventFuture
except ImportError:
    RUNTIMES['gevent'] = pytest.param(
        None,
        id='gevent',
        marks=pytest.mark.skip(reason='skipping gevent tests'),
    )
else:
    RUNTIMES['gevent'] = pytest.param(
        Runtime(
            name='gevent',
            actor_class=GeventActor,
            event_class=gevent.event.Event,
            future_class=GeventFuture,
            sleep_func=gevent.sleep,
        ),
        id='gevent',
    )

try:
    import eventlet
    from pykka.eventlet import EventletActor, EventletEvent, EventletFuture
except ImportError:
    RUNTIMES['eventlet'] = pytest.param(
        None,
        id='eventlet',
        marks=pytest.mark.skip(reason='skipping eventlet tests'),
    )
else:
    RUNTIMES['eventlet'] = pytest.param(
        Runtime(
            name='eventlet',
            actor_class=EventletActor,
            event_class=EventletEvent,
            future_class=EventletFuture,
            sleep_func=eventlet.sleep,
        ),
        id='eventlet',
    )


@pytest.fixture(scope='session')
def eventlet_runtime():
    return RUNTIMES['eventlet'].values[0]


@pytest.fixture(scope='session')
def gevent_runtime():
    return RUNTIMES['gevent'].values[0]


@pytest.fixture(scope='session', params=RUNTIMES.values())
def runtime(request):
    return request.param


@pytest.fixture
def stop_all():
    yield
    ActorRegistry.stop_all()
