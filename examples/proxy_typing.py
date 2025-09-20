from typing import cast, reveal_type

from pykka import ActorProxy, ThreadingActor
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method

# 1) The actor class to be proxied is defined as usual:


class CircleActor(ThreadingActor):
    pi = 3.14

    def area(self, radius: float) -> float:
        return self.pi * radius**2


# 2) In addition, a proxy class is defined, which inherits from
# ActorMemberMixin to get the correct type hints for the actor methods:


class CircleProxy(ActorMemberMixin, ActorProxy[CircleActor]):
    # For each field on the proxy, a proxy_field is defined:
    pi = proxy_field(CircleActor.pi)

    # For each method on the proxy, a proxy_method is defined:
    area = proxy_method(CircleActor.area)


# 3) The actor is started like usual, and a proxy is created as usual, but
# the proxy is casted to the recently defined proxy class:
proxy = cast("CircleProxy", CircleActor.start().proxy())


# Now, the type hints for the proxy are correct:

reveal_type(proxy.stop)
# Revealed type is 'Callable[[], pykka.Future[None]]'

reveal_type(proxy.pi)
# Revealed type is 'pykka.Future[float]'

reveal_type(proxy.area)
# Revealed type is 'Callable[[float], pykka.Future[float]]'
