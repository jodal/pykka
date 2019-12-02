import logging as _logging

from pykka._exceptions import ActorDeadError, Timeout
from pykka._future import Future, get_all
from pykka._proxy import ActorProxy, CallableProxy, traversable
from pykka._ref import ActorRef
from pykka._registry import ActorRegistry
from pykka._actor import Actor  # noqa: Must be imported late
from pykka._threading import ThreadingActor, ThreadingFuture


__all__ = [
    'Actor',
    'ActorDeadError',
    'ActorProxy',
    'ActorRef',
    'ActorRegistry',
    'CallableProxy',
    'Future',
    'ThreadingActor',
    'ThreadingFuture',
    'Timeout',
    'get_all',
    'traversable',
]


#: Pykka's :pep:`396` and :pep:`440` compatible version number
__version__ = '2.0.2'


_logging.getLogger('pykka').addHandler(_logging.NullHandler())
