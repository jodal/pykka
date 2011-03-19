import unittest

from pykka.future import Timeout, ThreadingFuture, get_all
from pykka.gevent import GeventFuture


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
            result = get_all(self.results, timeout=0)
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


class GeventFutureTest(FutureTest, unittest.TestCase):
    future_class = GeventFuture


class ThreadingFutureTest(FutureTest, unittest.TestCase):
    future_class = ThreadingFuture
