from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Awaitable, Literal, Optional, overload

if TYPE_CHECKING:
    __all__ = ["AsyncioEvent"]

class AsyncioEvent(asyncio.Event):
    """Same as asyncio.Event but adds a `wait` with timeout.
    """

    @overload
    async def wait(self) -> Literal[True]: ...

    @overload
    async def wait(self, timeout: Optional[float]) -> bool: ...

    async def wait(self, timeout: Optional[float] = None) -> bool:
        try:
            await asyncio.wait_for(super().wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
