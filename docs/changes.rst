=======
Changes
=======


v2.0.3 (2020-11-27)
===================

- Mark eventlet and gevent support as deprecated. The support will be removed
  in Pykka 3.0.

  These where somewhat interesting ways to implement
  concurrency in Python when Pykka was conceived in 2011. Today, it is
  unclear it these libraries still have any mindshare or if keeping the
  support for them just adds an unecessary burden to Pykka's maintenance.

- Include Python 3.9 in the test matrix. (PR: :issue:`98`)

- Add missing :class:`None` default value for the ``timeout`` keyword argument to
  :meth:`~pykka.eventlet.EventletEvent.wait`, so that it matches the
  :class:`~threading.Event` API.
  (PR: :issue:`91`)


v2.0.2 (2019-12-02)
===================

Bugfix release.

- Fix test suite run with pytest-mocker >= 1.11.2. (Fixes: :issue:`85`)


v2.0.1 (2019-10-10)
===================

Bugfix release.

- Make :class:`~pykka.ActorRef` hashable.


v2.0.0 (2019-05-07)
===================

Major feature release.

Dependencies
------------

- Drop support for Python 2.6, 3.2, 3.3, and 3.4. All have reached their end of
  life and do no longer receive security updates.

- Include CPython 3.5, 3.6, 3.7, and 3.8 pre-releases, and PyPy 3.5 in the test
  matrix.

- Include gevent and Eventlet tests in all environments. Since Pykka was
  originally developed, both has grown support for Python 3 and PyPy.

- On Python 3, import :class:`Callable` and :class:`Iterable` from
  :mod:`collections.abc` instead of :mod:`collections`. This fixes a
  deprecation warning on Python 3.7 and prepares for Python 3.8.

Actors
------

- Actor messages are no longer required to be ``dict`` objects. Any object type
  can be used as an actor message. (Fixes: :issue:`39`, :issue:`45`, PR:
  :issue:`79`)

  For existing code, this means that :meth:`~pykka.Actor.on_receive`
  implementations should no longer assume the received message to be a
  ``dict``, and guard with the appropriate amount of :func:`isinstance`
  checks. As an existing application will not observe any new message types
  before it starts using them itself, this is not marked as backwards
  incompatible.

Proxies
-------

- **Backwards incompatible:** Avoid accessing actor properties when creating
  a proxy for the actor. For properties with side effects, this is a major bug
  fix. For properties which does heavy work, this is a major startup
  performance improvement.

  This is backwards incompatible if you in a property getter returned an
  object instance with the ``pykka_traversable`` marker. Previously, this
  would work just like a traversable attribute. Now, the property always
  returns a future with the property getter's return value.

- Fix infinite recursion when creating a proxy for an actor with an attribute
  or method replaced with a :class:`~unittest.mock.Mock` without a ``spec``
  defined. (Fixes: :issue:`26`, :issue:`27`)

- Fix infinite recursion when creating a proxy for an actor with an attribute
  that was itself a proxy to the same actor. The attribute will now be ignored
  and a warning log message will ask you to consider making the self-proxy
  private. (Fixes: :issue:`48`)

- Add :meth:`~pykka.CallableProxy.defer` to support method calls through a
  proxy with :meth:`~pykka.ActorRef.tell` semantics. (Contributed by Andrey
  Gubarev. Fixes: :issue:`63`. PR: :issue:`72`)

- Add :func:`~pykka.traversable` for marking an actor's attributes as
  traversable when used through actor proxies. The old way of manually adding
  a ``pykka_traversable`` attribute to the object to be traversed still works,
  but the new function is recommended as it provides protection against typos
  in the marker name, and keeps the traversable marking in the actor class
  itself. (PR: :issue:`81`)

Futures
-------

- **Backwards incompatible:** :meth:`pykka.Future.set_exception` no longer
  accepts an exception instance, which was deprecated in 0.15. The method can
  be called with either an ``exc_info`` tuple or :class:`None`, in which case
  it will use :func:`sys.exc_info` to get information on the current exception.

- **Backwards incompatible:** :meth:`pykka.Future.map` on a future with an
  iterable result no longer applies the map function to each item in iterable.
  Instead, the entire future result is passed to the map function. (Fixes:
  :issue:`64`)

  To upgrade existing code, make sure to explicitly apply the core of your map
  function to each item in the iterable::

      >>> f = pykka.ThreadingFuture()
      >>> f.set([1, 2, 3])
      >>> f.map(lambda x: x + 1).get()  # Pykka < 2.0
      [2, 3, 4]
      >>> f.map(lambda x: [i + 1 for i in x]).get()  # Pykka >= 2.0
      [2, 3, 4]

  This change makes it easy to use :meth:`~pykka.Future.map` to extract a field
  from a future that returns a dict::

      >>> f = pykka.ThreadingFuture()
      >>> f.set({'foo': 'bar'})
      >>> f.map(lambda x: x['foo']).get()
      'bar'

  Because dict is an iterable, the now removed special handling of iterables
  made this pattern difficult to use.

- Reuse result from :meth:`pykka.Future.filter`, :meth:`pykka.Future.map`, and
  :meth:`pykka.Future.reduce`. Recalculating the result on each call to
  :meth:`pykka.Future.get` is both inconsistent with regular futures and can
  cause problems if the function is expensive or has side effects. (Fixes:
  :issue:`32`)

- If using Python 3.5+, one can now use the ``await`` keyword to get the
  result from a future. (Contributed by Joshua Doncaster-Marsiglio. PR:
  :issue:`78`)

Logging
-------

- Pykka's use of different log levels has been :ref:`documented <logging>`.

- Exceptions raised by an actor that are captured into a reply future are now
  logged on the :attr:`~logging.INFO` level instead of the
  :attr:`~logging.DEBUG` level. This makes it possible to detect potentially
  unhandled exceptions during development without having to turn on debug
  logging, which can have a low signal to noise ratio. (Contributed by Stefan
  Möhl. Fixes: :issue:`73`)

Gevent support
--------------

- Ensure that the original traceback is preserved when an exception is returned
  through a future from a Gevent actor. (Contributed by Arne Brutschy. Fixes:
  :issue:`74`, PR: :issue:`75`)

Internals
---------

- **Backwards incompatible:** Prefix all internal modules with ``_``. This is
  backwards incompatible if you have imported objects from other import paths
  than what is used in the documentation.

- Port tests to pytest.

- Format code with Black.

- Change internal messaging format from ``dict`` to ``namedtuple``. (PR:
  :issue:`80`)


v1.2.1 (2015-07-20)
===================

- Increase log level of :func:`pykka.debug.log_thread_tracebacks` debugging
  helper from :attr:`logging.INFO` to :attr:`logging.CRITICAL`.

- Fix errors in docs examples. (PR: :issue:`29`, :issue:`43`)

- Fix typos in docs.

- Various project setup and development improvements.


v1.2.0 (2013-07-15)
===================

- Enforce that multiple calls to :meth:`pykka.Future.set` raises an exception.
  This was already the case for some implementations. The exception raised is
  not specified.

- Add :meth:`pykka.Future.set_get_hook`.

- Add :meth:`~Pykka.Future.filter`, :meth:`~pykka.Future.join`,
  :meth:`~pykka.Future.map`, and :meth:`~pykka.Future.reduce` as convenience
  methods using the new :meth:`~pykka.Future.set_get_hook` method.

- Add support for running actors based on eventlet greenlets. See
  :mod:`pykka.eventlet` for details. Thanks to Jakub Stasiak for the
  implementation.

- Update documentation to reflect that the ``reply_to`` field on the message is
  private to Pykka. Actors should reply to messages simply by returning the
  response from :meth:`~pykka.Actor.on_receive`. The internal field is renamed
  to ``pykka_reply_to`` a to avoid collisions with other message fields. It is
  also removed from the message before the message is passed to
  :meth:`~pykka.Actor.on_receive`. Thanks to Jakub Stasiak.

- When messages are left in the actor inbox after the actor is stopped, those
  messages that are expecting a reply is now rejected by replying with an
  :exc:`~pykka.ActorDeadError` exception.  This causes other actors blocking on
  the returned :class:`~pykka.Future` without a timeout to raise the exception
  instead of waiting forever. Thanks to Jakub Stasiak.

  This makes the behavior of messaging an actor around the time it is stopped
  more consistent:

  - Messaging an already dead actor immediately raises
    :exc:`~pykka.ActorDeadError`.

  - Messaging an alive actor that is stopped before it processes the message
    will cause the reply future to raise :exc:`~pykka.ActorDeadError`.

  Similarly, if you ask an actor to stop multiple times, and block on the
  responses, all the messages will now get an reply. Previously only the first
  message got a reply, potentially making the application wait forever on
  replies to the subsequent stop messages.

- When :meth:`~pykka.ActorRef.ask` is used to asynchronously message a dead
  actor (e.g. ``block`` set to :class:`False`), it will no longer immediately
  raise :exc:`~pykka.ActorDeadError`. Instead, it will return a future and
  fail the future with the :exc:`~pykka.ActorDeadError` exception. This makes
  the interface more consistent, as you'll have one instead of two ways the
  call can raise exceptions under normal conditions. If
  :meth:`~pykka.ActorRef.ask` is called synchronously (e.g. ``block`` set to
  :class:`True`), the behavior is unchanged.

- A change to :meth:`~pykka.ActorRef.stop` reduces the likelyhood of a race
  condition when asking an actor to stop multiple times by not checking if the
  actor is dead before asking it to stop, but instead just go ahead and leave
  it to :meth:`~pykka.ActorRef.tell` to do the alive-or-dead check a single
  time, and as late as possible.

- Change :meth:`~pykka.ActorRef.is_alive` to check the actor's runnable flag
  instead of checking if the actor is registered in the actor registry.


v1.1.0 (2013-01-19)
===================

- An exception raised in :meth:`pykka.Actor.on_start` didn't stop the actor
  properly. Thanks to Jay Camp for finding and fixing the bug.

- Make sure exceptions in :meth:`pykka.Actor.on_stop` and
  :meth:`pykka.Actor.on_failure` is logged.

- Add :attr:`pykka.ThreadingActor.use_daemon_thread` flag for optionally
  running an actor on a daemon thread, so that it doesn't block the Python
  program from exiting. (Fixes: :issue:`14`)

- Add :func:`pykka.debug.log_thread_tracebacks` debugging helper. (Fixes:
  :issue:`17`)


v1.0.1 (2012-12-12)
===================

- Name the threads of :class:`pykka.ThreadingActor` after the actor class name
  instead of "PykkaThreadingActor-N" to ease debugging. (Fixes: :issue:`12`)


v1.0.0 (2012-10-26)
===================

- **Backwards incompatible:** Removed :attr:`pykka.VERSION` and
  :func:`pykka.get_version`, which have been deprecated since v0.14. Use
  :attr:`pykka.__version__` instead.

- **Backwards incompatible:** Removed :meth:`pykka.ActorRef.send_one_way` and
  :meth:`pykka.ActorRef.send_request_reply`, which have been deprecated since
  v0.14. Use :meth:`pykka.ActorRef.tell` and :meth:`pykka.ActorRef.ask`
  instead.

- **Backwards incompatible:** Actors no longer subclass
  :class:`threading.Thread` or :class:`gevent.Greenlet`. Instead they *have* a
  thread or greenlet that executes the actor's main loop.

  This is backwards incompatible because you no longer have access to
  fields/methods of the thread/greenlet that runs the actor through
  fields/methods on the actor itself. This was never advertised in Pykka's docs
  or examples, but the fields/methods have always been available.

  As a positive side effect, this fixes an issue on Python 3.x, that was
  introduced in Pykka 0.16, where :class:`pykka.ThreadingActor` would
  accidentally override the method :meth:`threading.Thread._stop`.

- **Backwards incompatible:** Actors that override :meth:`__init__()
  <pykka.Actor.__init__>` *must* call the method they override. If not, the
  actor will no longer be properly initialized. Valid ways to call the
  overridden :meth:`__init__` method include::

      super().__init__()
      # or
      pykka.ThreadingActor.__init__()
      # or
      pykka.gevent.GeventActor.__init__()

- Make :meth:`pykka.Actor.__init__` accept any arguments and
  keyword arguments by default. This allows you to use :func:`super` in
  :meth:`__init__` like this::

      super().__init__(1, 2, 3, foo='bar')

  Without this fix, the above use of :func:`super` would cause an exception
  because the default implementation of :meth:`__init__` in
  :class:`pykka.Actor` would not accept the arguments.

- Allow all public classes and functions to be imported directly from the
  :mod:`pykka` module. E.g. ``from pykka.actor import ThreadingActor`` can now
  be written as ``from pykka import ThreadingActor``. The exception is
  :mod:`pykka.gevent`, which still needs to be imported from its own package
  due to its additional dependency on gevent.


v0.16 (2012-09-19)
==================

- Let actors access themselves through a proxy. See the
  :class:`pykka.ActorProxy` documentation for use cases and usage examples.
  (Fixes: :issue:`9`)

- Give proxies direct access to the actor instances for inspecting available
  attributes. This access is only used for reading, and works since both
  threading and gevent based actors share memory with other actors. This
  reduces the creation cost for proxies, which is mostly visible in test suites
  that are starting and stopping lots of actors. For the Mopidy test suite the
  run time was reduced by about 33%. This change also makes self-proxying
  possible.

- Fix bug where :meth:`pykka.Actor.stop` called by an actor on itself did not
  process the remaining messages in the inbox before the actor stopped. The
  behavior now matches the documentation.


v0.15 (2012-08-11)
==================

- Change the argument of :meth:`pykka.Future.set_exception` from an exception
  instance to a ``exc_info`` three-tuple. Passing just an exception instance to
  the method still works, but it is deprecated and may be unsupported in a
  future release.

- Due to the above change, :meth:`pykka.Future.get` will now reraise exceptions
  with complete traceback from the point when the exception was first raised,
  and not just a traceback from when it was reraised by :meth:`get`. (Fixes:
  :issue:`10`)


v0.14 (2012-04-22)
==================

- Add :attr:`pykka.__version__` to conform with :pep:`396`. This deprecates
  :attr:`pykka.VERSION` and :meth:`pykka.get_version`.

- Add :meth:`pykka.ActorRef.tell` method in favor of now deprecated
  :meth:`pykka.ActorRef.send_one_way`.

- Add :meth:`pykka.ActorRef.ask` method in favor of now deprecated
  :meth:`pykka.ActorRef.send_request_reply`.

- :class:`ThreadingFuture.set() <pykka.ThreadingFuture>` no longer makes
  a copy of the object set on the future. The setter is urged to either only
  pass immutable objects through futures or copy the object himself before
  setting it on the future. This is a less safe default, but it removes
  unecessary overhead in speed and memory usage for users of immutable data
  structures. For example, the Mopidy test suite of about 1000 tests, many
  which are using Pykka, is still passing after this change, but the test suite
  runs approximately 20% faster.


v0.13 (2011-09-24)
==================

- 10x speedup of traversable attribute access by reusing proxies.

- 1.1x speedup of callable attribute access by reusing proxies.


v0.12.4 (2011-07-30)
====================

- Change and document order in which :meth:`pykka.ActorRegistry.stop_all` stops
  actors. The new order is the reverse of the order the actors were started in.
  This should make ``stop_all`` work for programs with simple dependency graphs
  in between the actors. For applications with more complex dependency graphs,
  the developer still needs to pay attention to the shutdown sequence. (Fixes:
  :issue:`8`)


v0.12.3 (2011-06-25)
====================

- If an actor that was stopped from :meth:`pykka.Actor.on_start`, it would
  unregister properly, but start the receive loop and forever block on
  receiving incoming messages that would never arrive. This left the thread
  alive and isolated, ultimately blocking clean shutdown of the program. The
  fix ensures that the receive loop is never executed if the actor is stopped
  before the receive loop is started.

- Set the thread name of any :class:`pykka.ThreadingActor` to
  ``PykkaActorThread-N`` instead of the default ``Thread-N``. This eases
  debugging by clearly labeling actor threads in e.g. the output of
  :func:`threading.enumerate`.

- Add utility method :meth:`pykka.ActorRegistry.broadcast` which broadcasts a
  message to all registered actors or to a given class of registred actors.
  (Fixes: :issue:`7`)

- Allow multiple calls to :meth:`pykka.ActorRegistry.unregister` with the same
  :class:`pykka.actor.ActorRef` as argument without throwing a
  :exc:`ValueError`. (Fixes: :issue:`5`)

- Make the :class:`pykka.ActorProxy`'s reference to its :class:`pykka.ActorRef`
  public as :attr:`pykka.ActorProxy.actor_ref`. The ``ActorRef`` instance was
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
  <https://www.mopidy.com/>`_ project. From now on, a changelog will be
  maintained and we will strive for backwards compatibility.
