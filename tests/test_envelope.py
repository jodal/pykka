from pykka import Future
from pykka._envelope import Envelope


def test_envelope_repr() -> None:
    envelope = Envelope("message", reply_to=Future())

    assert repr(envelope) == "Envelope(message='message', reply_to=<pykka.Future>)"
