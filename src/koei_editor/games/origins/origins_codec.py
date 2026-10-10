"""Native Origins Steam save envelope, independently implemented.

Build 21711288 reader/writer evidence is documented in ORIGINS_FORMAT.md.
Envelope integrity is a weak 16-bit word sum, not game/schema authentication.
The gameplay parser must separately qualify the decrypted payload's identity.
"""
from __future__ import annotations

from array import array
from dataclasses import dataclass
import struct
import sys

from koei_editor.shared.koei_codec import word_sum


SLOT_FILE_SIZE = 0x271664
USER_FILE_SIZE = 0x2804
FILE_SIZES = {"slot": SLOT_FILE_SIZE, "user": USER_FILE_SIZE}
HEADER_SIZE = 4
STEPS = 1


class SaveFormatError(ValueError):
    """A native envelope has invalid length, parameters, or integrity."""


@dataclass(frozen=True)
class Envelope:
    payload: bytes
    seed: int
    checksum: int
    kind: str
    steps: int = STEPS


def word_cipher(data: bytes, seed: int) -> bytes:
    """Apply the reversible PC word stream; no asset-key or format probing."""
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 0xffff:
        raise SaveFormatError("Origins seed must be an unsigned 16-bit integer.")
    if len(data) % 4:
        raise SaveFormatError("Origins cipher requires complete 32-bit words.")
    words = array("I")
    words.frombytes(bytes(data))
    if sys.byteorder != "little":
        words.byteswap()
    state = seed
    for index, value in enumerate(words):
        state = (state * 0x5b1a7851 + 0xce4e) & 0xffffffff
        words[index] = value ^ state
    if sys.byteorder != "little":
        words.byteswap()
    return words.tobytes()


def _kind_for_size(size: int, kind: str | None) -> str:
    if kind is not None:
        if kind not in FILE_SIZES:
            raise SaveFormatError("Unknown Origins save envelope kind.")
        if size != FILE_SIZES[kind]:
            raise SaveFormatError(f"Origins {kind} envelope has an invalid length.")
        return kind
    for candidate, expected in FILE_SIZES.items():
        if size == expected:
            return candidate
    raise SaveFormatError("Unsupported Origins envelope length.")


def decode(raw: bytes, kind: str | None = None) -> Envelope:
    """Validate native size and checksum, then return immutable decoded bytes."""
    raw = bytes(raw)
    kind = _kind_for_size(len(raw), kind)
    checksum, seed = struct.unpack_from("<HH", raw)
    payload = word_cipher(raw[HEADER_SIZE:], seed)
    if word_sum(payload) != checksum:
        raise SaveFormatError("Origins envelope checksum mismatch.")
    return Envelope(payload, seed, checksum, kind)


def encode(payload: bytes, seed: int, kind: str, steps: int = STEPS) -> bytes:
    """Encode a qualified payload with its original seed and native integrity."""
    if isinstance(steps, bool) or not isinstance(steps, int) or steps != STEPS:
        raise SaveFormatError("Only the verified Origins Steam cipher is supported.")
    payload = bytes(payload)
    _kind_for_size(len(payload) + HEADER_SIZE, kind)
    checksum = word_sum(payload)
    encrypted = word_cipher(payload, seed)
    return struct.pack("<HH", checksum, seed) + encrypted
