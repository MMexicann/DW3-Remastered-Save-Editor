"""Bounded, read-only classification of observed PSP Special export envelopes.

This independently written parser checks public product metadata and structural
declarations only. It does not authenticate PSP MACs, decrypt DATA.BIN, validate
game-layer integrity, or establish a playable save. No private metadata is
returned or included in errors. See docs/PSP_SPECIAL_RESEARCH.md for evidence.
"""
from dataclasses import dataclass
import struct


class EnvelopeError(ValueError):
    """The selected observed envelope profile was not structurally matched."""


@dataclass(frozen=True)
class EnvelopeProfile:
    id: str
    title: str
    directory: str
    data_size: int


# Exact observations, not inferred slot patterns or compatibility rules.
PROFILES = (
    EnvelopeProfile('dw6special_psp', '真・三國無双５ Special',
                    'ULJM055240000', 168592),
    EnvelopeProfile('dw7special_psp', '真・三國無双6 Special',
                    'ULJM05938SAVEDATA08', 297481),
    EnvelopeProfile('sw3zspecial_psp', '戦国無双３ Z Special',
                    'ULJM06024SAVEDATA00', 159792),
)


@dataclass(frozen=True)
class EnvelopeInspection:
    profile_id: str
    product_title: str
    savedata_directory: str
    secure_filename: str
    encrypted_file_size: int
    sfo_size: int
    secure_flag: int
    envelope_authenticated: bool = False
    payload_layout_verified: bool = False


def _reject():
    # Never echo player-controlled keys, strings, paths, hashes, or values.
    raise EnvelopeError('PSP Special envelope does not match the selected observed profile.')


def _sfo_fields(raw):
    """Return bounded local slices; only the caller's whitelist can escape."""
    if not isinstance(raw, bytes) or len(raw) != 4912:
        _reject()
    magic, version, keys_start, data_start, count = struct.unpack_from('<4sIIII', raw)
    if magic != b'\x00PSF' or version != 0x101 or not 1 <= count <= 64:
        _reject()
    index_end = 20 + count * 16
    if not index_end <= keys_start < data_start <= len(raw):
        _reject()
    fields = {}
    allocations = []
    key_ranges = []
    for index in range(count):
        key_offset, kind, length, capacity, value_offset = struct.unpack_from(
            '<HHIII', raw, 20 + index * 16)
        key_begin = keys_start + key_offset
        if not keys_start <= key_begin < data_start:
            _reject()
        key_end = raw.find(b'\0', key_begin, data_start)
        if key_end < 0 or not 1 <= key_end - key_begin <= 64:
            _reject()
        key = raw[key_begin:key_end]
        if any(c not in b'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for c in key):
            _reject()
        if key in fields or any(key_begin < end and begin < key_end + 1
                                for begin, end in key_ranges):
            _reject()
        key_ranges.append((key_begin, key_end + 1))
        begin = data_start + value_offset
        end = begin + capacity
        if (kind not in (0x0004, 0x0204, 0x0404) or length > capacity
                or value_offset % 4 or not data_start <= begin <= end <= len(raw)):
            _reject()
        if kind == 0x0404 and (length != 4 or capacity != 4):
            _reject()
        if kind == 0x0204 and (length == 0 or raw[begin + length - 1] != 0):
            _reject()
        if capacity and any(begin < old_end and old_begin < end
                            for old_begin, old_end in allocations):
            _reject()
        allocations.append((begin, end))
        fields[key] = (kind, raw[begin:begin + length])
    return fields


def inspect_envelope(profile_id: str, sfo_bytes: bytes,
                     encrypted_data: bytes) -> EnvelopeInspection:
    """Inspect copies in memory without writing, decrypting, or authenticating.

    Only the exact observed slot directory, public product title, encrypted flag,
    file-list declaration and file lengths are accepted for the selected profile.
    SFO identity can be forged; a matching result is not native-save validation.
    """
    profile = next((item for item in PROFILES if item.id == profile_id), None)
    if profile is None:
        _reject()
    if not isinstance(encrypted_data, bytes) or len(encrypted_data) != profile.data_size:
        _reject()
    fields = _sfo_fields(sfo_bytes)
    required = {
        b'CATEGORY': (0x0204, b'MS\0'),
        b'SAVEDATA_DIRECTORY': (0x0204, profile.directory.encode('ascii') + b'\0'),
        b'TITLE': (0x0204, profile.title.encode('utf-8') + b'\0'),
    }
    if any(fields.get(key) != value for key, value in required.items()):
        _reject()
    params = fields.get(b'SAVEDATA_PARAMS')
    file_list = fields.get(b'SAVEDATA_FILE_LIST')
    if (params is None or params[0] != 0x0004 or len(params[1]) != 128
            or params[1][0] != 0x41 or file_list is None
            or file_list[0] != 0x0004 or len(file_list[1]) != 3168):
        _reject()
    found = False
    for offset in range(0, len(file_list[1]), 32):
        entry = file_list[1][offset:offset + 32]
        if not any(entry):
            continue
        # The PSP secure-file list has a 13-byte filename area and 16-byte MAC.
        # Reserved bytes are intentionally not interpreted or returned.
        name = entry[:13]
        terminator = name.find(b'\0')
        if (terminator < 0 or name[:terminator] != b'DATA.BIN'
                or any(name[terminator:]) or not any(entry[13:29]) or found):
            _reject()
        found = True
    if not found:
        _reject()
    return EnvelopeInspection(profile.id, profile.title, profile.directory,
                              'DATA.BIN', len(encrypted_data), len(sfo_bytes), 0x41)
