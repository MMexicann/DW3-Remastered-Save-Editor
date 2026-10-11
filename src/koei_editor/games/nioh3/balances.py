"""Source-mapped balances within two explicitly qualified native tag profiles.

The historical public editor names these u64 values Amrita and Gold. Native
USER records establish their revision-specific tags, widths and neighbors.
Only deductions from opened balances are exposed; these do not perform a
purchase, level-up, reward transition or change another progression record.
"""
from dataclasses import dataclass
from functools import lru_cache
import struct

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.verified_editor import Field


@dataclass(frozen=True)
class Profile:
    amrita_tag_offset: int
    previous_tag: int

    @property
    def markers(self):
        offset = self.amrita_tag_offset
        return (
            (offset - 9, self.previous_tag, 1),
            (offset, 0x13B43052, 8),
            (offset + 0x10, 0x75AD54DF, 8),
            (offset + 0x20, 0x571E4459, 4),
            (offset + 0x2C, 0x0EE79EC8, 1),
            (offset + 0x35, 0xF73CFFDB, 8),
            (offset + 0x45, 0x80A7B9F9, 8),
        )


# Exact acquired USER revisions, not retail patch-number aliases. Later editor
# builds publish different fixed offsets and do not qualify either profile.
PROFILES = {
    0x01030001: Profile(0x3ADE1D, 0x285367E9),
    0x01040000: Profile(0x3ADE41, 0x29664BD7),
}


@lru_cache(maxsize=2)
def profile_for(payload, revision):
    if revision not in PROFILES:
        raise SaveError('Nioh 3 balances have no qualified native revision profile.')
    profile = PROFILES[revision]
    for offset, tag, length in profile.markers:
        if struct.unpack_from('<II', payload, offset) != (tag, length):
            raise SaveError('Nioh 3 native balance tags, widths or neighboring boundaries do not match the revision.')
    return profile


@lru_cache(maxsize=2)
def fields(payload, revision):
    profile = profile_for(payload, revision)
    return tuple(Field(identity, label, offset, 8,
                       int.from_bytes(payload[offset:offset + 8], 'little'),
                       'Balances', minimum=0, maxable=False)
                 for identity, label, offset in (
                     ('amrita', 'Amrita balance', profile.amrita_tag_offset + 8),
                     ('gold', 'Gold balance', profile.amrita_tag_offset + 0x18)))
