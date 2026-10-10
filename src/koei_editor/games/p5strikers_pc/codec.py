"""Native PC framing independently qualified against two public player saves.

The project's original research stream primitive is reused. Its published
32-byte vector checks the LCG separately from this full-file integrity layer.
The recovered low24 state is an equivalence class, not an account identifier.
"""
from dataclasses import dataclass, field
from functools import lru_cache

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.p5s.p5s_codec import (
    PC_SIZE, PC_VERSION_BYTES, PC_SLOT_SIZE, PC_HEADER_SIZE, PC_SLOT_COUNT,
    PC_LAYOUT_MARKER, recover_unique_stream_state, transform,
)

SAVE_SIZE = PC_SIZE
INTEGRITY_KIND = 'checksum'
TRAILER_SIZE = 4
MARKER_RELATIVE = 0x938
NAME_RELATIVE, NAME_SIZE = 0x87842, 33


@dataclass(frozen=True)
class Decoded:
    payload: bytes
    state: int = field(repr=False)


def validate_payload(payload):
    if type(payload) is not bytes or len(payload) != SAVE_SIZE:
        raise SaveError('Persona 5 Strikers requires the complete native PC save size.')
    if payload[:4] != PC_VERSION_BYTES or payload[-3:] != b'\0\0\0':
        raise SaveError('Unsupported Persona 5 Strikers PC version or trailer revision.')
    selected = int.from_bytes(payload[4:8], 'little', signed=True)
    if not -1 <= selected < PC_SLOT_COUNT:
        raise SaveError('Persona 5 Strikers selected save slot is malformed.')
    for slot in range(PC_SLOT_COUNT):
        base = PC_HEADER_SIZE + slot * PC_SLOT_SIZE
        marker = int.from_bytes(payload[base + MARKER_RELATIVE:base + MARKER_RELATIVE + 4], 'little')
        if marker != PC_LAYOUT_MARKER:
            raise SaveError('Persona 5 Strikers PC slot layout is unsupported.')
    if payload[-4] != sum(payload[:-TRAILER_SIZE]) & 0xFF:
        raise SaveError('Persona 5 Strikers plaintext checksum does not match.')


@lru_cache(maxsize=4)
def _decode(raw):
    try:
        state = recover_unique_stream_state(raw[:4], PC_VERSION_BYTES)
        payload = transform(raw[:-TRAILER_SIZE], state) + raw[-TRAILER_SIZE:]
    except (TypeError, ValueError) as error:
        raise SaveError('Persona 5 Strikers PC stream could not be uniquely qualified.') from error
    validate_payload(payload)
    return Decoded(payload, state)


def decode(raw):
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != SAVE_SIZE:
        raise SaveError('Open a complete encrypted Persona 5 Strikers PC SAVEDATA.BIN copy.')
    return _decode(bytes(raw))


def encode(payload, state):
    if type(state) is not int or not 0 <= state <= 0xFFFFFF:
        raise SaveError('A qualified original Persona 5 Strikers stream state is required.')
    validate_payload(payload)
    raw = transform(payload[:-TRAILER_SIZE], state) + payload[-TRAILER_SIZE:]
    if decode(raw).payload != payload:
        raise SaveError('Persona 5 Strikers edited encrypted copy failed verification.')
    return raw


def with_checksum(payload):
    if type(payload) is not bytes or len(payload) != SAVE_SIZE:
        raise SaveError('Persona 5 Strikers edited payload has the wrong type or size.')
    return payload[:-TRAILER_SIZE] + bytes((sum(payload[:-TRAILER_SIZE]) & 0xFF,)) + payload[-3:]
