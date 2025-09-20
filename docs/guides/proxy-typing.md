# Proxy typing

Since Pykka 4.0, Pykka has complete type hints for the public API, tested using
both [Mypy](https://www.mypy-lang.org/) and
[Pyright](https://github.com/microsoft/pyright).

Due to the dynamic nature of [`ActorProxy`][pykka.ActorProxy] objects,
it is not possible to automatically type them correctly.
The [`pykka.typing` module][pykka.typing] contains helpers
to manually create additional classes that correctly describe
the type hints for the proxy objects.
In cases where a proxy objects is used a lot,
this might be worth the extra effort
to increase development speed and catch bugs earlier.

## Example

```py title="examples/proxy_typing.py"
--8<-- "examples/proxy_typing.py"
```
