"""Read-only framing of publicly shared Spirit of Sanada PC copies.

Two gameplay copies and their system companion reproduce this outer stream and
checksum. Neither checksum nor the observed prefix authenticates a title/build.
Inner integrity, gameplay fields and existing-record ownership are unqualified.
This module is deliberately absent from the game registry and cannot edit data.
See docs/SANADA_PC_RESEARCH.md for evidence and precise remaining inputs.
"""
from dataclasses import dataclass
import struct

from koei_editor.shared.koei_codec import word_cipher, word_sum


FILE_SIZES = {"gameplay": 0x28A104, "system": 0x1004}
OBSERVED_PREFIX = (0x10, 0x65)


class FramingError(ValueError):
    """A candidate differs from the independently tested outer framing."""


@dataclass(frozen=True)
class Envelope:
    raw: bytes
    payload: bytes
    seed: int
    checksum: int
    kind: str


def inspect(raw: bytes, *, kind: str) -> Envelope:
    """Inspect the chosen file class, without claiming native title integrity.

    Selection is explicit: there is no fallback to another class or game codec.
    The checksum is only a weak 16-bit sum of decrypted little-endian words.
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise FramingError("A copied candidate must contain native bytes.")
    if not isinstance(kind, str) or kind not in FILE_SIZES:
        raise FramingError("Select the gameplay or system framing explicitly.")
    raw = bytes(raw)
    if len(raw) != FILE_SIZES[kind]:
        raise FramingError("Candidate length differs from the observed PC file class.")
    checksum, seed = struct.unpack_from("<HH", raw)
    payload = word_cipher(raw[4:], seed)
    if word_sum(payload) != checksum:
        raise FramingError("Candidate outer word checksum failed; no repair performed.")
    if struct.unpack_from("<II", payload) != OBSERVED_PREFIX:
        raise FramingError("Candidate does not have the observed shared-copy prefix.")
    return Envelope(raw, payload, seed, checksum, kind)


def unchanged_roundtrip(envelope: Envelope) -> bytes:
    """Rebuild and verify only the exact inspected copy, preserving its seed.

    Modified payloads/documents are rejected. No field writer or saving API is
    provided until title, build, inner integrity and field ownership qualify.
    """
    original = inspect(envelope.raw, kind=envelope.kind)
    if original != envelope:
        raise FramingError("Modified research envelopes cannot be serialized.")
    rebuilt = (struct.pack("<HH", envelope.checksum, envelope.seed)
               + word_cipher(envelope.payload, envelope.seed))
    if rebuilt != envelope.raw:
        raise FramingError("Candidate unchanged roundtrip differs from its source.")
    return rebuilt
