"""Observed checksum relationships in one genuine base SW2 Xbox 360 export.

This diagnostic is not an identity validator, gameplay parser or save writer.
The second range's endpoint falls in zero padding in the reference input, so
its exact native coverage remains unresolved. In particular, matching these
relationships must never enable an adapter. See docs/XBOX360_EXPANSION.md.
"""
from dataclasses import dataclass

from koei_editor.games.dw3.models import SaveError

SOURCE_URL = 'https://www.xpgamesaves.com/threads/game-name-change.77900/'
OBSERVED_EXPORT_SIZE = 0xAF000
FIRST_RANGE = (4, 0x2E70)
SECOND_CANDIDATE_RANGE = (0x2E74, 0x22E9C)
CHECKSUM_OFFSETS = (0x2E70, 0x22F1C, 0x22F20)
TRAILER_OFFSET = 0x22E9C


@dataclass(frozen=True)
class Inspection:
    size: int
    observed_section_sums: tuple[int, int]
    stored_checksums: tuple[int, int, int]
    section_matches: tuple[bool, bool]
    total_matches: bool
    observed_trailer_present: bool
    complete_integrity_qualified: bool = False
    qualified_game_profile: bool = False
    editable: bool = False


def inspect(raw: bytes) -> Inspection:
    """Compare measured candidate sums without repairing or qualifying input.

    The bound is the genuine directory entry's declared length, not the CON
    package size or an assumed block allocation. Exact length is solely a
    diagnostic processing bound; it proves neither title, edition nor region.
    No account/container metadata, inferred resources or writable fields are
    returned. Bytes outside the observed ranges remain deliberately unchecked.
    """
    if type(raw) is not bytes or len(raw) != OBSERVED_EXPORT_SIZE:
        raise SaveError('SW2 Xbox 360 research requires bounded extracted candidate bytes; CON packages are excluded.')
    first = sum(raw[FIRST_RANGE[0]:FIRST_RANGE[1]]) & 0xFFFFFFFF
    second = sum(raw[SECOND_CANDIDATE_RANGE[0]:SECOND_CANDIDATE_RANGE[1]]) & 0xFFFFFFFF
    stored = tuple(int.from_bytes(raw[offset:offset + 4], 'big') for offset in CHECKSUM_OFFSETS)
    return Inspection(len(raw), (first, second), stored,
                      (stored[0] == first, stored[1] == second),
                      stored[2] == ((first + second) & 0xFFFFFFFF),
                      raw[TRAILER_OFFSET:TRAILER_OFFSET + 4] == b'\x00\x01\x02\x03')
