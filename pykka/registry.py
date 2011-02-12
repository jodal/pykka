import gevent.coros
import logging

logger = logging.getLogger('pykka')


class ActorRegistry(object):
    """
    Registry which provides easy access to all running actors.

    Contains global state, but should be thread-safe.
    """

    _actors = []
    _actors_lock = gevent.coros.RLock()

    @classmethod
    def get_all(cls):
        """Get all running actors"""
        with cls._actors_lock:
            return cls._actors[:]

    @classmethod
    def get_by_class(cls, actor_class):
        """Get all running actors of the given class"""
        with cls._actors_lock:
            return filter(lambda a: a._actor_class == actor_class, cls._actors)

    @classmethod
    def get_by_class_name(cls, actor_class_name):
        """Get all running actors of the given class name"""
        with cls._actors_lock:
            return filter(
                lambda a: a._actor_class.__name__ == actor_class_name,
                cls._actors)

    @classmethod
    def get_by_urn(cls, actor_urn):
        """
        Get an actor by its universally unique URN.

        Returns :class:`None` if no matching actor is found.
        """
        with cls._actors_lock:
            actors = filter(lambda a: a.actor_urn == actor_urn, cls._actors)
            if actors:
                return actors[0]

    @classmethod
    def register(cls, actor):
        """
        Register an actor in the registry.

        This is done automatically when an actor is started.
        """
        with cls._actors_lock:
            cls._actors.append(actor)
        logger.debug(u'Registered %s', actor)

    @classmethod
    def stop_all(cls):
        """
        Stops all running actors.

        Returns a list of futures for all the stopping actors, so that you can
        block until they have stopped if you need to.
        """
        with cls._actors_lock:
            return [a.stop() for a in cls._actors]

    @classmethod
    def unregister(cls, actor):
        """
        Remove an actor from the registry.

        This is done automatically when an actor is stopped.
        """
        with cls._actors_lock:
            cls._actors.remove(actor)
        logger.debug(u'Unregistered %s', actor)
