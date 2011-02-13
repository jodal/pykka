import gevent.coros
import logging

logger = logging.getLogger('pykka')


class ActorRegistry(object):
    """
    Registry which provides easy access to all running actors.

    Contains global state, but should be thread-safe.
    """

    _actor_refs = []
    _actor_refs_lock = gevent.coros.RLock()

    @classmethod
    def get_all(cls):
        """Get :class:`ActorRef` for all running actors"""
        with cls._actor_refs_lock:
            return cls._actor_refs[:]

    @classmethod
    def get_by_class(cls, actor_class):
        """Get :class:`ActorRef` for all running actors of the given class"""
        with cls._actor_refs_lock:
            return [ref for ref in cls._actor_refs
                if ref.actor_class == actor_class]

    @classmethod
    def get_by_class_name(cls, actor_class_name):
        """
        Get :class:`ActorRef` for all running actors of the given class
        name
        """
        with cls._actor_refs_lock:
            return [ref for ref in cls._actor_refs
                if ref.actor_class.__name__ == actor_class_name]

    @classmethod
    def get_by_urn(cls, actor_urn):
        """
        Get an actor by its universally unique URN.

        Returns :class:`None` if no matching actor is found.
        """
        with cls._actor_refs_lock:
            refs = [ref for ref in cls._actor_refs
                if ref.actor_urn == actor_urn]
            if refs:
                return refs[0]

    @classmethod
    def register(cls, actor_ref):
        """
        Register an :class:`ActorRef` in the registry.

        This is done automatically when an actor is started, e.g. by calling
        :meth:`Actor.start`.
        """
        with cls._actor_refs_lock:
            cls._actor_refs.append(actor_ref)
        logger.debug(u'Registered %s', actor_ref)

    @classmethod
    def stop_all(cls, block=True, timeout=None):
        """
        Stop all running actors.

        If ``block`` is :class:`True`, it blocks forever or, if not
        :class:`None`, until ``timeout`` seconds has passed.

        If ``block`` is False, it returns a list with a future for each stop
        action.
        """
        return [ref.stop(block, timeout) for ref in cls.get_all()]

    @classmethod
    def unregister(cls, actor_ref):
        """
        Remove an :class:`ActorRef` from the registry.

        This is done automatically when an actor is stopped, e.g. by calling
        :meth:`Actor.stop`.
        """
        with cls._actor_refs_lock:
            cls._actor_refs.remove(actor_ref)
        logger.debug(u'Unregistered %s', actor_ref)
