"""Small independently testable transport safeguards."""
import base64
import binascii


def decode_audio(value: str) -> bytes:
    if not isinstance(value, str) or len(value) > 44000:
        raise ValueError("Audio frame too large")
    try:
        audio = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid audio frame") from exc
    if not audio or len(audio) % 2:
        raise ValueError("Expected PCM16 audio")
    return audio


class OutputGate:
    """Never release model audio before retrieval, including after barge-in."""
    def __init__(self):
        self.grounded = False
        self.interrupted = False
        self.active = False

    def interrupt(self):
        self.grounded = False
        self.interrupted = self.active

    def finish(self):
        self.grounded = False
        self.interrupted = False
        self.active = False

    def retrieved(self, has_sources):
        if not self.interrupted:
            self.grounded = bool(has_sources)
            self.active = True

    @property
    def allows_audio(self):
        return self.grounded and not self.interrupted
