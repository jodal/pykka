# Futures

Calling `ThreadingFuture.set_get_hook()` wakes threads already waiting in
`get()`. A hook installed during a waiting call receives that call's remaining
timeout.

::: pykka.Future

::: pykka.get_all
