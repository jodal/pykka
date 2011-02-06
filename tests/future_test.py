import gevent.event
import unittest

import pykka

class FutureTest(unittest.TestCase):
    def setUp(self):
        self.result = gevent.event.AsyncResult()
        self.future = pykka.Future(self.result)

    def test_future_str_returns_a_string(self):
        self.result.set(10)
        self.assertEqual('10', str(self.future))

    def test_future_repr_does_not_block(self):
        # Do not send anything on the connection
        repr(self.future)

    def test_future_repr_returns_a_string_which_includes_the_word_future(self):
        self.assert_('Future' in repr(self.future))

    def test_future_get_can_timeout_and_return_none(self):
        # Do not send anything on the connection
        self.assertEqual(None, self.future.get(timeout=0.1))

    def test_future_get_can_timeout_immediately(self):
        # Do not send anything on the connection
        self.assertEqual(None, self.future.get(timeout=False))

    def test_future_wait_is_alias_of_get(self):
        self.result.set(10)
        result1 = self.future.get()
        result2 = self.future.wait()
        self.assertEqual(result1, result2)

class GetAllTest(unittest.TestCase):
    def setUp(self):
        self.results = []
        self.futures = []
        for i in range(3):
            result = gevent.event.AsyncResult()
            self.results.append(result)
            self.futures.append(pykka.Future(result))

    def test_get_all_blocks_until_all_futures_are_available(self):
        self.results[0].set(0)
        self.results[1].set(1)
        self.results[2].set(2)
        result = pykka.get_all(self.futures)
        self.assertEqual(result, [0, 1, 2])

    def test_get_all_times_out_if_not_all_futures_are_available(self):
        self.results[0].set(0)
        self.results[2].set(2)
        result = pykka.get_all(self.futures, timeout=0)
        self.assertEqual(result, [0, None, 2])

    def test_wait_all_is_alias_of_get_all(self):
        self.results[0].set(0)
        self.results[1].set(1)
        self.results[2].set(2)
        result1 = pykka.get_all(self.futures)
        result2 = pykka.wait_all(self.futures)
        self.assertEqual(result1, result2)
