from pykka.messages import ProxyCall, ProxyGetAttr, ProxySetAttr, _ActorStop


def test_actor_stop() -> None:
    message = _ActorStop()

    assert isinstance(message, _ActorStop)


def test_proxy_call() -> None:
    message = ProxyCall(attr_path=("nested", "method"), args=(1,), kwargs={"a": "b"})

    assert isinstance(message, ProxyCall)
    assert message.attr_path == ("nested", "method")
    assert message.args == (1,)
    assert message.kwargs == {"a": "b"}


def test_proxy_get_attr() -> None:
    message = ProxyGetAttr(attr_path=("nested", "attr"))

    assert isinstance(message, ProxyGetAttr)
    assert message.attr_path == ("nested", "attr")


def test_proxy_set_attr() -> None:
    message = ProxySetAttr(attr_path=("nested", "attr"), value="abcdef")

    assert isinstance(message, ProxySetAttr)
    assert message.attr_path == ("nested", "attr")
    assert message.value == "abcdef"
