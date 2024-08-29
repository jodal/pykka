from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Iterator

import pytest

from pykka.asyncio import AsyncioActor

if TYPE_CHECKING:
    from pykka.asyncio import ActorRef


@pytest.fixture()
async def actor_ref() -> Iterator[ActorRef[AsyncioActor]]:
    ref = await AsyncioActor.start()
    yield ref
    await ref.stop()


async def test_asyncio_actor_is_named_after_pykka_actor_class(
    actor_ref: ActorRef[AsyncioActor],
) -> None:
    tasks = asyncio.all_tasks()
    task_names = [t.get_name() for t in tasks]
    named_correctly = [
        name.startswith(AsyncioActor.__name__) for name in task_names
    ]

    assert any(named_correctly)
