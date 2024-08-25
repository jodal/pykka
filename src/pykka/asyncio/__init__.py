"""Pykka is a Python implementation of the actor model."""

import importlib.metadata as _importlib_metadata
import logging as _logging

from pykka._exceptions import ActorDeadError, Timeout
from pykka.asyncio._future import Future, get_all
from pykka.asyncio._proxy import ActorProxy, CallableProxy, traversable
from pykka.asyncio._ref import ActorRef
from pykka.asyncio._registry import ActorRegistry

# The following must be imported late, in this specific order.
from pykka.asyncio._actor import Actor  # isort:skip
from pykka.asyncio._async import AsyncActor, AsyncFuture  # isort:skip


__all__ = [
    "Actor",
    "ActorDeadError",
    "ActorProxy",
    "ActorRef",
    "ActorRegistry",
    "CallableProxy",
    "Future",
    "AsyncActor",
    "AsyncFuture",
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
