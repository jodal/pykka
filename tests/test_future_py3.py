import asyncio
import sys

import pytest

from pykka import _compat


def run_async(coroutine):
    loop = asyncio.get_event_loop()
    f = asyncio.ensure_future(coroutine, loop=loop)
    return loop.run_until_complete(f)


@pytest.mark.skipif(
    sys.version_info < (3, 5), reason='await requires Python 3.5+'
)
def test_future_supports_await_syntax(future):
    @asyncio.coroutine
    def get_value():
        return _compat.await_keyword(future)

    future.set(1)
    assert run_async(get_value()) == 1


def test_future_supports_yield_from_syntax(future):
    @asyncio.coroutine
    def get_value():
        val = yield from future
        return val

    future.set(1)
    assert run_async(get_value()) == 1
