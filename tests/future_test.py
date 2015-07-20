import sys
import traceback
import unittest

from pykka import Future, ThreadingFuture, Timeout, get_all


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

    def test_set_multiple_times_fails(self):
        self.results[0].set(0)
        self.assertRaises(Exception, self.results[0].set, 0)

    def test_get_all_blocks_until_all_futures_are_available(self):
        self.results[0].set(0)
        self.results[1].set(1)
        self.results[2].set(2)
        result = get_all(self.results)
        self.assertEqual(result, [0, 1, 2])

    def test_get_all_raises_timeout_if_not_all_futures_are_available(self):
        self.results[0].set(0)
        self.results[1].set(1)

        self.assertRaises(Timeout, get_all, self.results, timeout=0)

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

    def test_filter_excludes_items_not_matching_predicate(self):
        future = self.results[0].filter(lambda x: x > 10)
        self.results[0].set([1, 3, 5, 7, 9, 11, 13, 15, 17, 19])

        self.assertEqual(future.get(timeout=0), [11, 13, 15, 17, 19])

    def test_filter_on_noniterable(self):
        future = self.results[0].filter(lambda x: x > 10)
        self.results[0].set(1)

        self.assertRaises(TypeError, future.get, timeout=0)

    def test_filter_preserves_the_timeout_kwarg(self):
        future = self.results[0].filter(lambda x: x > 10)

        self.assertRaises(Timeout, future.get, timeout=0)

    def test_join_combines_multiple_futures_into_one(self):
        future = self.results[0].join(self.results[1], self.results[2])
        self.results[0].set(0)
        self.results[1].set(1)
        self.results[2].set(2)

        self.assertEqual(future.get(timeout=0), [0, 1, 2])

    def test_join_preserves_timeout_kwarg(self):
        future = self.results[0].join(self.results[1], self.results[2])
        self.results[0].set(0)
        self.results[1].set(1)

        self.assertRaises(Timeout, future.get, timeout=0)

    def test_map_returns_future_which_passes_noniterable_through_func(self):
        future = self.results[0].map(lambda x: x + 10)
        self.results[0].set(30)

        self.assertEqual(future.get(timeout=0), 40)

    def test_map_returns_future_which_maps_iterable_through_func(self):
        future = self.results[0].map(lambda x: x + 10)
        self.results[0].set([10, 20, 30])

        self.assertEqual(future.get(timeout=0), [20, 30, 40])

    def test_map_preserves_timeout_kwarg(self):
        future = self.results[0].map(lambda x: x + 10)

        self.assertRaises(Timeout, future.get, timeout=0)

    def test_reduce_applies_function_cumulatively_from_the_left(self):
        future = self.results[0].reduce(lambda x, y: x + y)
        self.results[0].set([1, 2, 3, 4])

        self.assertEqual(future.get(timeout=0), 10)

    def test_reduce_accepts_an_initial_value(self):
        future = self.results[0].reduce(lambda x, y: x + y, 5)
        self.results[0].set([1, 2, 3, 4])

        self.assertEqual(future.get(timeout=0), 15)

    def test_reduce_on_noniterable(self):
        future = self.results[0].reduce(lambda x, y: x + y)
        self.results[0].set(1)

        self.assertRaises(TypeError, future.get, timeout=0)

    def test_reduce_preserves_the_timeout_kwarg(self):
        future = self.results[0].reduce(lambda x, y: x + y)

        self.assertRaises(Timeout, future.get, timeout=0)


class ThreadingFutureTest(FutureTest, unittest.TestCase):
    future_class = ThreadingFuture


try:
    from gevent.event import AsyncResult
    from pykka.gevent import GeventFuture

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
except ImportError:
    pass


try:
    from pykka.eventlet import EventletFuture

    class EventletFutureTest(FutureTest, unittest.TestCase):
        future_class = EventletFuture
except ImportError:
    pass
