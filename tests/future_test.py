from multiprocessing import Pipe
import unittest

from pykka import Future

class FutureTest(unittest.TestCase):
    def setUp(self):
        self.connection, future_connection = Pipe()
        self.future = Future(future_connection)

    def test_future_str_returns_a_string(self):
        self.connection.send(10)
        self.assertEqual('10', str(self.future))

    def test_future_repr_does_not_block(self):
        # Do not send anything on the connection
        repr(self.future)

    def test_future_repr_returns_a_string_which_includes_the_word_future(self):
        self.assert_('pykka.Future' in repr(self.future))

    def test_future_get_can_timeout_and_return_none(self):
        # Do not send anything on the connection
        self.assertEqual(None, self.future.get(timeout=0.1))

    def test_future_get_can_timeout_immediately(self):
        # Do not send anything on the connection
        self.assertEqual(None, self.future.get(timeout=False))
