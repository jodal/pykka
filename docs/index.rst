=====
Pykka
=====

Pykka is a Python implementation of the `actor model
<https://en.wikipedia.org/wiki/Actor_model>`_. The actor model introduces some
simple rules to control the sharing of state and cooperation between execution
units, which makes it easier to build concurrent applications.

For details and code examples, see the `Pykka documentation
<https://pykka.readthedocs.io/>`_.

Pykka is available from PyPI. To install it, run::

    pip install pykka

Pykka works with Python 3.9 or newer.


Inspiration
===========

Much of the naming of concepts and methods in Pykka is taken from the `Akka
<https://akka.io/>`_ project which implements actors on the JVM. Though, Pykka
does not aim to be a Python port of Akka, and supports far fewer features.

Notably, Pykka **does not** support the following features:

- Supervision: Linking actors, supervisors, or supervisor groups.

- Remoting: Communicating with actors running on other hosts.

- Routers: Pykka does not come with a set of predefined message routers, though
  you may make your own actors for routing messages.


Project resources
=================

- `Documentation <https://pykka.readthedocs.io/>`_
- `Source code <https://github.com/jodal/pykka>`_
- `Releases <https://github.com/jodal/pykka/releases>`_
- `Issue tracker <https://github.com/jodal/pykka/issues>`_
- `Contributors <https://github.com/jodal/pykka/graphs/contributors>`_
- `Users <https://github.com/jodal/pykka/wiki/Users>`_


.. toctree::
    :maxdepth: 2
    :caption: Usage

    quickstart
    examples
    runtimes/index
    testing


.. toctree::
    :maxdepth: 2
    :caption: Reference

    api/module
    api/actors
    api/proxies
    api/futures
    api/registry
    api/exceptions
    api/messages
    api/logging
    api/debug
    api/typing


License
=======

Pykka is copyright 2010-2024 Stein Magnus Jodal and contributors.
Pykka is licensed under the
`Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_.
