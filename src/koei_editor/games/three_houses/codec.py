"""Strict native slot framing, independently implemented from format evidence.

The export has no title magic or DLC entitlement marker. Title provenance must
come from the extraction; the selected adapter additionally checks the exact
source-backed native revision, length, NPC marker and inventory structure.
No revision migration, checksum repair or trailing-byte normalization is done.
"""
from dataclasses import dataclass

from koei_editor.games.dw3.models import SaveError

HEADER_SIZE = 12
BYTEORDER = 'little'


@dataclass(frozen=True)
class Profile:
    revision: int
    size: int
    character_stride: int
    npc_size_offset: int
    player_offset: int
    activities_offset: int
    support_count: int


# Offsets are relative to the native payload, after its 12-byte header.
PROFILES = {
    13: Profile(13, 0x2540C, 0x230, 0x89B8, 0x22AB9, 0x24981, 256),
    23: Profile(23, 0x25B2C, 0x24C, 0x9048, 0x231D9, 0x250A1, 270),
}
SAVE_SIZE = max(profile.size for profile in PROFILES.values())
CHARACTER_BASE = 0x644
CHARACTER_COUNT = 60
CONVOY_COUNT = 400
ITEM_STRIDE = 4
NPC_SIZE_MARKER = 0x19DF0


def uint(payload, offset, size):
    return int.from_bytes(payload[offset:offset + size], BYTEORDER)


def item_id(payload, offset):
    return int.from_bytes(payload[offset:offset + 2], BYTEORDER, signed=True)


def checksum(raw):
    """The native checksum covers every payload byte, including unknown data."""
    return sum(raw[HEADER_SIZE:]) & 0xFFFFFFFF


def qualify(raw):
    if type(raw) not in (bytes, bytearray) or len(raw) < HEADER_SIZE:
        raise SaveError('Three Houses requires a complete extracted slot/auto copy.')
    revision = uint(raw, 4, 4)
    profile = PROFILES.get(revision)
    if profile is None:
        raise SaveError('Unsupported Three Houses native save revision; only 13 and 23 are qualified.')
    if len(raw) != profile.size or uint(raw, 8, 4) != profile.size:
        raise SaveError('Three Houses slot length/header mismatch; system, suspend and padded exports are excluded.')
    if uint(raw, 0, 4) != checksum(raw):
        raise SaveError('Three Houses native payload checksum does not match.')
    payload = raw[HEADER_SIZE:]
    if uint(payload, profile.npc_size_offset, 4) != NPC_SIZE_MARKER:
        raise SaveError('Unsupported Three Houses NPC serialization profile.')
    count = uint(payload, 0x640, 4)
    occupied = sum(item_id(payload, index * ITEM_STRIDE) != -1 for index in range(CONVOY_COUNT))
    if count > CONVOY_COUNT or count != occupied:
        raise SaveError('Three Houses convoy count does not match its existing records.')
    for index in range(CHARACTER_COUNT):
        base = CHARACTER_BASE + index * profile.character_stride
        count = payload[base + 0x87]
        occupied = sum(item_id(payload, base + slot * ITEM_STRIDE) != -1 for slot in range(6))
        if count > 6 or count != occupied:
            raise SaveError('Three Houses held-item count does not match its character record.')
    return profile


def encode(payload, original):
    """Surgical native integrity update; no-op returns the exact opened bytes."""
    if payload == original:
        return original
    output = bytearray(payload)
    output[:4] = checksum(output).to_bytes(4, BYTEORDER)
    result = bytes(output)
    qualify(result)
    return result
