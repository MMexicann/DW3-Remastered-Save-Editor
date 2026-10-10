"""Source-only OROCHI Z PC plaintext/integrity candidate, never registered.

The attached native executable establishes length, revision and checksum. No
independent native save has qualified title identity or gameplay semantics.
No file I/O, save repair, gameplay edits or library card is provided here.
"""
from dataclasses import dataclass

from models import SaveError

SAVE_SIZE = 0x25F48
CHECKSUM_OFFSET = 0x25F24
INTEGRITY_SIZE = 20
REVISION_OFFSET = 4
REVISION = 2


@dataclass(frozen=True)
class Candidate:
    raw: bytes
    revision: int
    checksum: int
    native_identity_verified: bool = False


def inspect(raw):
    """Validate the native routine's envelope rules without claiming title proof."""
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != SAVE_SIZE:
        raise SaveError(f'OROCHI Z PC candidate requires exactly {SAVE_SIZE:,} bytes.')
    raw = bytes(raw)
    revision = int.from_bytes(raw[REVISION_OFFSET:REVISION_OFFSET + 2], 'little')
    if revision != REVISION:
        raise SaveError('Unsupported OROCHI Z candidate revision.')
    integrity = raw[CHECKSUM_OFFSET:CHECKSUM_OFFSET + INTEGRITY_SIZE]
    checksum = int.from_bytes(integrity[:4], 'little')
    if integrity[4:] != bytes(16):
        raise SaveError('OROCHI Z candidate native integrity padding failed.')
    if checksum != sum(raw[:CHECKSUM_OFFSET]):
        raise SaveError('OROCHI Z candidate native byte-sum checksum failed.')
    return Candidate(raw, revision, checksum)


def unchanged(candidate):
    """Only a byte-exact, validated unchanged roundtrip is exposed."""
    if not isinstance(candidate, Candidate):
        raise SaveError('Expected an OROCHI Z candidate snapshot.')
    verified = inspect(candidate.raw)
    if verified != candidate:
        raise SaveError('The candidate metadata was modified externally.')
    return candidate.raw
