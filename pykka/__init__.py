import gevent.monkey
gevent.monkey.patch_all()

from pykka.actor import Actor
from pykka.proxy import ActorProxy, CallableProxy
from pykka.ref import ActorRef
from pykka.registry import ActorRegistry


__all__ = ['Actor', 'ActorProxy', 'ActorRef', 'ActorRegistry', 'CallableProxy',
    'get_all', 'wait_all']


VERSION = (0, 6)

def get_version():
    """Returns a formatted version number"""
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if len(VERSION) > 2:
        version = '%s.%s' % (version, VERSION[2])
    return version

def get_all(results, timeout=None):
    """
    Get all values encapsulated in the list of
    :class:`gevent.event.AsyncResult`.

    :attr:`timeout` has the same behaviour as for :meth:`Future.get`.
    """
    return map(lambda result: result.get(timeout=timeout), results)

def wait_all(results, timeout=None):
    """
    Block until all :class:`gevent.event.AsyncResult` in the list are avaiable.

    An alias for :func:`get_all`, but with a name that is more describing if
    you do not care about the return values.
    """
    return get_all(results, timeout)
