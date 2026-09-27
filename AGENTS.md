# AGENTS.md

Guidance for coding agents that work in this repo.

Pykka is a Python implementation of the actor model. It supports Python 3.10
and newer, and has no runtime dependencies.

## Layout

- `src/pykka/`: the library
- `tests/`: the pytest suite
- `benchmarks/`: pyperf benchmarks, see `benchmarks/README.md`
- `examples/`: runnable examples
- `docs/`: the MkDocs site

## Checks

CI runs each check as a tox env. Run them with uv:

```sh
uv run tox -e 3.14                          # pytest on Python 3.14
uv run tox -e 3.14 -- tests/test_actor.py   # one test file
uv run tox -e mypy
uv run tox -e pyright
uv run tox -e ty
uv run tox -e ruff-format
uv run tox -e ruff-check
uv run tox -e docs
uv run tox -e zizmor
```

## Rules

- Keep the public API stable. Do not change or remove public names or
  behavior unless you are asked to. Mopidy and other projects use Pykka, and
  Debian and other distributions package it.
- Do not add runtime dependencies.
- mypy, basedpyright, and ty run in strict mode. Add precise type
  annotations.
- Add or change tests for each change in behavior.
- Update `docs/` and `examples/` when behavior that users see changes.
- Use Conventional Commits for commit messages.
