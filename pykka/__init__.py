#: Pykka's version as a tuple that can be used for comparison
VERSION = (0, 13, 0)


def get_version():
    """Returns Pykka's version as a formatted string"""
    return '.'.join(map(str, VERSION))


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
