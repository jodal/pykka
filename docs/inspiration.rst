===========
Inspiration
===========

Much of the naming of concepts and methods in Pykka is taken from the `Akka
<https://akka.io/>`_ project which implements actors on the JVM. Though, Pykka
does not aim to be a Python port of Akka, and supports far fewer features.

What Pykka is not
=================

Notably, Pykka **does not** support the following features:

- Supervision: Linking actors, supervisors, or supervisor groups.

- Remoting: Communicating with actors running on other hosts.

- Routers: Pykka does not come with a set of predefined message routers, though
  you may make your own actors for routing messages.
