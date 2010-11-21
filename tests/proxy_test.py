import unittest

from pykka import Actor

class ActorProxyTest(unittest.TestCase):
    def setUp(self):
        class ActorWithAttributesAndCallables(Actor):
            foo = 'bar'
            def __init__(self):
                super(ActorWithAttributesAndCallables, self).__init__()
                self.baz = 'quox'
            def func(self):
                pass
        self.actor = ActorWithAttributesAndCallables().start()

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
