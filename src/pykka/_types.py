from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


AttrPath: TypeAlias = tuple[str, ...]


# OptExcInfo matches the return type of sys.exc_info() in typeshed
OptExcInfo = tuple[
    Optional[type[BaseException]],
    Optional[BaseException],
    Optional[TracebackType],
]
