"""Sample-qualified native PC DW8 Empires envelopes, without gameplay writes.

Five public PC saves qualify the arithmetic, sizes and title revision described
in DYNASTY_RESEARCH.md. This codec is separate from the broader arithmetic-only
candidate. No adapter is registered until gameplay mappings are independently
proven. Envelope metadata before 0x408 is preserved and is not checksum covered.
"""
from dataclasses import dataclass
import struct

import koei_editor.research.dw8e.dw8e_candidate_codec as candidate


MAGIC = bytes.fromhex('f1280814')
SYSTEM_SIZE = 244952
BATTLE_SIZE = 1083236
SIZES = {'SystemSave': SYSTEM_SIZE, 'BattleSave': BATTLE_SIZE}
PC_SAMPLE_VERIFIED = True
NATIVE_IDENTITY_VERIFIED = True


def _bytes(value, label):
    if type(value) not in (bytes, bytearray, memoryview):
        raise ValueError(f'{label} requires byte data.')
    length = value.nbytes if type(value) is memoryview else len(value)
    if length not in SIZES.values():
        raise ValueError('Unsupported native PC DW8 Empires size.')
    return value.tobytes() if type(value) is memoryview else bytes(value)


@dataclass(frozen=True)
class Document:
    raw: bytes
    payload: bytes
    kind: candidate.SaveKind

    @property
    def seed(self):
        return struct.unpack_from('<H', self.raw, candidate.SEED_OFFSET)[0]


def decode(raw, *, kind):
    """Require an explicit native profile, exact size, checksums and revision."""
    candidate._validate_kind(kind)
    frozen = _bytes(raw, 'DW8 Empires save')
    if len(frozen) != SIZES[kind]:
        raise ValueError('The native PC DW8 Empires size does not match this save profile.')
    result = candidate.decode_candidate(frozen, kind=kind)
    if result.payload[:4] != MAGIC:
        raise ValueError('Unsupported native PC DW8 Empires title/revision.')
    return Document(frozen, result.payload, kind)


def validate_document(document):
    if (type(document) is not Document or type(document.raw) is not bytes
            or type(document.payload) is not bytes):
        raise ValueError('An immutable decoded native PC DW8 Empires document is required.')
    original = decode(document.raw, kind=document.kind)
    if original.payload != document.payload:
        raise ValueError('The DW8 Empires snapshot was changed outside the encoding workflow.')


def encode(document, payload=None):
    """Research serialization preserves the prefix and seed; no filesystem API."""
    validate_document(document)
    if payload is None:
        return document.raw
    if type(payload) not in (bytes, bytearray, memoryview):
        raise ValueError('Edited payload requires byte data.')
    size = payload.nbytes if type(payload) is memoryview else len(payload)
    if size != len(document.payload):
        raise ValueError('DW8 Empires serialization preserves the native payload size.')
    edited = payload.tobytes() if type(payload) is memoryview else bytes(payload)
    if edited[:4] != MAGIC:
        raise ValueError('DW8 Empires serialization preserves the qualified title/revision.')
    original = candidate.decode_candidate(document.raw, kind=document.kind)
    raw = original.encode_candidate(edited)
    if decode(raw, kind=document.kind).payload != edited:
        raise ValueError('DW8 Empires candidate serialization verification failed.')
    return raw
