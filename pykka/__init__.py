#: Pykka's :pep:`386` and :pep:`396` compatible version number
__version__ = '0.14'

#: Pykka's version as a tuple that can be used for comparison
#:
#: .. deprecated:: 0.14
#:    Use :attr:`__version__` instead. This will be removed in a future
#:    release.
VERSION = tuple(map(int, __version__.split('.')))

def get_version():
    """
    Returns Pykka's version as a formatted string

    .. deprecated:: 0.14
       Use :attr:`__version__` instead. This will be removed in a future
       release.
    """
    return __version__


# pylint: disable = W0404
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
# pylint: enable = W0404


class ActorDeadError(Exception):
    """Exception raised when trying to use a dead or unavailable actor."""
    pass


class Timeout(Exception):
    """Exception raised at future timeout."""
    pass
