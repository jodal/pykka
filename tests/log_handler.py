import collections
import logging
import threading
import time
from enum import StrEnum
from typing import Any


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PykkaTestLogHandler(logging.Handler):
    messages_lock: threading.RLock
    events: dict[str, threading.Event]
    messages: dict[LogLevel, list[logging.LogRecord]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.messages_lock = threading.RLock()
        with self.messages_lock:
            self.events = collections.defaultdict(threading.Event)
            self.messages = {}
            self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        with self.messages_lock:
            level = LogLevel(record.levelname.lower())
            self.messages[level].append(record)
            self.events[level].set()

    def reset(self) -> None:
        with self.messages_lock:
            for level in LogLevel:
                self.events[level].clear()
                self.messages[level] = []

    def wait_for_message(
        self, level: LogLevel, num_messages: int = 1, timeout: float = 5
    ) -> None:
        """Wait until at least `num_messages` log messages have been emitted
        to the given log level."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self.messages_lock:
                if len(self.messages[level]) >= num_messages:
                    return
                self.events[level].clear()
            self.events[level].wait(1)
        msg = f"Timeout: Waited {timeout:d}s for log message"
        raise Exception(msg)
