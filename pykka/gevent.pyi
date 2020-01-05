import gevent.event

from pykka import Actor, Future

class GeventFuture(Future):
    async_result: gevent.event.AsyncResult

class GeventActor(Actor): ...
