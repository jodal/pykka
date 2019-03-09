from pykka.actor import Actor
from pykka.exceptions import ActorDeadError, Timeout
from pykka.future import Future, get_all
from pykka.proxy import ActorProxy, CallableProxy
from pykka.ref import ActorRef
from pykka.registry import ActorRegistry
from pykka.threading import ThreadingActor, ThreadingFuture


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
]


#: Pykka's :pep:`396` and :pep:`440` compatible version number
__version__ = '2.0.0a1'


def _add_null_handler_for_logging():
    import logging

    try:
        NullHandler = logging.NullHandler  # Python 2.7 and upwards
    except AttributeError:

        class NullHandler(logging.Handler):
            def emit(self, record):
                pass

    logging.getLogger('pykka').addHandler(NullHandler())


_add_null_handler_for_logging()
