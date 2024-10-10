from __future__ import annotations

import logging
import threading
import time
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

import pytest

from pykka import ActorRegistry, ThreadingActor, ThreadingFuture
from tests.log_handler import PykkaTestLogHandler
from tests.types import Events, Runtime

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pykka import Actor, Future


RUNTIMES = {
    "threading": pytest.param(
        Runtime(
            name="threading",
            actor_class=ThreadingActor,
            event_class=threading.Event,
            future_class=ThreadingFuture,
            sleep_func=time.sleep,
        ),
        id="threading",
    )
}


@pytest.fixture(scope="session", params=RUNTIMES.values())
def runtime(request: pytest.FixtureRequest) -> Runtime:
    return cast(Runtime, request.param)


@pytest.fixture()
def _stop_all() -> Iterator[None]:  # pyright: ignore[reportUnusedFunction]
    yield
    ActorRegistry.stop_all()


@pytest.fixture()
def log_handler() -> Iterator[logging.Handler]:
    log_handler = PykkaTestLogHandler()

    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    # pytest sets the root logger level to WARNING. We reset it to NOTSET
    # so that all log messages reaches our log handler.
    root_logger.setLevel(logging.NOTSET)

    yield log_handler

    log_handler.close()


@pytest.fixture()
def events(runtime: Runtime) -> Events:
    return Events(
        on_start_was_called=runtime.event_class(),
        on_stop_was_called=runtime.event_class(),
        on_failure_was_called=runtime.event_class(),
        greetings_was_received=runtime.event_class(),
        actor_registered_before_on_start_was_called=runtime.event_class(),
    )


@pytest.fixture(scope="module")
def early_failing_actor_class(runtime: Runtime) -> type[Actor]:
    class EarlyFailingActor(runtime.actor_class):  # type: ignore[name-defined]
        def __init__(self, events: Events) -> None:
            super().__init__()
            self.events = events

        def on_start(self) -> None:
            try:
                raise RuntimeError("on_start failure")
            finally:
                self.events.on_start_was_called.set()

    return EarlyFailingActor


@pytest.fixture(scope="module")
def late_failing_actor_class(runtime: Runtime) -> type[Actor]:
    class LateFailingActor(runtime.actor_class):  # type: ignore[name-defined]
        def __init__(self, events: Events) -> None:
            super().__init__()
            self.events = events

        def on_start(self) -> None:
            self.stop()

        def on_stop(self) -> None:
            try:
                raise RuntimeError("on_stop failure")
            finally:
                self.events.on_stop_was_called.set()

    return LateFailingActor


@pytest.fixture(scope="module")
def failing_on_failure_actor_class(runtime: Runtime) -> type[Actor]:
    class FailingOnFailureActor(runtime.actor_class):  # type: ignore[name-defined]
        def __init__(self, events: Events) -> None:
            super().__init__()
            self.events = events

        def on_receive(self, message: Any) -> Any:
            if message.get("command") == "raise exception":
                raise Exception("on_receive failure")
            return super().on_receive(message)

        def on_failure(self, *args: Any) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
            try:
                raise RuntimeError("on_failure failure")
            finally:
                self.events.on_failure_was_called.set()

    return FailingOnFailureActor


@pytest.fixture()
def future(runtime: Runtime) -> Future[Any]:
    return runtime.future_class()


@pytest.fixture()
def futures(runtime: Runtime) -> list[Future[Any]]:
    return [runtime.future_class() for _ in range(3)]
