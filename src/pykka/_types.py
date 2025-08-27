from __future__ import annotations

from types import TracebackType
from typing import TypeAlias

AttrPath: TypeAlias = tuple[str, ...]


# OptExcInfo matches the return type of sys.exc_info() in typeshed
OptExcInfo = tuple[
    type[BaseException] | None,
    BaseException | None,
    TracebackType | None,
]
