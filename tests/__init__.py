import logging
import threading
import time


class TestLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        self.event = threading.Event()
        self.lock = threading.RLock()
        with self.lock:
            self.messages = {}
            self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        with self.lock:
            self.messages[record.levelname.lower()].append(record)
            self.event.set()

    def reset(self):
        with self.lock:
            self.messages = {
                'debug': [],
                'info': [],
                'warning': [],
                'error': [],
                'critical': [],
            }
            self.event.clear()

    def wait_for_message(self):
        """Wait until at least one log message has been emitted."""
        time.sleep(0.001)  # Yield to other threads
        self.event.wait(5)
