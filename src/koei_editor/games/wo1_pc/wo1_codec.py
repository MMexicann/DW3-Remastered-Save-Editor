"""Original PC revision-2 plaintext save and additive integrity.

The original period disk editor's reader/writer and two independent native
copies qualify this profile. Bytes after the checksum are opaque, not a guessed
padding requirement. See docs/WO1_PC_FORMAT.md for the evidence distinction.
"""
from koei_editor.games.dw3.models import SaveError

SAVE_SIZE = 0x24180
CHECKSUM_OFFSET = 0x24160
REVISION_OFFSET = 4
REVISION = 2


def _profile(raw):
    if type(raw) not in (bytes, bytearray) or len(raw) != SAVE_SIZE:
        raise SaveError(f'Original Warriors Orochi PC requires exactly {SAVE_SIZE:,} bytes.')
    raw = bytes(raw)
    if int.from_bytes(raw[4:6], 'little') != REVISION:
        raise SaveError('Unsupported original Warriors Orochi PC save revision.')
    return raw


def decode(raw):
    raw = _profile(raw)
    if int.from_bytes(raw[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 4], 'little') != sum(raw[:CHECKSUM_OFFSET]):
        raise SaveError('Original Warriors Orochi PC additive integrity check failed.')
    return raw


def encode(payload):
    raw = bytearray(_profile(payload))
    raw[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 4] = sum(raw[:CHECKSUM_OFFSET]).to_bytes(4, 'little')
    return decode(raw)
