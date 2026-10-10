"""Native revision-2 plaintext envelope and 20-byte integrity record.

The native loader verifies the byte sum and all sixteen integrity padding bytes.
The final sixteen opaque bytes lie outside that check and are preserved. No game
code or distributed player save is included. See docs/OROCHI_RESEARCH.md.
"""
from koei_editor.games.dw3.models import SaveError

SAVE_SIZE = 0x25F48
CHECKSUM_OFFSET = 0x25F24
INTEGRITY_SIZE = 20
REVISION_OFFSET = 4
REVISION = 2
MARKER_OFFSET = 8
MARKER = 3000


def _profile(raw):
    if type(raw) not in (bytes, bytearray) or len(raw) != SAVE_SIZE:
        raise SaveError(f'Warriors Orochi Z requires exactly {SAVE_SIZE:,} bytes.')
    raw = bytes(raw)
    if int.from_bytes(raw[4:6], 'little') != REVISION:
        raise SaveError('Unsupported Warriors Orochi Z save revision.')
    if int.from_bytes(raw[8:12], 'little') != MARKER:
        raise SaveError('The native Warriors Orochi Z layout marker is missing.')
    return raw


def decode(raw):
    raw = _profile(raw)
    integrity = raw[CHECKSUM_OFFSET:CHECKSUM_OFFSET + INTEGRITY_SIZE]
    if integrity[4:] != bytes(16):
        raise SaveError('Warriors Orochi Z integrity padding failed.')
    if int.from_bytes(integrity[:4], 'little') != sum(raw[:CHECKSUM_OFFSET]):
        raise SaveError('Warriors Orochi Z byte-sum integrity check failed.')
    return raw


def encode(payload):
    raw = bytearray(_profile(payload))
    raw[CHECKSUM_OFFSET:CHECKSUM_OFFSET + INTEGRITY_SIZE] = (
        sum(raw[:CHECKSUM_OFFSET]).to_bytes(4, 'little') + bytes(16))
    return decode(bytes(raw))
