import unittest

from pykka import Actor

class ProxyDirTest(unittest.TestCase):
    def setUp(self):
        class ActorWithAttributesAndCallables(Actor):
            foo = 'bar'
            def __init__(self):
                super(ActorWithAttributesAndCallables, self).__init__()
                self.baz = 'quox'
            def func(self):
                pass
        self.actor = ActorWithAttributesAndCallables.start()

    def tearDown(self):
        self.actor.stop()

    def test_dir_on_proxy_lists_attributes_of_the_actor(self):
        result = dir(self.actor)
        self.assert_('foo' in result)
        self.assert_('baz' in result)
        self.assert_('func' in result)

    def test_dir_on_proxy_lists_private_attributes_of_the_proxy(self):
        result = dir(self.actor)
        self.assert_('__class__' in result)
        self.assert_('__dict__' in result)
        self.assert_('__getattr__' in result)
        self.assert_('__setattr__' in result)


class ProxySendMessageTest(unittest.TestCase):
    def setUp(self):
        class ActorWithCustomReact(Actor):
            received_messages = []
            def react(self, message):
                self.received_messages.append(message)
        self.actor = ActorWithCustomReact.start()

    def tearDown(self):
        self.actor.stop()

    def test_send_on_proxy_delivers_message_to_actors_custom_react(self):
        self.actor.send({'command': 'a custom message'})
        self.assert_({'command': 'a custom message'} in
            self.actor.received_messages.get())
