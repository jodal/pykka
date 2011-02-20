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
        """
        Get :class:`pykka.actor.ActorRef` for all running actors.

        :returns: list of :class:`pykka.actor.ActorRef`
        """
        with cls._actor_refs_lock:
            return cls._actor_refs[:]

    @classmethod
    def get_by_class(cls, actor_class):
        """
        Get :class:`ActorRef` for all running actors of the given class.

        :param actor_class: actor class
        :type actor_class: :class:`pykka.actor.Actor` subclass

        :returns: list of :class:`pykka.actor.ActorRef`
        """
        with cls._actor_refs_lock:
            return [ref for ref in cls._actor_refs
                if ref.actor_class == actor_class]

    @classmethod
    def get_by_class_name(cls, actor_class_name):
        """
        Get :class:`ActorRef` for all running actors of the given class
        name.

        :param actor_class_name: actor class name
        :type actor_class_name: string

        :returns: list of :class:`pykka.actor.ActorRef`
        """
        with cls._actor_refs_lock:
            return [ref for ref in cls._actor_refs
                if ref.actor_class.__name__ == actor_class_name]

    @classmethod
    def get_by_urn(cls, actor_urn):
        """
        Get an actor by its universally unique URN.

        :param actor_urn: actor URN
        :type actor_urn: string

        :returns: :class:`pykka.actor.ActorRef` or :class:`None` if not found
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
        :meth:`pykka.actor.Actor.start`.

        :param actor_ref: reference to the actor to register
        :type actor_ref: :class:`pykka.actor.ActorRef`
        """
        with cls._actor_refs_lock:
            cls._actor_refs.append(actor_ref)
        logger.debug(u'Registered %s', actor_ref)

    @classmethod
    def stop_all(cls, block=True, timeout=None):
        """
        Stop all running actors.

        ``block`` and ``timeout`` works as for
        :meth:`pykka.actor.ActorRef.stop`.

        :returns: If not blocking, a list with a future for each stop action.
            If blocking, a list of return values from
            :meth:`pykka.actor.ActorRef.stop`.
        """
        return [ref.stop(block, timeout) for ref in cls.get_all()]

    @classmethod
    def unregister(cls, actor_ref):
        """
        Remove an :class:`pykka.actor.ActorRef` from the registry.

        This is done automatically when an actor is stopped, e.g. by calling
        :meth:`pykka.actor.Actor.stop`.

        :param actor_ref: reference to the actor to unregister
        :type actor_ref: :class:`pykka.actor.ActorRef`
        """
        with cls._actor_refs_lock:
            cls._actor_refs.remove(actor_ref)
        logger.debug(u'Unregistered %s', actor_ref)
