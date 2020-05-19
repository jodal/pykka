import logging
import time
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any

from pykka import ActorDeadError, ActorRef

logger = logging.getLogger("pykka")

__all__ = ["Cancellable", "Scheduler"]


class Cancellable:
    """
    Signifies a delayed task that can be cancelled.

    Built around a `threading.Timer` object and is able to cancel it.
    For periodical jobs its `_timer` property is being updated on
    every run from a separated thread, so to avoid race conditions where
    in the middle of the `cancel` run another thread updates the `_timer`
    property with a non-cancelled timer, Lock is used.
    """

    def __init__(self, timer: Any) -> None:
        self._cancelled: bool = False
        self._timer: Any = timer
        self._timer_lock: Lock = Lock()

    def is_cancelled(self) -> bool:
        """
        `._cancelled` property getter for external users.

        There is no external setter for this property.

        Returns: Bool that shows whether it is cancelled.
        """
        return self._cancelled

    def set_timer(self, timer: Any) -> bool:
        """
        `_.timer` property setter to update timers for periodic jobs.

        There is no external getter for this property.

        Cancelled Cancellable objects shouldn't allow to update their timers.

        Args:
            timer: Timer or GreenEvent object handling a delayed task execution.
        Returns: Bool that shows whether the '_.timer` property was updated.
        """
        with self._timer_lock:
            if self.is_cancelled():
                logger.error(
                    "An attempt to update a timer for a stopped Cancellable happened."
                )
                return False
            self._timer = timer
            return True

    def cancel(self) -> bool:
        """
        Cancels the Cancellable by stopping its timer.

        Returns True only if it is not in a cancelled state.
        If it was requested to cancel an already cancelled Cancellable,
        it returns False to be consistent with a Cancellable object
        from Akka.

        'threading.Timer' and 'GreenThread' has 'cancel' commands.
        'Greenlet' from gevent has only 'kill' command.

        Returns: Bool that shows whether this request actually cancelled
                 the Cancellable timer.
        """
        with self._timer_lock:
            if self.is_cancelled():
                return False
            self._cancelled = True
            if hasattr(self._timer, "cancel"):
                self._timer.cancel()
                return True
            if hasattr(self._timer, "kill"):
                self._timer.kill()
                return True
            logger.error("Tried to cancel Cancellable without a proper Timer.")
            return True


class Scheduler(ABC):
    """
    Interface for a Scheduler class.
    """

    @classmethod
    def schedule_once(
        cls, delay: float, receiver: ActorRef, message: Any
    ) -> Cancellable:
        """
        Based on:
        akka.Scheduler.scheduleOnce(
            delay: java.time.Duration,
            receiver: ActorRef,
            message: Any
        ): Cancellable

        Creates a time object to `tell` a message to an actor once after a specified
        delay. The returning Cancellable object can be cancelled before a message was
        sent.

        Args:
            delay (float): How much time in ``seconds`` must pass before execution.
            receiver (ActorRef): Actor Reference of an addressee.
            message (Any): Message to send to an addressee.
        Returns: A Cancellable object.
        """
        cancellable = Cancellable(None)
        timer = cls._get_timer(delay, receiver.tell, message)
        cancellable.set_timer(timer)
        return cancellable

    @classmethod
    def schedule_at_fixed_rate(
        cls,
        initial_delay: float,
        interval: float,
        receiver: ActorRef,
        message: Any,
    ) -> Cancellable:
        """
        Based on:
        akka.Scheduler.scheduleAtFixedRate(
            initialDelay: FiniteDuration,
            interval: FiniteDuration,
            receiver: ActorRef,
            message: Any
        ): Cancellable

        Schedules a message to be sent to an actor PRECISELY every `delay`
        seconds after waiting for an `initial_delay` amount of seconds.
        Any time drift is compensated here by performing additional
        calculations.

        Args:
            initial_delay (float): How many seconds we wait before the first execution.
            interval (float): How many seconds we wait between executions.
            receiver (ActorRef): Actor Reference of an addressee.
            message (Any): Message to send to an addressee.
        Returns: A Cancellable object.
        """
        return cls._tell_periodically(
            initial_delay, interval, receiver, message, precise=True
        )

    @classmethod
    def schedule_with_fixed_delay(
        cls,
        initial_delay: float,
        delay: float,
        receiver: ActorRef,
        message: Any,
    ) -> Cancellable:
        """
        Based on:
        akka.Scheduler.scheduleWithFixedDelay(
            initialDelay: FiniteDuration,
            delay: FiniteDuration,
            receiver: ActorRef,
            message: Any
        ): Cancellable

        Schedules a message to be sent to an actor every `delay` seconds after
        waiting for an `initial_delay` amount of seconds. This is not a precise
        method, so there can be a slight time drift.

        Args:
            initial_delay (float): How many seconds we wait before the first execution.
            delay (float): How many seconds we wait between executions.
            receiver (ActorRef): Actor Reference of an addressee.
            message (Any): Message to send to an addressee.
        Returns: A Cancellable object.
        """
        return cls._tell_periodically(
            initial_delay, delay, receiver, message, precise=False
        )

    @classmethod
    def _tell_periodically(
        cls,
        initial_delay: float,
        interval: float,
        receiver: ActorRef,
        message: Any,
        precise: bool,
    ) -> Cancellable:
        """
        A generic method to handle both precise and imprecise versions of
        periodical message sending.

        It returns a Cancellable object, that can anytime cancel scheduled
        executions by calling its `.cancel()` method. Its `._timer` property
        is being updated via a pseudo-callback `_execute_and_update_cancellable`
        that sends a message and creates a new Timer for another execution.
        To keep it cancellable, this callback replaces an expired timer of
        the returned Cancellable object with this newly created timer.

        Args:
            initial_delay (float): How many seconds we wait before the first execution.
            interval (float): How many seconds we wait between executions.
            receiver (ActorRef): Actor Reference of an addressee.
            message (Any): Message to send to an addressee.
            precise (bool): Defines whether the time drift should be compensated to keep
                            the fixed messaging rate.
        Returns: A Cancellable object.
        """
        cancellable = Cancellable(None)

        started = time.time() + initial_delay

        timer = cls._get_timer(
            initial_delay,
            cls._tell_and_update_cancellable,
            cancellable,
            interval,
            receiver,
            message,
            started,
            precise,
        )
        cancellable.set_timer(timer)
        return cancellable

    @classmethod
    def _tell_and_update_cancellable(
        cls,
        cancellable: Cancellable,
        interval: float,
        receiver: ActorRef,
        message: Any,
        started: float,
        precise: bool,
    ) -> None:
        """
        A pseudo-callback function that creates a new Timer for the next
        message delivery and updates a Cancellable object with this Timer
        to keep the scheduled activity cancellable.

        If `started` parameter is not None, it tries to be as precise as
        possible and to calculate and compensate time drift from the 'ideal'
        execution time.

        Args:
            cancellable (Cancellable): A previously returned object whose
                `_timer` property we need to update.
            interval (float): How many seconds we wait between executions.
            receiver (ActorRef): Actor Reference of an addressee.
            message (Any): Message to send to an addressee.
            started (Optional[float]): Unix timestamp that says when our
                first execution was happened. If set, it's used to calculate
                and compensate time drift between executions.
        Returns: None, since that's a pseudo-callback.
        """
        now = time.time()
        if precise or now < started:
            time_drift = (now - started) % interval
            delay = interval - time_drift
        else:
            delay = interval

        try:
            if now >= started:
                receiver.tell(message)
            timer = cls._get_timer(
                delay,
                cls._tell_and_update_cancellable,
                cancellable,
                interval,
                receiver,
                message,
                started,
                precise,
            )
            cancellable.set_timer(timer)
        except ActorDeadError as exception:
            logger.error("Stopping periodic job: %s", exception)

    @staticmethod
    @abstractmethod
    def _get_timer(delay, func, *args):
        """
        Abstract method to return a timer of an specific type.
        """
        raise NotImplementedError("Use a subclass of Scheduler")
