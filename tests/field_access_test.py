import os
import sys
import unittest

from pykka.actor import ThreadingActor


class SomeObject(object):
    baz = 'bar.baz'

    _private_field = 'secret'


class ActorWithFields(object):
    foo = 'foo'

    bar = SomeObject()
    bar.pykka_traversable = True

    _private_field = 'secret'


class FieldAccessTest(object):
    def setUp(self):
        self.actor = self.ActorWithFields()
        self.proxy = self.ActorWithFields.start().proxy()

    def tearDown(self):
        self.proxy.stop()

    def test_actor_field_can_be_read_using_get_postfix(self):
        self.assertEqual('foo', self.proxy.foo.get())

    def test_actor_field_can_be_set_using_assignment(self):
        self.assertEqual('foo', self.proxy.foo.get())
        self.proxy.foo = 'foo2'
        self.assertEqual('foo2', self.proxy.foo.get())

    def test_private_field_access_raises_exception(self):
        try:
            self.proxy._private_field.get()
            self.fail('Should raise AttributeError exception')
        except AttributeError:
            pass
        except Exception:
            self.fail('Should raise AttributeError exception')

    def test_attr_of_traversable_attr_can_be_read(self):
        self.assertEqual('bar.baz', self.proxy.bar.baz.get())

    def test_actor_get_attributes_contains_traversable_attributes(self):
        attr_paths = list(self.actor._get_attributes().keys())
        self.assert_(('foo',) in attr_paths)
        self.assert_(('bar',) in attr_paths)
        self.assert_(('bar', 'baz') in attr_paths)


class ThreadingFieldAccessTest(FieldAccessTest, unittest.TestCase):
    class ActorWithFields(ActorWithFields, ThreadingActor):
        pass


if sys.version_info < (3,) and 'TRAVIS' not in os.environ:
    from pykka.gevent import GeventActor

    class GeventFieldAccessTest(FieldAccessTest, unittest.TestCase):
        class ActorWithFields(ActorWithFields, GeventActor):
            pass
