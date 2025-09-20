# Introduction

Pykka is a Python implementation of the [actor model](getting-started/model.md).
The actor model introduces some simple rules to control the sharing of state and
cooperation between execution units, which makes it easier to build concurrent
applications.

## Installation

Pykka has no dependencies other than Python 3.10 or newer.
It can be installed from [PyPI](https://pypi.org/project/pykka/),
e.g. with `uv`:

```console
$ uv add pykka
```

Next up, check out the [Getting started](getting-started/index.md) docs or the
[Reference](reference/index.md).

## Project resources

- [Source code](https://github.com/jodal/pykka)
- [Releases](https://github.com/jodal/pykka/releases)
- [Issue tracker](https://github.com/jodal/pykka/issues)
- [Contributors](https://github.com/jodal/pykka/graphs/contributors)
- [Users](https://github.com/jodal/pykka/wiki/Users)

## History and inspiration

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
