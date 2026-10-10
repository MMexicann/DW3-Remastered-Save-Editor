"""Bounded, read-only Sigma 2 Master Collection PC story diagnostics.

The native metadata CRC is proved. The payload checksum is not: this module
must never expose writes or imply complete integrity qualification. Offsets are
specific to the PC title described by Nozomi Miyamori's public-domain notes,
independently corroborated against 31 separately held native story copies.
"""
from dataclasses import dataclass
import struct

from koei_editor.games.dw3.models import SaveError

SOURCE_URL = 'https://gist.github.com/nm004/9eabd7b94b644fd8365e503471aec6cf'
SIZE = 0x8C80
PREAMBLE_SIZE = 0xA00
NATIVE_SIZE = 0x8280
REVISION = 6


def metadata_crc(data):
    """CRC-32/BZIP2: poly 04C11DB7, init/xorout FFFFFFFF, no reflection."""
    value = 0xFFFFFFFF
    for byte in data:
        value ^= byte << 24
        for _ in range(8):
            value = ((value << 1) ^ (0x04C11DB7 if value & 0x80000000 else 0)) & 0xFFFFFFFF
    return value ^ 0xFFFFFFFF


@dataclass(frozen=True)
class Profile:
    name: str
    enabled_marker: int
    essence: int
    current_health: int
    maximum_health: int
    current_ninpo_units: int
    maximum_ninpo_units: int
    equipped_melee_id: int
    equipped_melee_level: int
    loaded_costume_id: int
    pending_costume_id: int


@dataclass(frozen=True)
class Inspection:
    raw: bytes
    native: bytes
    revision: int
    metadata_crc_verified: bool
    unresolved_payload_checksum: int
    profiles: tuple[Profile, ...]
    total_karma: int
    stage_karma: int
    stage_start_karma: int
    integrity_verified: bool = False
    writable: bool = False
    qualified_game_profile: bool = False


def inspect(raw):
    if type(raw) is not bytes or len(raw) != SIZE:
        raise SaveError('Sigma 2 PC story inspection requires the exact 35,968-byte native copy.')
    # These are descriptive strings, not a cryptographic title signature. Their
    # presence does not establish identity for another platform or edition.
    for start in (0, 0x100, 0x200):
        region = raw[start:start + 0x100]
        terminal = next((i for i in range(0, len(region), 2) if region[i:i + 2] == b'\0\0'), None)
        if terminal is None:
            raise SaveError('Sigma 2 PC descriptive UTF-16 string is not terminated.')
        try:
            text = region[:terminal].decode('utf-16le')
        except UnicodeError as error:
            raise SaveError('Invalid Sigma 2 PC descriptive UTF-16 string.') from error
        if start == 0 and not text.startswith('Saved Game / CHAPTER '):
            raise SaveError('Expected a Sigma 2 PC story description; system/foreign data is excluded.')
    native = raw[PREAMBLE_SIZE:]
    if struct.unpack_from('<II', native) != (NATIVE_SIZE, REVISION):
        raise SaveError('Unmapped Sigma 2 PC native length or revision.')
    stored = struct.unpack_from('<I', native, 0xC)[0]
    if stored != metadata_crc(native[0x10:0x1C]):
        raise SaveError('Sigma 2 PC native metadata CRC does not match.')
    profiles = []
    for name, offset in (('Ryu', 0x13F0), ('Rachel', 0x16B0), ('Ayane', 0x1970), ('Momiji', 0x1C30)):
        profiles.append(Profile(
            name, raw[offset], struct.unpack_from('<i', raw, offset + 0xB0)[0],
            *struct.unpack_from('<HH', raw, offset + 0x64),
            *struct.unpack_from('<HH', raw, offset + 0x88),
            struct.unpack_from('<H', raw, offset + 0x90)[0], raw[offset + 0x92],
            raw[offset + 0x8E], raw[offset + 0x8F],
        ))
    return Inspection(raw, native, REVISION, True, struct.unpack_from('<I', native, 0x14)[0],
                      tuple(profiles), *struct.unpack_from('<III', raw, 0x1EFC))


def encode(inspection, raw=None):
    """Permit exact no-edit copies only; do not recalculate unknown integrity."""
    if (type(inspection) is not Inspection or type(inspection.raw) is not bytes
            or type(inspection.native) is not bytes or type(inspection.revision) is not int
            or type(inspection.unresolved_payload_checksum) is not int
            or any(type(getattr(inspection, flag)) is not bool for flag in
                   ('metadata_crc_verified', 'integrity_verified', 'writable', 'qualified_game_profile'))
            or type(inspection.profiles) is not tuple
            or any(type(profile) is not Profile or type(profile.name) is not str
                   or any(type(getattr(profile, name)) is not int for name in Profile.__dataclass_fields__
                          if name != 'name') for profile in inspection.profiles)
            or any(type(getattr(inspection, name)) is not int for name in
                   ('total_karma', 'stage_karma', 'stage_start_karma'))):
        raise SaveError('Expected a Sigma 2 PC inspection snapshot.')
    checked = inspect(inspection.raw)
    if checked != inspection:
        raise SaveError('Sigma 2 PC inspection snapshot changed after parsing.')
    if raw is not None and (type(raw) is not bytes or raw != inspection.raw):
        raise SaveError('Sigma 2 PC payload checksum is unresolved; this module is inspection-only.')
    return inspection.raw
