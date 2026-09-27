from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from benchmarks.threading_actors import BENCHMARKS

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize("func", BENCHMARKS.values(), ids=BENCHMARKS.keys())
def test_benchmark_runs(func: Callable[[int], float]) -> None:
    assert func(10) > 0
