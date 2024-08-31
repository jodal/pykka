from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, AsyncGenerator, NoReturn, Optional

import pytest

from pykka.asyncio import Actor
from tests.log_handler import LogLevel, PykkaTestLogHandler

if TYPE_CHECKING:
    from types import TracebackType

    from pykka.asyncio import ActorRef
    from tests.asyncio.types import Events, Runtime

pytestmark = pytest.mark.usefixtures("_stop_all")


class LoggingActor(Actor):
    def __init__(self, events: Events) -> None:
        super().__init__()
        self.events = events

    async def on_stop(self) -> None:
        self.events.on_stop_was_called.set()

    async def on_failure(
        self,
        exception_type: Optional[type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.events.on_failure_was_called.set()

    async def on_receive(self, message: Any) -> Any:
        if message.get("command") == "raise exception":
            return self.raise_exception()
        if message.get("command") == "raise base exception":
            raise BaseException
        return await super().on_receive(message)

    def raise_exception(self) -> NoReturn:
        raise Exception("foo")


@pytest.fixture(scope="module")
def actor_class(runtime: Runtime) -> type[LoggingActor]:
    class LoggingActorImpl(LoggingActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return LoggingActorImpl


@pytest.fixture()
async def actor_ref(
    actor_class: type[LoggingActor],
    events: Events,
) -> AsyncGenerator[ActorRef[LoggingActor]]:
    ref = actor_class.start(events)
    yield ref
    await ref.stop()


def test_null_handler_is_added_to_avoid_warnings() -> None:
    logger = logging.getLogger("pykka")
    handler_names = [h.__class__.__name__ for h in logger.handlers]

    assert "NullHandler" in handler_names


async def test_unexpected_messages_are_logged(
    actor_ref: ActorRef[LoggingActor],
    log_handler: PykkaTestLogHandler,
) -> None:
    await actor_ref.ask({"unhandled": "message"})

    log_handler.wait_for_message(LogLevel.WARNING)
    with log_handler.lock:
        assert len(log_handler.messages[LogLevel.WARNING]) == 1
        log_record = log_handler.messages[LogLevel.WARNING][0]

    assert log_record.getMessage().split(": ")[0] == (
        f"Unexpected message received by {actor_ref}"
    )


async def test_exception_is_logged_when_returned_to_caller(
    actor_ref: ActorRef[LoggingActor],
    log_handler: PykkaTestLogHandler,
) -> None:
    with pytest.raises(Exception, match="foo"):
        await actor_ref.proxy().raise_exception()

    log_handler.wait_for_message(LogLevel.INFO)
    with log_handler.lock:
        assert len(log_handler.messages[LogLevel.INFO]) == 1
        log_record = log_handler.messages[LogLevel.INFO][0]

    assert log_record.getMessage() == (
        f"Exception returned from {actor_ref} to caller:"
    )
    assert log_record.exc_info
    assert log_record.exc_info[0] is Exception
    assert str(log_record.exc_info[1]) == "foo"


async def test_exception_is_logged_when_not_reply_requested(
    actor_ref: ActorRef[LoggingActor],
    events: Events,
    log_handler: PykkaTestLogHandler,
) -> None:
    events.on_failure_was_called.clear()
    actor_ref.tell({"command": "raise exception"})

    await events.on_failure_was_called.wait(5)
    assert events.on_failure_was_called.is_set()

    log_handler.wait_for_message(LogLevel.ERROR)
    with log_handler.lock:
        assert len(log_handler.messages[LogLevel.ERROR]) == 1
        log_record = log_handler.messages[LogLevel.ERROR][0]

    assert log_record.getMessage() == f"Unhandled exception in {actor_ref}:"
    assert log_record.exc_info
    assert log_record.exc_info[0] is Exception
    assert str(log_record.exc_info[1]) == "foo"


async def test_base_exception_is_logged(
    actor_ref: ActorRef[LoggingActor],
    events: Events,
    log_handler: PykkaTestLogHandler,
) -> None:
    log_handler.reset()
    events.on_stop_was_called.clear()
    actor_ref.tell({"command": "raise base exception"})

    await events.on_stop_was_called.wait(5)
    assert events.on_stop_was_called.is_set()

    log_handler.wait_for_message(LogLevel.DEBUG, num_messages=3)
    with log_handler.lock:
        assert len(log_handler.messages[LogLevel.DEBUG]) == 3
        log_record = log_handler.messages[LogLevel.DEBUG][0]

    assert log_record.getMessage() == (
        f"BaseException() in {actor_ref}. Stopping all actors."
    )


async def test_exception_in_on_start_is_logged(
    early_failing_actor_class: type[LoggingActor],
    events: Events,
    log_handler: PykkaTestLogHandler,
) -> None:
    log_handler.reset()
    actor_ref = early_failing_actor_class.start(events)
    await events.on_start_was_called.wait(5)

    log_handler.wait_for_message(LogLevel.ERROR)
    with log_handler.lock:
        assert len(log_handler.messages[LogLevel.ERROR]) == 1
        log_record = log_handler.messages[LogLevel.ERROR][0]

    assert log_record.getMessage() == f"Unhandled exception in {actor_ref}:"


async def test_exception_in_on_stop_is_logged(
    late_failing_actor_class: type[LoggingActor],
    events: Events,
    log_handler: PykkaTestLogHandler,
) -> None:
    log_handler.reset()
    actor_ref = late_failing_actor_class.start(events)
    await events.on_stop_was_called.wait(5)

    log_handler.wait_for_message(LogLevel.ERROR)
    with log_handler.lock:
        assert len(log_handler.messages[LogLevel.ERROR]) == 1
        log_record = log_handler.messages[LogLevel.ERROR][0]

    assert log_record.getMessage() == f"Unhandled exception in {actor_ref}:"


async def test_exception_in_on_failure_is_logged(
    failing_on_failure_actor_class: type[LoggingActor],
    events: Events,
    log_handler: PykkaTestLogHandler,
) -> None:
    log_handler.reset()
    actor_ref = failing_on_failure_actor_class.start(events)
    actor_ref.tell({"command": "raise exception"})
    await events.on_failure_was_called.wait(5)

    log_handler.wait_for_message(LogLevel.ERROR, num_messages=2)
    with log_handler.lock:
        assert len(log_handler.messages[LogLevel.ERROR]) == 2
        log_record = log_handler.messages[LogLevel.ERROR][0]

    assert log_record.getMessage() == f"Unhandled exception in {actor_ref}:"
