# Introduction

Pykka is a Python implementation of the [actor
model](https://en.wikipedia.org/wiki/Actor_model). The actor model
introduces some simple rules to control the sharing of state and
cooperation between execution units, which makes it easier to build
concurrent applications.

## Installation

Pykka has no dependencies other than Python 3.10 or newer.

Pykka is available from [PyPI](https://pypi.org/project/pykka/):

```sh
python3 -m pip install pykka
```

## Inspiration

Pykka was originally created around 2011 as
a formalization of concurrency patterns that emerged in
the [Mopidy music server](https://www.mopidy.com/).
The original Pykka source code wasn't extracted from Mopidy,
but it built and improved on the concepts from Mopidy.
Mopidy was later ported to build on Pykka
instead of its own concurrency abstractions.

Much of the naming of concepts and methods in Pykka was inspired by
[Jonas Bonér](https://jonasboner.com/)'s conference talks around 2010 on Akka,
a JVM implementation of the actor model.
Pykka is not a Python port of Akka, and supports far fewer features.

Notably, Pykka **does not** support the following features:

- Supervision: Linking actors, supervisors, or supervisor groups.
- Remoting: Communicating with actors running on other hosts.
- Routers: Pykka does not come with a set of predefined message
  routers, though you may make your own actors for routing messages.

## Project resources

- [Source code](https://github.com/jodal/pykka)
- [Releases](https://github.com/jodal/pykka/releases)
- [Issue tracker](https://github.com/jodal/pykka/issues)
- [Contributors](https://github.com/jodal/pykka/graphs/contributors)
- [Users](https://github.com/jodal/pykka/wiki/Users)
