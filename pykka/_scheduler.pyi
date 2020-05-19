from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, Callable

from pykka import ActorRef

class Cancellable:
    _cancelled: bool
    _timer: Any
    _timer_lock: Lock
    def __init__(self, timer: Any) -> None: ...
    def is_cancelled(self) -> bool: ...
    def set_timer(self, timer: Any) -> bool: ...
    def cancel(self) -> bool: ...

class Scheduler(ABC):
    @classmethod
    def schedule_once(
        cls, delay: float, receiver: ActorRef, message: Any
    ) -> Cancellable: ...
    @classmethod
    def schedule_at_fixed_rate(
        cls,
        initial_delay: float,
        interval: float,
        receiver: ActorRef,
        message: Any,
    ) -> Cancellable: ...
    @classmethod
    def schedule_with_fixed_delay(
        cls,
        initial_delay: float,
        delay: float,
        receiver: ActorRef,
        message: Any,
    ) -> Cancellable: ...
    @classmethod
    def _tell_periodically(
        cls,
        initial_delay: float,
        interval: float,
        receiver: ActorRef,
        message: Any,
        precise: bool,
    ) -> Cancellable: ...
    @classmethod
    def _tell_and_update_cancellable(
        cls,
        cancellable: Cancellable,
        interval: float,
        receiver: ActorRef,
        message: Any,
        started: float,
        precise: bool,
    ) -> None: ...
    @staticmethod
    @abstractmethod
    def _get_timer(delay: float, func: Callable, *args: Any) -> Any: ...
