import time
from threading import Timer

import pytest

from pykka import Cancellable, Scheduler

PERIODIC_JOB_METHODS = (
    Scheduler.schedule_at_fixed_rate,
    Scheduler.schedule_with_fixed_delay,
)


@pytest.fixture(scope="module", params=PERIODIC_JOB_METHODS)
def periodic_job_method(request):
    return request.param


@pytest.fixture(scope="module")
def counting_actor_class(runtime):
    class CountingActor(runtime.actor_class):
        def __init__(self):
            super().__init__()
            self.count = 0

        def on_receive(self, message):
            if message.get("command") == "return count":
                return self.count
            else:
                self.count += 1

    return CountingActor


@pytest.fixture
def actor_ref(counting_actor_class):
    ref = counting_actor_class.start()
    yield ref
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


def test_schedule_once_sends_a_message_only_once(actor_ref):
    Scheduler.schedule_once(0.2, actor_ref, {"command": "increment"})
    time.sleep(0.3)
    first_count = actor_ref.ask({"command": "return count"})
    time.sleep(0.3)
    second_count = actor_ref.ask({"command": "return count"})
    assert first_count == 1
    assert second_count == first_count


def test_schedule_once_is_cancellable(actor_ref):
    cancellable = Scheduler.schedule_once(
        0.2, actor_ref, {"command": "increment"}
    )
    cancellable.cancel()
    time.sleep(0.3)
    count = actor_ref.ask({"command": "return count"})
    assert count == 0


def test_periodic_job_is_cancellable_before_the_first_run(
    periodic_job_method, actor_ref
):
    cancellable = periodic_job_method(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    cancellable.cancel()
    time.sleep(0.2)
    count = actor_ref.ask({"command": "return count"})
    assert count == 0


def test_periodic_job_is_cancellable_after_the_first_run(
    periodic_job_method, actor_ref
):
    cancellable = periodic_job_method(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    time.sleep(0.15)
    cancellable.cancel()
    first_count = actor_ref.ask({"command": "return count"})
    time.sleep(0.1)
    second_count = actor_ref.ask({"command": "return count"})
    assert first_count == 1
    assert second_count == first_count


def test_periodic_job_is_executed_periodically(periodic_job_method, actor_ref):
    cancellable = periodic_job_method(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    time.sleep(0.15)
    first_count = actor_ref.ask({"command": "return count"}, block=False)
    time.sleep(0.1)
    second_count = actor_ref.ask({"command": "return count"}, block=False)
    time.sleep(0.1)
    third_count = actor_ref.ask({"command": "return count"}, block=False)
    cancellable.cancel()
    assert first_count.get() == 1
    assert second_count.get() == 2
    assert third_count.get() == 3


def test_periodic_job_stops_when_actor_is_stopped(
    periodic_job_method, counting_actor_class
):
    actor_ref = counting_actor_class.start()
    cancellable = periodic_job_method(
        0.1, 0.1, actor_ref, {"command": "increment"}
    )
    # There is no exception on stop during running interval:
    actor_ref.stop()
    time.sleep(0.15)
    cancellable.cancel()
