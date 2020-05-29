import logging as _logging

import pkg_resources as _pkg_resources

from pykka._exceptions import ActorDeadError, Timeout
from pykka._future import Future, get_all
from pykka._proxy import ActorProxy, CallableProxy, traversable
from pykka._ref import ActorRef
from pykka._registry import ActorRegistry
from pykka._actor import Actor  # noqa: Must be imported late
from pykka._scheduler import Cancellable, Scheduler
from pykka._threading import ThreadingActor, ThreadingFuture, ThreadingScheduler


__all__ = [
    "Actor",
    "ActorDeadError",
    "ActorProxy",
    "ActorRef",
    "ActorRegistry",
    "CallableProxy",
    "Cancellable",
    "Future",
    "Scheduler",
    "ThreadingScheduler",
    "ThreadingActor",
    "ThreadingFuture",
    "Timeout",
    "get_all",
    "traversable",
]


#: Pykka's :pep:`396` and :pep:`440` compatible version number
__version__ = _pkg_resources.get_distribution("pykka").version


_logging.getLogger("pykka").addHandler(_logging.NullHandler())
