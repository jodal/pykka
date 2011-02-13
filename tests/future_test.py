import gevent
import gevent.event
import unittest

from pykka import get_all, wait_all

class GetAllTest(unittest.TestCase):
    def setUp(self):
        self.results = [gevent.event.AsyncResult() for _ in range(3)]

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
        except gevent.Timeout:
            pass

    def test_wait_all_is_alias_of_get_all(self):
        self.results[0].set(0)
        self.results[1].set(1)
        self.results[2].set(2)
        result1 = get_all(self.results)
        result2 = wait_all(self.results)
        self.assertEqual(result1, result2)
