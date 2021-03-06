from types import TracebackType
from typing import Optional, Tuple, Type

# OptExcInfo matches the return type of sys.exc_info() in typeshed
OptExcInfo = Tuple[
    Optional[Type[BaseException]],
    Optional[BaseException],
    Optional[TracebackType],
]
