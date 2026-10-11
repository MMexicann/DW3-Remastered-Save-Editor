"""Strict native Nioh Complete Edition PC USER inspection, without writes.

The PC revision layout and seven bypass flags are documented by pawREP's
MIT-licensed Nioh-Savedata-Decryption-Tool at commit
1127f936ccc35b0f93f16b6d94e0e860f329942f. A freely shared native USER file
independently confirms the complete size/revision and retained flag values.
Its encrypted/decrypted roundtrip is exact. None of that proves the native
integrity consumers or permits gameplay editing. Flag values are observations;
zeroing them is never offered. Nioh 2 and console editions are excluded.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import struct

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.katana import katana_codec
from koei_editor.shared.save_safety import safe_path


GAME_ID = 'nioh'
HEADER_SIZE = 0x148
USER_BODY_SIZE = 0x1F2C50
USER_SIZE = HEADER_SIZE + USER_BODY_SIZE
REVISION = 0x17091200
INTEGRITY_FLAG_OFFSETS = (
    0x16934C, 0x16938D, 0x169390, 0x1693B4, 0x1693BF, 0x17CE54, 0x1DE8DC,
)
READ_ONLY_REASON = (
    'Native Nioh PC gameplay integrity is not mapped. Inspection and unchanged '
    'roundtrips only; native integrity flags, seeds and unknown bytes are preserved.'
)


@dataclass(frozen=True)
class Document:
    raw: bytes
    payload: bytes
    encrypted: bool
    source: Path

    @property
    def writable(self):
        return False

    @property
    def integrity_verified(self):
        return False


def decode(raw, game_id=GAME_ID, source=Path('copy.bin')):
    if game_id != GAME_ID:
        raise SaveError('Select the native Nioh Complete Edition PC USER inspection profile.')
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != USER_SIZE:
        raise SaveError(f'Nioh Complete Edition PC USER requires exactly {USER_SIZE:,} bytes.')
    raw = bytes(raw)
    try:
        native = katana_codec.decode(raw, GAME_ID)
    except (ValueError, TypeError) as error:
        raise SaveError(str(error)) from error
    payload = native.payload
    if (payload[:8] != b'NIOHUSR\0' or
            struct.unpack_from('<I', payload, 8)[0] != REVISION or
            struct.unpack_from('<I', payload, HEADER_SIZE + 8)[0] != REVISION):
        raise SaveError('Nioh Complete Edition PC USER title/revision markers do not match.')
    if any(payload[offset] not in (0, 1) for offset in INTEGRITY_FLAG_OFFSETS):
        raise SaveError('Nioh PC integrity flags do not match the observed revision layout.')
    return Document(raw, payload, native.encrypted, Path(source))


def validate_document(document):
    if (not isinstance(document, Document) or type(document.raw) is not bytes or
            type(document.payload) is not bytes or type(document.encrypted) is not bool or
            not isinstance(document.source, Path)):
        raise SaveError('Nioh inspection requires an immutable opened snapshot.')
    reopened = decode(document.raw, source=document.source)
    if reopened.payload != document.payload or reopened.encrypted != document.encrypted:
        raise SaveError('The opened Nioh inspection snapshot was changed.')


def _copy_path(path):
    candidate = Path(path)
    resolved = safe_path(candidate)
    for checked in (candidate, candidate.absolute(), resolved):
        text = str(checked).replace('\\', '/').lower()
        if re.search(r'/koeitecmo/nioh(?:/|$)', text):
            raise SaveError('Inspect a separate copy outside the live Nioh save folder.')
    return resolved


def read_save(path, game_id=GAME_ID):
    source = _copy_path(path)
    if source.suffix.lower() != '.bin':
        raise SaveError('Inspect a separate native Nioh PC .bin USER save copy.')
    with source.open('rb') as stream:
        raw = stream.read(USER_SIZE + 1)
    return decode(raw, game_id, source)


def serialize(document, changes):
    validate_document(document)
    if not isinstance(changes, dict) or changes:
        raise SaveError(READ_ONLY_REASON)
    return document.raw


def fields_for(document):
    validate_document(document)
    return ()


def inspection_rows(document):
    validate_document(document)
    rows = [
        {'group': 'Format', 'label': 'Native integrity', 'value': READ_ONLY_REASON},
        {'group': 'Format', 'label': 'Observed revision', 'value': f'{REVISION:08X}'},
        {'group': 'Format', 'label': 'Representation',
         'value': 'Native encrypted' if document.encrypted else 'Native decrypted'},
        {'group': 'Format', 'label': 'Header / body bytes',
         'value': f'{HEADER_SIZE:,} / {USER_BODY_SIZE:,}'},
    ]
    rows.extend({'group': 'Integrity flags', 'label': f'Flag at 0x{offset:X}',
                 'value': f'{document.payload[offset]} (preserved)'}
                for offset in INTEGRITY_FLAG_OFFSETS)
    return tuple(rows)
