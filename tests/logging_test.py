import logging
import unittest

from pykka.actor import ThreadingActor
from pykka.gevent import GeventActor
from pykka.registry import ActorRegistry


class LoggingNullHandlerTest(unittest.TestCase):
    def test_null_handler_is_added_to_avoid_warnings(self):
        logger = logging.getLogger('pykka')
        handler_names = [h.__class__.__name__ for h in logger.handlers]
        self.assert_('NullHandler' in handler_names)


class ActorLoggingTest(object):
    def setUp(self):
        self.actor_proxy = self.AnActor.start().proxy()
        self.log_handler = TestLogHandler(logging.DEBUG)
        self.root_logger = logging.getLogger()
        self.root_logger.addHandler(self.log_handler)

    def tearDown(self):
        self.log_handler.close()
        ActorRegistry.stop_all()

    def test_exception_is_logged_when_returned_to_caller(self):
        try:
            self.actor_proxy.raise_exception().get()
            self.fail('Should raise exception')
        except Exception:
            pass
        self.assertEqual(1, len(self.log_handler.messages['debug']))
        log_record = self.log_handler.messages['debug'][0]
        self.assertEqual('Exception returned from %s to caller:' %
            self.actor_ref, log_record.getMessage())
        self.assertEqual(Exception, log_record.exc_info[0])
        self.assertEqual('foo', log_record.exc_info[1].message)


class TestLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record)

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }


class AnActor(object):
    def raise_exception(self):
        raise Exception('foo')


class GeventActorLoggingTest(ActorLoggingTest, unittest.TestCase):
    class AnActor(GeventActor, AnActor):
        pass


class ThreadingActorLoggingTest(ActorLoggingTest, unittest.TestCase):
    class AnActor(ThreadingActor, AnActor):
        pass
