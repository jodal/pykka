from pykka._envelope import Envelope


def test_envelope_repr():
    envelope = Envelope('message', reply_to=123)

    assert repr(envelope) == "Envelope(message='message', reply_to=123)"
