import logging
from threading import Timer

import pytest

from pykka import Cancellable

logger = logging.getLogger("pykka")


@pytest.fixture(scope="module")
def counting_actor_class(runtime):
    class CountingActor(runtime.actor_class):
        def __init__(self):
            super().__init__()
            self.count = 0

        def on_receive(self, message):
            logger.debug("CountingActor received message %s.", message)
            if message.get("command") == "return count":
                return self.count
            else:
                self.count += 1

    return CountingActor


@pytest.fixture
def actor_ref_scheduler_sleep(counting_actor_class, runtime):
    ref = counting_actor_class.start()
    yield ref, runtime.scheduler_class, runtime.sleep_func
    ref.stop()


@pytest.fixture(params=[None, Timer(1, print, ("Hello Pykka!",))])
def timer(request):
    test_timer = request.param
    yield test_timer
    if isinstance(test_timer, Timer):
        test_timer.cancel()


def test_cancellable_is_cancellable(timer):
    cancellable = Cancellable(timer)
    first_check = cancellable.is_cancelled()
    result = cancellable.cancel()
    second_check = cancellable.is_cancelled()
    assert first_check is False
    assert result is True
    assert second_check is True


def test_cancelled_cancellable_is_not_cancellable(timer):
    cancellable = Cancellable(timer)
    cancellable.cancel()
    result = cancellable.cancel()
    assert result is False


def test_cancellable_set_timer(timer):
    cancellable = Cancellable(None)
    result = cancellable.set_timer(timer)
    assert cancellable._timer == timer
    assert result is True


def test_cancelled_cancellable_set_timer(timer):
    cancellable = Cancellable("Not a timer or None")
    cancellable.cancel()
    result = cancellable.set_timer(timer)
    assert cancellable._timer == "Not a timer or None"
    assert result is False


def test_schedule_once_sends_a_message_only_once(actor_ref_scheduler_sleep):
    actor_ref, scheduler, sleep = actor_ref_scheduler_sleep
    scheduler.schedule_once(0.2, actor_ref, {"command": "increment"})
    sleep(0.3)
    first_count = actor_ref.ask({"command": "return count"})
    sleep(0.3)
    second_count = actor_ref.ask({"command": "return count"})
    assert first_count == 1
    assert second_count == first_count


def test_schedule_once_is_cancellable(actor_ref_scheduler_sleep):
    actor_ref, scheduler, sleep = actor_ref_scheduler_sleep
    cancellable = scheduler.schedule_once(
        0.2, actor_ref, {"command": "increment"}
    )
    cancellable.cancel()
    sleep(0.3)
    count = actor_ref.ask({"command": "return count"})
    assert count == 0


def test_periodic_job_is_cancellable_before_the_first_run(
    actor_ref_scheduler_sleep
):
    actor_ref, scheduler, sleep = actor_ref_scheduler_sleep
    cancellable = scheduler.schedule_with_fixed_delay(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    cancellable.cancel()
    sleep(0.2)
    count = actor_ref.ask({"command": "return count"})
    assert count == 0


def test_periodic_job_is_cancellable_after_the_first_run(
    actor_ref_scheduler_sleep
):
    actor_ref, scheduler, sleep = actor_ref_scheduler_sleep
    cancellable = scheduler.schedule_at_fixed_rate(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    sleep(0.15)
    cancellable.cancel()
    first_count = actor_ref.ask({"command": "return count"})
    sleep(0.1)
    second_count = actor_ref.ask({"command": "return count"})
    assert first_count == 1
    assert second_count == first_count


def test_schedule_at_fixed_rate_is_executed_periodically(
    actor_ref_scheduler_sleep
):
    actor_ref, scheduler, sleep = actor_ref_scheduler_sleep
    cancellable = scheduler.schedule_at_fixed_rate(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    sleep(0.15)
    first_count = actor_ref.ask({"command": "return count"})
    sleep(0.1)
    second_count = actor_ref.ask({"command": "return count"})
    sleep(0.1)
    third_count = actor_ref.ask({"command": "return count"})
    cancellable.cancel()
    assert first_count == 1
    assert second_count == 2
    assert third_count == 3


def test_schedule_with_fixed_delay_is_executed_periodically(
    actor_ref_scheduler_sleep
):
    actor_ref, scheduler, sleep = actor_ref_scheduler_sleep
    cancellable = scheduler.schedule_with_fixed_delay(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    sleep(0.15)
    first_count = actor_ref.ask({"command": "return count"})
    sleep(0.1)
    second_count = actor_ref.ask({"command": "return count"})
    sleep(0.1)
    third_count = actor_ref.ask({"command": "return count"})
    cancellable.cancel()
    assert first_count == 1
    assert second_count == 2
    assert third_count == 3


def test_periodic_job_stops_when_actor_is_stopped(actor_ref_scheduler_sleep):
    actor_ref, scheduler, sleep = actor_ref_scheduler_sleep
    cancellable = scheduler.schedule_at_fixed_rate(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    # There is no exception on stop during running interval:
    actor_ref.stop()
    sleep(0.15)
    cancellable.cancel()
