"""Pykka is a Python implementation of the actor model."""

import importlib.metadata as _importlib_metadata
import logging as _logging

from pykka._exceptions import ActorDeadError, Timeout
from pykka._future import Future, get_all
from pykka._proxy import ActorProxy, CallableProxy, traversable
from pykka._ref import ActorRef
from pykka._registry import ActorRegistry

# The following must be imported late, in this specific order.
from pykka._actor import Actor  # isort:skip
from pykka._threading import ThreadingActor, ThreadingFuture  # isort:skip


__all__ = [
    "Actor",
    "ActorDeadError",
    "ActorProxy",
    "ActorRef",
    "ActorRegistry",
    "CallableProxy",
    "Future",
    "ThreadingActor",
    "ThreadingFuture",
    "Timeout",
    "get_all",
    "traversable",
]


#: Pykka's :pep:`396` and :pep:`440` compatible version number
__version__: str
try:
    __version__ = _importlib_metadata.version(__name__)
except _importlib_metadata.PackageNotFoundError:
    __version__ = "unknown"


_logging.getLogger(__name__).addHandler(_logging.NullHandler())
