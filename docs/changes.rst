=======
Changes
=======


v0.14 (2012-04-22)
==================

- Add :attr:`pykka.__version__` to conform with :pep:`396`. This deprecates
  :attr:`pykka.VERSION` and :meth:`pykka.get_version`.

- Add :meth:`ActorRef.tell() <pykka.actor.ActorRef.tell>` method in favor of now
  deprecated :meth:`ActorRef.send_one_way() <pykka.actor.ActorRef.send_one_way>`.

- Add :meth:`ActorRef.ask() <pykka.actor.ActorRef.ask>` method in favor of now
  deprecated :meth:`ActorRef.send_request_reply()
  <pykka.actor.ActorRef.send_request_reply>`.

- :class:`ThreadingFuture.set() <pykka.future.ThreadingFuture>` no longer makes
  a copy of the object set on the future. The setter is urged to either only
  pass immutable objects through futures or copy the object himself before
  setting it on the future. This is a less safe default, but it removes
  unecessary overhead in speed and memory usage for users of immutable data
  structures. For example, the `Mopidy <http://www.mopidy.com>`_ test suite of
  about 1000 tests, many which are using Pykka, is still passing after this
  change, but the test suite runs approximately 20% faster.


v0.13 (2011-09-24)
==================

- 10x speedup of traversible attribute access by reusing proxies.

- 1.1x speedup of callable attribute access by reusing proxies.


v0.12.4 (2011-07-30)
====================

- Change and document order in which
  :meth:`pykka.registry.ActorRegistry.stop_all` stops actors. The new order is
  the reverse of the order the actors were started in. This should make
  ``stop_all`` work for programs with simple dependency graphs in between the
  actors. For applications with more complex dependency graphs, the developer
  still needs to pay attention to the shutdown sequence. (Fixes: :issue:`8`)


v0.12.3 (2011-06-25)
====================

- If an actor that was stopped from :meth:`pykka.actor.Actor.on_start`, it
  would unregister properly, but start the receive loop and forever block on
  receiving incoming messages that would never arrive. This left the thread
  alive and isolated, ultimately blocking clean shutdown of the program. The
  fix ensures that the receive loop is never executed if the actor is stopped
  before the receive loop is started.

- Set the thread name of any :class:`pykka.actor.ThreadingActor` to
  ``PykkaActorThread-N`` instead of the default ``Thread-N``. This eases
  debugging by clearly labeling actor threads in e.g. the output of
  :func:`threading.enumerate`.

- Add utility method :meth:`pykka.registry.ActorRegistry.broadcast` which
  broadcasts a message to all registered actors or to a given class of
  registred actors. (Fixes: :issue:`7`)

- Allow multiple calls to :meth:`pykka.registry.ActorRegistry.unregister`
  with the same :class:`pykka.actor.ActorRef` as argument without throwing a
  :exc:`ValueError`. (Fixes: :issue:`5`)

- Make the :class:`pykka.proxy.ActorProxy`'s reference to its
  :class:`pykka.actor.ActorRef` public as
  :attr:`pykka.proxy.ActorProxy.actor_ref`. The ``ActorRef`` instance was
  already exposed as a public field by the actor itself using the same name,
  but making it public directly on the proxy makes it possible to do e.g.
  ``proxy.actor_ref.is_alive()`` without waiting for a potentially dead actor
  to return an ``ActorRef`` instance you can use. (Fixes: :issue:`3`)


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
