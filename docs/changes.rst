=======
Changes
=======

v0.12.1 (2011-04-25)
====================

- Stop all running actors on :exc:`BaseException` instead of just
  :exc:`KeyboardInterrupt`, so that ``sys.exit(1)`` will work.

v0.12 (2011-03-30)
==================

- First stable release, as Pykka now is used by the `Mopidy
  <http://www.mopidy,com/>`_ project. From now on, a changelog will be
  maintained and we will strive for backwards compatability.
