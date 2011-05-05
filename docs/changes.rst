=======
Changes
=======


v0.12.2 (2011-05-05)
====================

- Actors are now registered in :class:`pykka.registry.ActorRegistry` before
  they are started. This fixes a race condition where an actor tried to stop
  and unregister itself before it was registered, causing an exception in
  :meth:`ActorRegistry.unregister`.


v0.12.1 (2011-04-25)
====================

- Stop all running actors on :exc:`BaseException` instead of just
  :exc:`KeyboardInterrupt`, so that ``sys.exit(1)`` will work.


v0.12 (2011-03-30)
==================

- First stable release, as Pykka now is used by the `Mopidy
  <http://www.mopidy.com/>`_ project. From now on, a changelog will be
  maintained and we will strive for backwards compatability.
