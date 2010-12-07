from multiprocessing import Pipe
import unittest

import pykka

class FutureTest(unittest.TestCase):
    def setUp(self):
        self.connection, future_connection = Pipe()
        self.future = pykka.Future(future_connection)

    def test_future_str_returns_a_string(self):
        self.connection.send(10)
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
        self.connection.send(10)
        result1 = self.future.get()

        self.connection.send(10)
        result2 = self.future.wait()

        self.assertEqual(result1, result2)

class GetAllTest(unittest.TestCase):
    def setUp(self):
        self.connections = []
        self.futures = []
        for i in range(3):
            connection, future_connection = Pipe()
            self.connections.append(connection)
            self.futures.append(pykka.Future(future_connection))

    def test_get_all_blocks_until_all_futures_are_available(self):
        self.connections[0].send(0)
        self.connections[1].send(1)
        self.connections[2].send(2)
        result = pykka.get_all(self.futures)
        self.assertEqual(result, [0, 1, 2])

    def test_get_all_times_out_if_not_all_futures_are_available(self):
        self.connections[0].send(0)
        self.connections[2].send(2)
        result = pykka.get_all(self.futures, timeout=0)
        self.assertEqual(result, [0, None, 2])

    def test_wait_all_is_alias_of_get_all(self):
        self.connections[0].send(0)
        self.connections[1].send(1)
        self.connections[2].send(2)
        result1 = pykka.get_all(self.futures)

        self.connections[0].send(0)
        self.connections[1].send(1)
        self.connections[2].send(2)
        result2 = pykka.wait_all(self.futures)

        self.assertEqual(result1, result2)
