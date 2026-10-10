"""Sample-qualified DW8 Empires PS3 decrypted-export codecs, without an editor.

The US SYSTEM and EMPIRE exports have different encryption at the game layer.
PS3 PFD encryption/signing remains outside this module. Published cipher facts
are independently implemented using the common byte cipher; see PS3_EXPANSION.
No runtime address is used as a serialized resource label or gameplay mapping.
"""
from dataclasses import dataclass

from koei_editor.shared.koei_codec import byte_cipher

REVISION = bytes.fromhex('f1280814')
SYSTEM_SIZE = 251036
EMPIRE_SIZE = 1091800
SYSTEM_SEED = 0x14082801
SIZES = {'system': SYSTEM_SIZE, 'empire': EMPIRE_SIZE}
SAMPLE_VERIFIED = True


@dataclass(frozen=True)
class Document:
    raw: bytes
    payload: bytes
    kind: str


@dataclass(frozen=True)
class ResourceCandidate:
    """Observed physical row; owner and second/third labels remain unresolved."""
    slot: int
    ordinal: int
    raw_prefix_flag: int
    candidate_materials: int
    second_value: int
    third_value: int
    editable: bool = False


def _kind(kind):
    if type(kind) is not str or kind not in SIZES:
        raise ValueError('Choose the explicit US PS3 system or empire profile.')


def decode(raw, *, kind):
    """Decode already PFD-decrypted bytes; refuse native PC envelope sizes."""
    _kind(kind)
    if type(raw) is not bytes or len(raw) != SIZES[kind]:
        raise ValueError('Unsupported DW8 Empires US PS3 decrypted-export size.')
    if kind == 'system':
        payload = byte_cipher(raw[:-1], SYSTEM_SEED)
        if (sum(payload) & 0xFF) != raw[-1]:
            raise ValueError('DW8 Empires PS3 SYSTEM byte checksum mismatch.')
    else:
        payload = raw
    if payload[:4] != REVISION:
        raise ValueError('Unsupported DW8 Empires PS3 title revision.')
    return Document(raw, payload, kind)


def validate_document(document):
    if (type(document) is not Document or type(document.raw) is not bytes
            or type(document.payload) is not bytes or type(document.kind) is not str):
        raise ValueError('An immutable DW8 Empires PS3 research snapshot is required.')
    if decode(document.raw, kind=document.kind).payload != document.payload:
        raise ValueError('The decoded research snapshot was changed.')


def encode(document, payload=None):
    """Research bytes only; no gameplay stage, Max, save or filesystem API."""
    validate_document(document)
    if payload is None or payload == document.payload and type(payload) is bytes:
        return document.raw
    if (type(payload) is not bytes or len(payload) != len(document.payload)
            or payload[:4] != REVISION):
        raise ValueError('Research serialization preserves the payload size and revision.')
    raw = (byte_cipher(payload, SYSTEM_SEED) + bytes([sum(payload) & 0xFF])
           if document.kind == 'system' else payload)
    if decode(raw, kind=document.kind).payload != payload:
        raise ValueError('DW8 Empires PS3 research serialization verification failed.')
    return raw


def resource_candidates(document):
    """Inspect source-proposed 40-row array without inventing owner semantics."""
    validate_document(document)
    if document.kind != 'empire':
        return ()
    rows = []
    for index in range(40):
        offset = 0x5BF4 + index * 0xE4
        data = document.payload
        rows.append(ResourceCandidate(
            index, int.from_bytes(data[offset - 6:offset - 4], 'little'),
            int.from_bytes(data[offset - 2:offset], 'little'),
            *(int.from_bytes(data[offset + delta:offset + delta + 4], 'little')
              for delta in (0, 4, 8))))
    return tuple(rows)
