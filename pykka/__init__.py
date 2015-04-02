from pykka.actor import Actor, ActorRef
from pykka.exceptions import ActorDeadError, Timeout
from pykka.future import Future, get_all
from pykka.proxy import ActorProxy
from pykka.registry import ActorRegistry
from pykka.threading import ThreadingActor, ThreadingFuture


__all__ = [
    'Actor',
    'ActorDeadError',
    'ActorProxy',
    'ActorRef',
    'ActorRegistry',
    'Future',
    'ThreadingActor',
    'ThreadingFuture',
    'Timeout',
    'get_all',
]


#: Pykka's :pep:`386` and :pep:`396` compatible version number
__version__ = '1.2.0'


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
