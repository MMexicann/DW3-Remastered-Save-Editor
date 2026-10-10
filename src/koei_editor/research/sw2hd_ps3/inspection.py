"""Source-backed diagnostic facts, without gameplay/profile/write support.

Apollo NPJB00439.savepatch documents a money scalar and duplicated additive
checksum. The native header, exact revision/size and complete serialized layout
remain unqualified; a matching diagnostic result alone must not expose writes.
"""
from dataclasses import dataclass

from koei_editor.games.dw3.models import SaveError

SOURCE_URL = 'https://github.com/bucanero/apollo-patches/blob/main/PS3/NPJB00439.savepatch'
CHECKSUM_RANGE = (0x8, 0x36E0)  # End is exclusive.
CHECKSUM_OFFSETS = (0x36E0, 0x23790)
MONEY_OFFSET = 0x2758
MIN_CANDIDATE_SIZE = 0x23794
MAX_CANDIDATE_SIZE = 2 * 1024 * 1024  # Processing ceiling, not native size.


@dataclass(frozen=True)
class Inspection:
    size: int
    candidate_money: int
    expected_byte_sum: int
    stored_checksums: tuple[int, int]
    checksums_match: bool
    editable: bool = False
    qualified_game_profile: bool = False


def inspect(raw):
    if (type(raw) is not bytes or not MIN_CANDIDATE_SIZE <= len(raw) <= MAX_CANDIDATE_SIZE):
        raise SaveError('Source-only SW2 HD diagnostic requires bounded decrypted candidate bytes.')
    expected = sum(raw[CHECKSUM_RANGE[0]:CHECKSUM_RANGE[1]]) & 0xFFFFFFFF
    actual = tuple(int.from_bytes(raw[offset:offset + 4], 'big') for offset in CHECKSUM_OFFSETS)
    money = int.from_bytes(raw[MONEY_OFFSET:MONEY_OFFSET + 4], 'big')
    return Inspection(len(raw), money, expected, actual, actual == (expected, expected))
