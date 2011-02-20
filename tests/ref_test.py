import gevent
import gevent.event
import unittest

from pykka.actor import Actor, ActorRef

class AnActor(Actor):
    pass


class ActorWithCustomReact(Actor):
    def __init__(self, received_message):
        self.received_message = received_message

    def react(self, message):
        if message.get('command') == 'ping':
            gevent.sleep(0.01)
            return 'pong'
        else:
            self.received_message.set(message)


class RefSendMessageTest(unittest.TestCase):
    def setUp(self):
        self.received_message = gevent.event.AsyncResult()
        self.ref = ActorWithCustomReact.start(self.received_message)

    def tearDown(self):
        self.ref.stop()

    def test_send_one_way_delivers_message_to_actors_custom_react(self):
        self.ref.send_one_way({'command': 'a custom message'})
        self.assertEqual({'command': 'a custom message'},
            self.received_message.get())

    def test_send_request_reply_blocks_until_response_arrives(self):
        result = self.ref.send_request_reply({'command': 'ping'})
        self.assertEqual('pong', result)

    def test_send_request_reply_can_timeout_if_blocked_too_long(self):
        try:
            self.ref.send_request_reply({'command': 'ping'}, timeout=0)
            self.fail('Should raise Timeout exception')
        except gevent.Timeout:
            pass

    def test_send_request_reply_can_return_future_instead_of_blocking(self):
        future = self.ref.send_request_reply({'command': 'ping'}, block=False)
        self.assertEqual('pong', future.get())


class RefReprAndStrTest(unittest.TestCase):
    def setUp(self):
        self.ref = AnActor.start()

    def tearDown(self):
        self.ref.stop()

    def test_repr_is_wrapped_in_lt_and_gt(self):
        result = repr(self.ref)
        self.assert_(result.startswith('<'))
        self.assert_(result.endswith('>'))

    def test_repr_reveals_that_this_is_a_ref(self):
        self.assert_('ActorRef' in repr(self.ref))

    def test_repr_contains_actor_class_name(self):
        self.assert_('AnActor' in repr(self.ref))

    def test_repr_contains_actor_urn(self):
        self.assert_(self.ref.actor_urn in repr(self.ref))

    def test_str_contains_actor_class_name(self):
        self.assert_('AnActor' in str(self.ref))

    def test_str_contains_actor_urn(self):
        self.assert_(self.ref.actor_urn in str(self.ref))
