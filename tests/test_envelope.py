import re
import time

from pykka._envelope import Envelope


def test_envelope_repr():
    current_time = time.monotonic()
    delay = 10
    envelope = Envelope("message", reply_to=123, delay=delay)
    match = re.match(
        r"Envelope\(message='message', reply_to=123, timestamp=([\d\.]+)\)",
        repr(envelope),
    )

    assert match is not None
    # there will be some difference, execution takes time
    assert abs(float(match.group(1)) - current_time - delay) < 0.1
