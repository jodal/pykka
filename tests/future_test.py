import pickle
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

    def test_future_works_across_serialization(self):
        future1 = self.future_class()
        future1.set('foo')
        serialized_future = pickle.dumps(future1)
        future2 = pickle.loads(serialized_future)
        self.assertEqual(future2.get(), 'foo')

    def test_future_in_future_works_across_serialization(self):
        inner_future1 = self.future_class()
        inner_future1.set('foo')
        outer_future1 = self.future_class()
        outer_future1.set(inner_future1)

        serialized_future = pickle.dumps(outer_future1)
        outer_future2 = pickle.loads(serialized_future)
        inner_future2 = outer_future2.get()
        self.assertEqual(inner_future2.get(), 'foo')

    def test_future_works_after_multiple_serializations(self):
        future1 = self.future_class()
        future1.set('foo')
        serialized_future1 = pickle.dumps(future1)
        future2 = pickle.loads(serialized_future1)
        serialized_future2 = pickle.dumps(future2)
        future3 = pickle.loads(serialized_future2)
        self.assertEqual(future3.get(), 'foo')


class GeventFutureTest(FutureTest, unittest.TestCase):
    future_class = GeventFuture


class ThreadingFutureTest(FutureTest, unittest.TestCase):
    future_class = ThreadingFuture
