"""Exact Steam GVAS container diagnostics, independently checked on 19 copies.

Black's native ByteData contains an additional checksum. Generic GVAS parsing
does not qualify that checksum or authorize gameplay writes. The system array
is a separate native format and never uses the story layout.
"""
from dataclasses import dataclass
import struct

from koei_editor.games.dw3.models import SaveError

SAVE_CLASS = '/Script/NINJAGAIDEN2BLACK.SystemSaveData'
MAX_SIZE = 128 * 1024
STORY_SIZE = 0x8280
SYSTEM_SIZE = 0x24B0


class _Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, size):
        if size < 0 or size > len(self.data) - self.pos:
            raise SaveError('Black Steam GVAS record exceeds its bounded container.')
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def number(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self):
        size = self.number('<i')
        if size == 0 or abs(size) > 4096:
            raise SaveError('Black Steam GVAS FString length is unmapped.')
        raw = self.take(size if size > 0 else -2 * size)
        terminal = b'\0' if size > 0 else b'\0\0'
        if not raw.endswith(terminal):
            raise SaveError('Black Steam GVAS FString is not terminated.')
        try:
            result = raw[:-len(terminal)].decode('utf-8' if size > 0 else 'utf-16le')
        except UnicodeError as error:
            raise SaveError('Invalid Black Steam GVAS FString encoding.') from error
        if '\0' in result:
            raise SaveError('Embedded terminator in Black Steam GVAS FString.')
        return result


def _metadata_crc(data):
    value = 0xFFFFFFFF
    for byte in data:
        value ^= byte << 24
        for _ in range(8):
            value = ((value << 1) ^ (0x04C11DB7 if value & 0x80000000 else 0)) & 0xFFFFFFFF
    return value ^ 0xFFFFFFFF


@dataclass(frozen=True)
class Property:
    name: str
    offset: int
    size: int
    text: str | None = None


@dataclass(frozen=True)
class Inspection:
    raw: bytes
    kind: str
    byte_data: bytes
    byte_data_offset: int
    properties: tuple[Property, ...]
    native_revision: int | None
    metadata_crc_verified: bool
    unresolved_payload_checksum: int | None
    integrity_verified: bool = False
    writable: bool = False
    qualified_game_profile: bool = False


def inspect(raw):
    if type(raw) is not bytes or not 64 <= len(raw) <= MAX_SIZE:
        raise SaveError('Black Steam GVAS inspection requires a bounded native copy.')
    r = _Reader(raw)
    if r.take(4) != b'GVAS':
        raise SaveError('Black Steam GVAS magic does not match.')
    if tuple(r.number('<I') for _ in range(3)) != (3, 522, 1012):
        raise SaveError('Unmapped Black Steam GVAS serialization revision.')
    if tuple(r.number('<H') for _ in range(3)) != (5, 4, 2):
        raise SaveError('Unmapped Black Steam engine revision.')
    if r.number('<I') != 0 or r.string() != 'UE5' or r.number('<I') != 3:
        raise SaveError('Unmapped Black Steam GVAS engine/custom-version metadata.')
    if r.number('<I') != 79:
        raise SaveError('Unmapped Black Steam custom-version table length.')
    r.take(79 * 20)  # Preserve the GUID/version table; it is not an owner identifier.
    if r.string() != SAVE_CLASS or r.number('<B') != 0:
        raise SaveError('Expected the native Black Steam save class and serialization control.')
    properties = []
    byte_data = None
    byte_offset = None
    while True:
        name = r.string()
        if name == 'None':
            break
        if name not in ('Title', 'Subtitle', 'Detail', 'ByteData') or name in [p.name for p in properties]:
            raise SaveError('Unmapped or duplicate Black Steam GVAS property.')
        typ = r.string()
        children = r.number('<I')
        if name == 'ByteData':
            if (typ, children) != ('ArrayProperty', 1) or r.string() != 'ByteProperty' or r.number('<I') != 0:
                raise SaveError('Black Steam ByteData must be a native byte array.')
        elif (typ, children) != ('StrProperty', 0):
            raise SaveError('Black Steam description must be a native string property.')
        size = r.number('<I')
        if r.number('<B') != 0:
            raise SaveError('Unmapped Black Steam complete property-tag flags.')
        offset = r.pos
        if name == 'ByteData':
            count = r.number('<I')
            if count not in (STORY_SIZE, SYSTEM_SIZE) or size != count + 4:
                raise SaveError('Unmapped Black Steam native byte-array count/size.')
            byte_offset = r.pos
            byte_data = r.take(count)
            text = None
        else:
            text = r.string()
        if r.pos - offset != size:
            raise SaveError('Black Steam property size does not match its serialized value.')
        properties.append(Property(name, offset, size, text))
        if len(properties) > 4:
            raise SaveError('Too many Black Steam GVAS properties.')
    if r.take(4) != b'\0' * 4 or r.pos != len(raw):
        raise SaveError('Black Steam GVAS terminator/trailer does not match.')
    names = tuple(p.name for p in properties)
    if byte_data is None:
        raise SaveError('Missing Black Steam native ByteData.')
    if len(byte_data) == STORY_SIZE:
        if names != ('Title', 'Subtitle', 'Detail', 'ByteData'):
            raise SaveError('Black Steam story property sequence does not match.')
        if not properties[0].text.startswith('Saved Game / CHAPTER '):
            raise SaveError('Expected Black Steam story description.')
        if struct.unpack_from('<II', byte_data) != (STORY_SIZE, 6):
            raise SaveError('Unmapped Black Steam native story length/revision.')
        if struct.unpack_from('<I', byte_data, 0xC)[0] != _metadata_crc(byte_data[0x10:0x1C]):
            raise SaveError('Black Steam native metadata CRC does not match.')
        revision, verified = 6, True
        checksum = struct.unpack_from('<I', byte_data, 0x14)[0]
        kind = 'story'
    else:
        if names != ('Title', 'ByteData') or properties[0].text != 'System Preferences':
            raise SaveError('Black Steam system property sequence/description does not match.')
        kind, revision, verified, checksum = 'system', None, False, None
    return Inspection(raw, kind, byte_data, byte_offset, tuple(properties), revision, verified, checksum)


def encode(inspection, raw=None):
    """Keep all GVAS metadata, native seeds and byte-array values byte-exact."""
    if (type(inspection) is not Inspection or type(inspection.raw) is not bytes
            or type(inspection.byte_data) is not bytes or type(inspection.byte_data_offset) is not int
            or type(inspection.kind) is not str
            or type(inspection.native_revision) not in (int, type(None))
            or type(inspection.unresolved_payload_checksum) not in (int, type(None))
            or any(type(getattr(inspection, flag)) is not bool for flag in
                   ('metadata_crc_verified', 'integrity_verified', 'writable', 'qualified_game_profile'))
            or type(inspection.properties) is not tuple
            or any(type(prop) is not Property or type(prop.name) is not str
                   or type(prop.offset) is not int or type(prop.size) is not int
                   or type(prop.text) not in (str, type(None)) for prop in inspection.properties)
            or inspect(inspection.raw) != inspection):
        raise SaveError('Black Steam inspection snapshot changed after parsing.')
    if raw is not None and (type(raw) is not bytes or raw != inspection.raw):
        raise SaveError('Black Steam native integrity remains unresolved; this module is inspection-only.')
    return inspection.raw
