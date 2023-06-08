from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Optional, Sequence, Tuple, Type

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


AttrPath: TypeAlias = Sequence[str]


# OptExcInfo matches the return type of sys.exc_info() in typeshed
OptExcInfo = Tuple[
    Optional[Type[BaseException]],
    Optional[BaseException],
    Optional[TracebackType],
]
