from __future__ import annotations

import asyncio
import sys
import traceback
import types
from typing import TYPE_CHECKING, Any

import pytest

from pykka import Future, Timeout, get_all

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from pytest_mock import MockerFixture

    from tests.types import Runtime


def run_async(coroutine: Any) -> Any:
    loop = asyncio.new_event_loop()
    f = asyncio.ensure_future(coroutine, loop=loop)
    return loop.run_until_complete(f)


def test_base_future_get_is_not_implemented() -> None:
    future: Future[Any] = Future()

    with pytest.raises(NotImplementedError):
        future.get()


def test_base_future_set_is_not_implemented() -> None:
    future: Future[Any] = Future()

    with pytest.raises(NotImplementedError):
        future.set(None)


def test_base_future_set_exception_is_not_implemented() -> None:
    future: Future[Any] = Future()

    with pytest.raises(NotImplementedError):
        future.set_exception(None)


def test_set_multiple_times_fails(
    future: Future[int],
) -> None:
    future.set(0)

    with pytest.raises(Exception):  # noqa: B017, PT011
        future.set(0)


def test_get_all_blocks_until_all_futures_are_available(
    futures: list[Future[int]],
) -> None:
    futures[0].set(0)
    futures[1].set(1)
    futures[2].set(2)

    result = get_all(futures)

    assert result == [0, 1, 2]


def test_get_all_raises_timeout_if_not_all_futures_are_available(
    futures: list[Future[int]],
) -> None:
    futures[0].set(0)
    futures[1].set(1)
    # futures[2] has not been set

    with pytest.raises(Timeout):
        get_all(futures, timeout=0)


def test_get_all_can_be_called_multiple_times(
    futures: list[Future[int]],
) -> None:
    futures[0].set(0)
    futures[1].set(1)
    futures[2].set(2)

    result1 = get_all(futures)
    result2 = get_all(futures)

    assert result1 == result2


def test_future_in_future_works(runtime: Runtime) -> None:
    inner_future = runtime.future_class()
    inner_future.set("foo")

    outer_future = runtime.future_class()
    outer_future.set(inner_future)

    assert outer_future.get().get() == "foo"


def test_get_raises_exception_with_full_traceback(runtime: Runtime) -> None:
    exc_class_get = None
    exc_class_set = None
    exc_instance_get = None
    exc_instance_set = None
    exc_traceback_get = None
    exc_traceback_set = None
    future = runtime.future_class()

    try:
        raise NameError("foo")  # noqa: TRY301
    except NameError:
        exc_class_set, exc_instance_set, exc_traceback_set = sys.exc_info()
        future.set_exception()

    # We could move to another thread at this point

    try:
        future.get()
    except NameError:
        exc_class_get, exc_instance_get, exc_traceback_get = sys.exc_info()

    assert exc_class_set == exc_class_get
    assert exc_instance_set == exc_instance_get

    exc_traceback_list_set = list(reversed(traceback.extract_tb(exc_traceback_set)))
    exc_traceback_list_get = list(reversed(traceback.extract_tb(exc_traceback_get)))

    # All frames from the first traceback should be included in the
    # traceback from the future.get() reraise
    assert len(exc_traceback_list_set) < len(exc_traceback_list_get)
    for i, frame in enumerate(exc_traceback_list_set):
        assert frame == exc_traceback_list_get[i]


def test_future_supports_await_syntax(
    future: Future[int],
) -> None:
    async def get_value() -> int:
        return await future

    future.set(1)
    assert run_async(get_value()) == 1


def test_future_supports_yield_from_syntax(
    future: Future[int],
) -> None:
    @types.coroutine
    def get_value() -> Generator[None, None, int]:
        val = yield from future
        return val

    future.set(1)
    assert run_async(get_value()) == 1


def test_filter_excludes_items_not_matching_predicate(
    future: Future[Iterable[int]],
) -> None:
    filtered = future.filter(lambda x: x > 10)
    future.set([1, 3, 5, 7, 9, 11, 13, 15, 17, 19])

    assert filtered.get(timeout=0) == [11, 13, 15, 17, 19]


def test_filter_on_noniterable(
    future: Future[int],
) -> None:
    filtered = future.filter(lambda x: x > 10)  # type: ignore  # noqa: PGH003
    future.set(1)

    with pytest.raises(TypeError):
        filtered.get(timeout=0)  # pyright: ignore[reportUnknownMemberType]


def test_filter_preserves_the_timeout_kwarg(
    future: Future[Iterable[int]],
) -> None:
    filtered = future.filter(lambda x: x > 10)

    with pytest.raises(Timeout):
        filtered.get(timeout=0)


def test_filter_reuses_result_if_called_multiple_times(
    future: Future[Iterable[int]],
    mocker: MockerFixture,
) -> None:
    raise_on_reuse_func = mocker.Mock(side_effect=[False, True, Exception])

    filtered = future.filter(raise_on_reuse_func)
    future.set([1, 2])

    assert filtered.get(timeout=0) == [2]
    assert filtered.get(timeout=0) == [2]  # First result is reused
    assert filtered.get(timeout=0) == [2]  # First result is reused


def test_join_combines_multiple_futures_into_one(
    futures: list[Future[int]],
) -> None:
    joined = futures[0].join(futures[1], futures[2])
    futures[0].set(0)
    futures[1].set(1)
    futures[2].set(2)

    assert joined.get(timeout=0) == [0, 1, 2]


def test_join_preserves_timeout_kwarg(
    futures: list[Future[int]],
) -> None:
    joined = futures[0].join(futures[1], futures[2])
    futures[0].set(0)
    futures[1].set(1)
    # futures[2] has not been set

    with pytest.raises(Timeout):
        joined.get(timeout=0)


def test_map_returns_future_which_passes_result_through_func(
    future: Future[int],
) -> None:
    mapped = future.map(lambda x: x + 10)
    future.set(30)

    assert mapped.get(timeout=0) == 40


def test_map_works_on_dict(
    future: Future[dict[str, str]],
) -> None:
    # Regression test for issue #64

    mapped = future.map(lambda x: x["foo"])
    future.set({"foo": "bar"})

    assert mapped.get(timeout=0) == "bar"


def test_map_does_not_map_each_value_in_futures_iterable_result(
    future: Future[Iterable[int]],
) -> None:
    # Behavior changed in Pykka 2.0:
    # This used to map each value in the future's result through the func,
    # yielding [20, 30, 40].

    mapped = future.map(lambda x: x + 10)  # type: ignore  # noqa: PGH003
    future.set([10, 20, 30])

    with pytest.raises(TypeError):
        mapped.get(timeout=0)


def test_map_preserves_timeout_kwarg(
    future: Future[int],
) -> None:
    mapped = future.map(lambda x: x + 10)

    with pytest.raises(Timeout):
        mapped.get(timeout=0)


def test_map_reuses_result_if_called_multiple_times(
    future: Future[int],
    mocker: MockerFixture,
) -> None:
    raise_on_reuse_func = mocker.Mock(side_effect=[10, Exception])

    mapped = future.map(raise_on_reuse_func)
    future.set(30)

    assert mapped.get(timeout=0) == 10
    assert mapped.get(timeout=0) == 10  # First result is reused


def test_reduce_applies_function_cumulatively_from_the_left(
    future: Future[Iterable[int]],
) -> None:
    reduced: Future[int] = future.reduce(lambda x, y: x + y)
    future.set([1, 2, 3, 4])

    assert reduced.get(timeout=0) == 10


def test_reduce_accepts_an_initial_value(
    future: Future[Iterable[int]],
) -> None:
    reduced = future.reduce(lambda x, y: x + y, 5)
    future.set([1, 2, 3, 4])

    assert reduced.get(timeout=0) == 15


def test_reduce_on_noniterable(
    future: Future[int],
) -> None:
    reduced = future.reduce(lambda x, y: x + y)  # type: ignore  # noqa: PGH003
    future.set(1)

    with pytest.raises(TypeError):
        reduced.get(timeout=0)  # pyright: ignore[reportUnknownMemberType]


def test_reduce_preserves_the_timeout_kwarg(
    future: Future[Iterable[int]],
) -> None:
    reduced: Future[int] = future.reduce(lambda x, y: x + y)

    with pytest.raises(Timeout):
        reduced.get(timeout=0)


def test_reduce_reuses_result_if_called_multiple_times(
    future: Future[Iterable[int]],
    mocker: MockerFixture,
) -> None:
    raise_on_reuse_func = mocker.Mock(side_effect=[3, 6, Exception])

    reduced = future.reduce(raise_on_reuse_func)
    future.set([1, 2, 3])

    assert reduced.get(timeout=0) == 6
    assert reduced.get(timeout=0) == 6  # First result is reused
    assert reduced.get(timeout=0) == 6  # First result is reused
