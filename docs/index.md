# Introduction

Pykka is a Python implementation of the [actor
model](https://en.wikipedia.org/wiki/Actor_model). The actor model
introduces some simple rules to control the sharing of state and
cooperation between execution units, which makes it easier to build
concurrent applications.

For details and code examples, see the [Pykka
documentation](https://pykka.readthedocs.io/).

Pykka is available from PyPI. To install it, run:

```sh
pip install pykka
```

Pykka works with Python 3.10 or newer.

## Inspiration

Much of the naming of concepts and methods in Pykka is taken from the
[Akka](https://akka.io/) project which implements actors on the JVM.
Though, Pykka does not aim to be a Python port of Akka, and supports far
fewer features.

Notably, Pykka **does not** support the following features:

- Supervision: Linking actors, supervisors, or supervisor groups.
- Remoting: Communicating with actors running on other hosts.
- Routers: Pykka does not come with a set of predefined message
  routers, though you may make your own actors for routing messages.

## Project resources

- [Documentation](https://pykka.readthedocs.io/)
- [Source code](https://github.com/jodal/pykka)
- [Releases](https://github.com/jodal/pykka/releases)
- [Issue tracker](https://github.com/jodal/pykka/issues)
- [Contributors](https://github.com/jodal/pykka/graphs/contributors)
- [Users](https://github.com/jodal/pykka/wiki/Users)

## License

Pykka is copyright 2010-2025 Stein Magnus Jodal and contributors. Pykka
is licensed under the [Apache License, Version
2.0](https://www.apache.org/licenses/LICENSE-2.0).
