import unittest

from pykka import ThreadingActor


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
            self.proxy._private_field.get()
            self.fail('Should raise AttributeError exception')
        except AttributeError:
            pass
        except Exception:
            self.fail('Should raise AttributeError exception')

    def test_attr_of_traversable_attr_can_be_read(self):
        self.assertEqual('bar.baz', self.proxy.bar.baz.get())


def ConcreteFieldAccessTest(actor_class):
    class C(FieldAccessTest, unittest.TestCase):

        class ActorWithFields(ActorWithFields, actor_class):
            pass
    C.__name__ = '%sFieldAccessTest' % actor_class.__name__
    return C


ThreadingFieldAccessTest = ConcreteFieldAccessTest(ThreadingActor)


try:
    from pykka.gevent import GeventActor
    GeventFieldAccessTest = ConcreteFieldAccessTest(GeventActor)
except ImportError:
    pass


try:
    from pykka.eventlet import EventletActor
    EventletFieldAccessTest = ConcreteFieldAccessTest(EventletActor)
except ImportError:
    pass
