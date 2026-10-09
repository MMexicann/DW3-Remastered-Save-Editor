"""Research-only DW8 Empires cipher candidate; native PC support is pending.

Numeric cipher observations were inspected at commit
b2e98ed254e6afc57697bf19fddf84296863dad1 of:
https://github.com/bucanero/ps3-save-decrypters/tree/b2e98ed254e6afc57697bf19fddf84296863dad1/dw8xl-decrypter/samples
The dw8e-dec.py / dw8e-enc.py notes cite:
https://www.tapatalk.com/groups/koeiwarriors/dw8e-modding-efforts-t17446-s10.html

The surrounding repository's DW8XL fixtures are PS3 saves. No genuine native
PC Empires bytes, title magic, accepted size/revision, editable gameplay fields
or game load has been validated here. Arithmetic checksum matches cannot prove
game identity, platform, or the caller's classification.

The caller must explicitly choose SystemSave (two cipher layers) or BattleSave
(outer layer only). The BattleSave classification is inferred from the source's
conditional SystemSave branch and remains unverified. Names are never inspected
and there is no automatic detection, game adapter, CLI, file reader or writer.
Encoding returns bytes for research and preserves unrelated envelope data.
"""
from dataclasses import dataclass
import struct
from typing import Literal

from koei_codec import byte_cipher, word_cipher, word_sum


BODY_OFFSET = 0x40C
CHECKSUM_OFFSET = 0x408
SEED_OFFSET = 0x40A
SYSTEM_BYTE_SEED = 0x14082801
# Resource ceiling for research input, not a verified native save size.
MAX_BYTES = 32 * 1024 * 1024
PC_SAMPLE_VERIFIED = False
NATIVE_IDENTITY_VERIFIED = False
SaveKind = Literal['SystemSave', 'BattleSave']
BytesInput = bytes | bytearray | memoryview


def _validate_kind(kind: SaveKind) -> None:
    if type(kind) is not str or kind not in ('SystemSave', 'BattleSave'):
        raise ValueError('Explicit SystemSave or BattleSave classification is required.')


def _freeze_bytes(value: BytesInput, label: str) -> bytes:
    # bytes(integer) allocates zeros and bytes(iterable) silently accepts a list.
    # Neither conversion is suitable for a purported save or edited payload.
    if type(value) not in (bytes, bytearray, memoryview):
        raise ValueError(f'{label} requires bytes, bytearray or memoryview.')
    size = value.nbytes if type(value) is memoryview else len(value)
    if size > MAX_BYTES:
        raise ValueError(f'{label} exceeds the research input limit.')
    return value.tobytes() if type(value) is memoryview else bytes(value)


def _decode_payload(raw: bytes, kind: SaveKind) -> bytes:
    _validate_kind(kind)
    if not BODY_OFFSET + 4 <= len(raw) <= MAX_BYTES:
        raise ValueError('Candidate envelope is truncated or exceeds the research input limit.')
    if (len(raw) - BODY_OFFSET) % 4:
        raise ValueError('Candidate body must contain complete four-byte words.')
    expected, seed = struct.unpack_from('<HH', raw, CHECKSUM_OFFSET)
    body = word_cipher(raw[BODY_OFFSET:], seed)
    if word_sum(body) != expected:
        raise ValueError('Candidate outer checksum mismatch.')
    if kind == 'SystemSave':
        payload = byte_cipher(body[:-1], SYSTEM_BYTE_SEED)
        if (sum(payload) & 0xFF) != body[-1]:
            raise ValueError('Candidate SystemSave byte checksum mismatch.')
        return payload
    return body


@dataclass(frozen=True)
class CandidateDocument:
    """Immutable arithmetic snapshot; it does not establish PC game identity."""
    raw: bytes
    payload: bytes
    kind: SaveKind

    @property
    def header(self) -> bytes:
        return self.raw[:BODY_OFFSET]

    def encode_candidate(self, payload: BytesInput | None = None) -> bytes:
        """Return a same-size candidate copy after checking the original snapshot.

        This exposes no gameplay field mapping and is not a production editor.
        The two checksum bytes can change; other header bytes and the original
        seed are preserved. No data is written to the filesystem.
        """
        validate_candidate_document(self)
        edited = self.payload if payload is None else _freeze_bytes(payload, 'Edited payload')
        if len(edited) != len(self.payload):
            raise ValueError('Candidate encoding preserves the original payload size.')
        if self.kind == 'SystemSave':
            body = byte_cipher(edited, SYSTEM_BYTE_SEED) + bytes([sum(edited) & 0xFF])
        else:
            body = edited
        header = bytearray(self.header)
        struct.pack_into('<H', header, CHECKSUM_OFFSET, word_sum(body))
        seed = struct.unpack_from('<H', header, SEED_OFFSET)[0]
        return bytes(header) + word_cipher(body, seed)


def decode_candidate(raw: BytesInput, *, kind: SaveKind) -> CandidateDocument:
    """Check candidate arithmetic; never infer the game or system/battle kind."""
    _validate_kind(kind)
    frozen = _freeze_bytes(raw, 'Candidate envelope')
    payload = _decode_payload(frozen, kind)
    return CandidateDocument(frozen, payload, kind)


def validate_candidate_document(document: CandidateDocument) -> None:
    """Reject forged/mutable snapshots before using their payload for encoding."""
    if type(document) is not CandidateDocument:
        raise ValueError('A decoded candidate document is required.')
    if type(document.raw) is not bytes or type(document.payload) is not bytes:
        raise ValueError('Candidate snapshots require immutable byte data.')
    original = _decode_payload(document.raw, document.kind)
    if original != document.payload:
        raise ValueError('The candidate snapshot was changed outside the encoding workflow.')
