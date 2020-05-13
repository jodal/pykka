import logging
import time
from threading import Timer, Lock
from typing import Any, Optional

from pykka import ActorRef

logger = logging.getLogger("pykka")

__all__ = ["Scheduler", "Cancellable"]


class Cancellable:
    """
    Signifies a delayed task that can be cancelled.

    Built around a `threading.Timer` object and is able to cancel it.
    For periodical jobs its `_timer` property is being updated on
    every run from a separated thread, so to avoid race conditions where
    in the middle of the `cancel` run another thread updates the `_timer`
    property with a non-cancelled timer, Lock is used.
    """

    def __init__(self, timer):
        self._cancelled: bool = False
        self._timer: Optional[Timer] = timer
        self._timer_lock: Lock = Lock()

    def is_cancelled(self) -> bool:
        """
        `._cancelled` property getter for external users.

        There is no external setter for this property.

        Returns: Bool that shows whether it is cancelled.
        """
        return self._cancelled

    def set_timer(self, timer: Timer) -> bool:
        """
        `_.timer` property setter to update timers for periodic jobs.

        There is no external getter for this property.

        Cancelled Canellable objects shouldn't allow to update their timers.

        Args:
            timer (Timer): Timer object handling a delayed task execution.
        Returns: Bool that shows whether the '_.timer` property was updated.
        """
        with self._timer_lock:
            if self.is_cancelled():
                logger.error(
                    "An attempt to update a timer for a stopped Cancellable happened."
                )
                return False
            else:
                self._timer = timer
                return True

    def cancel(self) -> bool:
        """
        Cancels the Cancellable by stopping its timer.

        Returns True only if it is not in a cancelled state.
        If it was requested to cancel an already cancelled Cancellable,
        it returns False to be consistent with a Cancellable object
        from Akka.

        Returns: Bool that shows whether this request actually cancelled
                 the Cancellable timer.
        """
        with self._timer_lock:
            if self.is_cancelled():
                return False
            else:
                if isinstance(self._timer, Timer):
                    self._timer.cancel()
                self._cancelled = True
                return True


class Scheduler:
    """
    A basic Pykka Scheduler service based on Akka Scheduler behaviour.

    Its main purpose is to `tell` a message to an actor after a specified
    delay or to do it periodically. It isn't a long-term scheduler
    and is expected to be used for retransmitting messages or to schedule
    periodic startup of an actor-based data processing pipeline.
    """

    @staticmethod
    def schedule_once(
            delay: float, receiver: ActorRef, message: Any
    ) -> Cancellable:
        """
        Based on:
        akka.Scheduler.scheduleOnce(
            delay: java.time.Duration,
            receiver: ActorRef,
            message: Any
        ): Cancellable

        Creates a `threading.Timer` object to `tell` a message to an
        actor once after a specified delay. The returning Cancellable object
        can be cancelled before a message was sent.

        Args:
            delay (float): How much time in ``seconds`` must pass before execution.
            receiver (ActorRef): Actor Reference of an addressee.
            message (Any): Message to send to an addressee.
        Returns: A Cancellable object.
        """
        timer = Timer(interval=delay, function=receiver.tell, args=(message,))
        timer.start()
        return Cancellable(timer)

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

        if precise:
            started = time.time() + initial_delay
        else:
            started = None

        timer = Timer(
            interval=initial_delay,
            function=cls._tell_and_update_cancellable,
            args=(cancellable, interval, receiver, message, started),
        )
        timer.start()

        cancellable.set_timer(timer)
        return cancellable

    @classmethod
    def _tell_and_update_cancellable(
            cls,
            cancellable: Cancellable,
            interval: float,
            receiver: ActorRef,
            message: Any,
            started: Optional[float] = None,
    ):
        """
        A pseudo-callback function that creates a new Timer for the next
        message delivery and updates a Cancellable object with this Timer
        to keep the scheduled activity cancellable.

        If `started` parameter is not None, it tried to be as precise as
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
        if started:
            time_drift = (time.time() - started) % interval
            delay = interval - time_drift
        else:
            delay = interval

        timer = Timer(
            interval=delay,
            function=cls._tell_and_update_cancellable,
            args=(cancellable, interval, receiver, message, started),
        )
        timer.start()

        receiver.tell(message)
        cancellable.set_timer(timer)
