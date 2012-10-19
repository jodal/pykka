import unittest

from pykka.actor import ThreadingActor

try:
    from pykka.gevent import GeventActor
    HAS_GEVENT = True
except ImportError:
    HAS_GEVENT = False


class SomeObject(object):
    pykka_traversable = False
    baz = 'bar.baz'

    _private_field = 'secret'


class ActorWithFields(object):
    foo = 'foo'

    bar = SomeObject()
    bar.pykka_traversable = True

    _private_field = 'secret'


class FieldAccessTest(object):
    def setUp(self):
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
            # pylint: disable = W0212
            self.proxy._private_field.get()
            # pylint: enable = W0212
            self.fail('Should raise AttributeError exception')
        except AttributeError:
            pass
        except Exception:
            self.fail('Should raise AttributeError exception')

    def test_attr_of_traversable_attr_can_be_read(self):
        self.assertEqual('bar.baz', self.proxy.bar.baz.get())


class ThreadingFieldAccessTest(FieldAccessTest, unittest.TestCase):
    class ActorWithFields(ActorWithFields, ThreadingActor):
        pass


if HAS_GEVENT:
    class GeventFieldAccessTest(FieldAccessTest, unittest.TestCase):
        class ActorWithFields(ActorWithFields, GeventActor):
            pass
