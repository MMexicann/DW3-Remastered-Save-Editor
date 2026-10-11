"""Bounded original Sigma Master Collection PC gameplay shape inspection.

Seven genuine PC gameplay copies establish the exact file size and descriptive
envelope. They do not prove a native revision marker, serializer, integrity rule
or any gameplay offsets. This module has no writable fields and never treats
generic strings or pointer-looking words as qualified title identity.
"""
from dataclasses import dataclass
import re
import struct

from koei_editor.games.dw3.models import SaveError

SIZE = 0x3AD50
PREAMBLE_SIZE = 0xA00
SOURCE_URL = ('https://gtrainers.com/load/categories/savegames/'
              'ninja_gaiden_sigma_1_savegame_all_difficulties_and_costumes_are_open/30-1-0-14091')


@dataclass(frozen=True)
class Inspection:
    raw: bytes
    native: bytes
    description_values: tuple[int, ...]
    native_prefix_words: tuple[int, ...]
    revision: None = None
    integrity_verified: bool = False
    writable: bool = False
    qualified_game_profile: bool = False


def _description(raw, start):
    region = raw[start:start + 0x100]
    end = next((at for at in range(0, len(region), 2) if region[at:at + 2] == b'\0\0'), None)
    if end is None:
        raise SaveError('Sigma PC descriptive UTF-16 string is not terminated.')
    try:
        return region[:end].decode('utf-16le')
    except UnicodeError as error:
        raise SaveError('Sigma PC descriptive UTF-16 string is malformed.') from error


def inspect(raw):
    if type(raw) is not bytes or len(raw) != SIZE:
        raise SaveError('Sigma PC gameplay inspection requires the exact 240,976-byte copied profile. '
                        'System, Survival, user settings and Sigma 2 are separate formats.')
    if _description(raw, 0) != 'Game Save':
        raise SaveError('Not the observed Sigma PC gameplay descriptive envelope.')
    description = _description(raw, 0x100)
    if not re.fullmatch(r'[0-9]+(?:\s*/\s*[0-9]+){6}', description):
        raise SaveError('The observed Sigma PC seven-value gameplay description is malformed.')
    # These integers are retained without guessing chapter/difficulty/score or
    # reward semantics. Native words at 0xA00 resemble variable addresses/tables;
    # no inventory, PS3 offsets or Sigma 2 length/revision header is transplanted.
    values = tuple(int(value.strip()) for value in description.split('/'))
    native = raw[PREAMBLE_SIZE:]
    return Inspection(raw, native, values, struct.unpack_from('<8I', native))


def encode(inspection, raw=None):
    """Only return the exact unchanged snapshot; native integrity is unresolved."""
    if (type(inspection) is not Inspection or
            type(inspection.raw) is not bytes or type(inspection.native) is not bytes or
            type(inspection.description_values) is not tuple or
            any(type(value) is not int for value in inspection.description_values) or
            type(inspection.native_prefix_words) is not tuple or
            any(type(value) is not int for value in inspection.native_prefix_words) or
            inspection.revision is not None or
            type(inspection.integrity_verified) is not bool or
            type(inspection.writable) is not bool or
            type(inspection.qualified_game_profile) is not bool or
            inspect(inspection.raw) != inspection):
        raise SaveError('A frozen unchanged Sigma PC inspection snapshot is required.')
    if raw is not None and (type(raw) is not bytes or raw != inspection.raw):
        raise SaveError('Sigma PC native integrity and gameplay fields remain unresolved; inspection-only.')
    return inspection.raw
