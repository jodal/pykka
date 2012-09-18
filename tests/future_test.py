import sys
import traceback
import unittest

from pykka import Timeout
from pykka.future import Future, ThreadingFuture, get_all

try:
    from gevent.event import AsyncResult
    from pykka.gevent import GeventFuture
    HAS_GEVENT = True
except ImportError:
    HAS_GEVENT = False


class FutureBaseTest(unittest.TestCase):
    def setUp(self):
        self.future = Future()

    def test_future_get_is_not_implemented(self):
        self.assertRaises(NotImplementedError, self.future.get)

    def test_future_set_is_not_implemented(self):
        self.assertRaises(NotImplementedError, self.future.set, None)

    def test_future_set_exception_is_not_implemented(self):
        self.assertRaises(NotImplementedError, self.future.set_exception, None)


class FutureTest(object):
    def setUp(self):
        self.results = [self.future_class() for _ in range(3)]

    def test_get_all_blocks_until_all_futures_are_available(self):
        self.results[0].set(0)
        self.results[1].set(1)
        self.results[2].set(2)
        result = get_all(self.results)
        self.assertEqual(result, [0, 1, 2])

    def test_get_all_raises_timeout_if_not_all_futures_are_available(self):
        try:
            self.results[0].set(0)
            self.results[2].set(2)
            get_all(self.results, timeout=0)
            self.fail('Should timeout')
        except Timeout:
            pass

    def test_get_all_can_be_called_multiple_times(self):
        self.results[0].set(0)
        self.results[1].set(1)
        self.results[2].set(2)
        result1 = get_all(self.results)
        result2 = get_all(self.results)
        self.assertEqual(result1, result2)

    def test_future_in_future_works(self):
        inner_future = self.future_class()
        inner_future.set('foo')
        outer_future = self.future_class()
        outer_future.set(inner_future)
        self.assertEqual(outer_future.get().get(), 'foo')

    def test_get_raises_exception_with_full_traceback(self):
        exc_class_get = None
        exc_class_set = None
        exc_instance_get = None
        exc_instance_set = None
        exc_traceback_get = None
        exc_traceback_set = None
        future = self.future_class()

        try:
            raise NameError('foo')
        except NameError:
            exc_class_set, exc_instance_set, exc_traceback_set = sys.exc_info()
            future.set_exception()

        # We could move to another thread at this point

        try:
            future.get()
        except NameError:
            exc_class_get, exc_instance_get, exc_traceback_get = sys.exc_info()

        self.assertEqual(exc_class_set, exc_class_get)
        self.assertEqual(exc_instance_set, exc_instance_get)

        exc_traceback_list_set = list(reversed(
            traceback.extract_tb(exc_traceback_set)))
        exc_traceback_list_get = list(reversed(
            traceback.extract_tb(exc_traceback_get)))

        # All frames from the first traceback should be included in the
        # traceback from the future.get() reraise
        self.assert_(len(exc_traceback_list_set) < len(exc_traceback_list_get))
        for i, frame in enumerate(exc_traceback_list_set):
            self.assertEquals(frame, exc_traceback_list_get[i])


class ThreadingFutureTest(FutureTest, unittest.TestCase):
    future_class = ThreadingFuture


if HAS_GEVENT:
    class GeventFutureTest(FutureTest, unittest.TestCase):
        future_class = GeventFuture

        def test_can_wrap_existing_async_result(self):
            async_result = AsyncResult()
            future = GeventFuture(async_result)
            self.assertEquals(async_result, future.async_result)

        def test_get_raises_exception_with_full_traceback(self):
            # gevent prints the first half of the traceback instead of
            # passing it through to the other side of the AsyncResult
            pass
