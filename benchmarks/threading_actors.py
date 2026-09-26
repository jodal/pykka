"""Benchmark of Pykka's threading actors.

See `README.md` in this directory for how to run the benchmark.

A release is blocked if the mean of `ask` or one of the proxy cases is more
than 10% slower than the last release. The means of these cases repeat
within 0.5% between runs.

`tell` and `start_stop` are only reported. The mean of `tell` changes by up
to 13% between runs, and `start_stop` mostly measures how fast the kernel
makes and joins a thread.
"""

from __future__ import annotations

import importlib.metadata
import time
from typing import TYPE_CHECKING, Any

from pykka import ThreadingActor

if TYPE_CHECKING:
    from collections.abc import Callable


class SomeObject:
    pykka_traversable = False
    cat = "bar.cat"

    def func(self) -> None:
        pass


class AnActor(ThreadingActor):
    bar = SomeObject()
    bar.pykka_traversable = True

    foo = "foo"

    def func(self) -> None:
        pass

    def on_receive(self, message: Any) -> Any:
        return message


def bench_tell(loops: int) -> float:
    ref = AnActor.start()
    start = time.perf_counter()
    for _ in range(loops):
        ref.tell("ping")
    ref.ask("ping")  # Wait until the actor has handled all messages.
    elapsed = time.perf_counter() - start
    ref.stop()
    return elapsed


def bench_ask(loops: int) -> float:
    ref = AnActor.start()
    start = time.perf_counter()
    for _ in range(loops):
        ref.ask("ping")
    elapsed = time.perf_counter() - start
    ref.stop()
    return elapsed


def bench_proxy_call(loops: int) -> float:
    ref = AnActor.start()
    proxy = ref.proxy()
    start = time.perf_counter()
    for _ in range(loops):
        proxy.func().get()
    elapsed = time.perf_counter() - start
    ref.stop()
    return elapsed


def bench_proxy_attr(loops: int) -> float:
    ref = AnActor.start()
    proxy = ref.proxy()
    start = time.perf_counter()
    for _ in range(loops):
        proxy.foo.get()
    elapsed = time.perf_counter() - start
    ref.stop()
    return elapsed


def bench_proxy_traversable_call(loops: int) -> float:
    ref = AnActor.start()
    proxy = ref.proxy()
    start = time.perf_counter()
    for _ in range(loops):
        proxy.bar.func().get()
    elapsed = time.perf_counter() - start
    ref.stop()
    return elapsed


def bench_proxy_traversable_attr(loops: int) -> float:
    ref = AnActor.start()
    proxy = ref.proxy()
    start = time.perf_counter()
    for _ in range(loops):
        proxy.bar.cat.get()
    elapsed = time.perf_counter() - start
    ref.stop()
    return elapsed


def bench_start_stop(loops: int) -> float:
    start = time.perf_counter()
    for _ in range(loops):
        AnActor.start().stop()
    return time.perf_counter() - start


BENCHMARKS: dict[str, Callable[[int], float]] = {
    "tell": bench_tell,
    "ask": bench_ask,
    "proxy_call": bench_proxy_call,
    "proxy_attr": bench_proxy_attr,
    "proxy_traversable_call": bench_proxy_traversable_call,
    "proxy_traversable_attr": bench_proxy_traversable_attr,
    "start_stop": bench_start_stop,
}


def main() -> None:
    import pyperf  # noqa: PLC0415  # pyright: ignore[reportMissingTypeStubs]

    runner: Any = pyperf.Runner()
    runner.metadata["pykka_version"] = importlib.metadata.version("pykka")
    for name, func in BENCHMARKS.items():
        runner.bench_time_func(name, func)


if __name__ == "__main__":
    main()
