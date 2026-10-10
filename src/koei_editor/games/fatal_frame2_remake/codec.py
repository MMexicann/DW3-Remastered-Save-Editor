"""FF2 remake revision 0x24121300; independently qualified native envelopes.

Cipher/checksum facts: MIT KatanaSaveDataResigner 4c90a2b, Ff2CbrFile.cs.
Reuse attributed project primitives, never the upstream dummy as native evidence.
Native Steam system and gameplay copies independently match both checksums.
"""
from functools import lru_cache
import hmac
import struct

from koei_editor.research.katana import katana_codec as katana

HEADER_SIZE = 0x100
JSON_OFFSET = 0x110
REVISION = 0x24121300
SYSTEM_SIZE = 61851984
GAMEPLAY_SIZE = 9318960
MAX_FILE_SIZE = SYSTEM_SIZE
DATA_CHECKSUM = 0x50
HEADER_CHECKSUM = 0x70


def checksum(data):
    """Same seven modulo-16-bit lanes; bulk sums avoid per-byte Python work."""
    lane4 = [sum(data[i::4]) for i in range(4)]
    alternating = sum(sum(data[i::8]) for i in range(4))
    total = sum(lane4)
    lanes = [total, alternating, total - alternating, *lane4]
    result = bytearray(32)
    struct.pack_into('<7H', result, 0, *(value & 0xffff for value in lanes))
    for index in range(31):
        result[index + 1] = (result[index + 1] + 2 * index + result[index]) & 255
    table = katana._CHECKSUM_TABLE
    return bytes((table[32 + value] + table[index]) & 255 for index, value in enumerate(result))


def _validate_header(raw):
    if type(raw) is not bytes or len(raw) not in (SYSTEM_SIZE, GAMEPLAY_SIZE):
        raise ValueError('Requires a complete observed native Steam FF2 remake system or gameplay copy.')
    expected_size = {b'WLNSYS\0\0': SYSTEM_SIZE, b'WLNUSR\0\0': GAMEPLAY_SIZE}.get(raw[:8])
    if expected_size != len(raw) or struct.unpack_from('<I', raw, 8)[0] != REVISION:
        raise ValueError('Wrong title/revision or system/gameplay framing.')
    if struct.unpack_from('<II', raw, 0x14) != (HEADER_SIZE, len(raw) - HEADER_SIZE):
        raise ValueError('FF2 remake header/body lengths do not match.')
    header = bytearray(raw[:HEADER_SIZE])
    expected = bytes(header[HEADER_CHECKSUM:HEADER_CHECKSUM + 32])
    header[HEADER_CHECKSUM:HEADER_CHECKSUM + 32] = bytes(32)
    if not hmac.compare_digest(expected, checksum(header)):
        raise ValueError('FF2 remake native header checksum is invalid.')


@lru_cache(maxsize=2)
def decode(raw):
    _validate_header(raw)
    encrypted = raw[8:16] != raw[HEADER_SIZE:HEADER_SIZE + 8]
    if not encrypted:
        raise ValueError('Select the native encrypted Steam copy, not a decrypted intermediary.')
    body = katana._cbc(raw[HEADER_SIZE:], katana._WOLONG_KEY, katana._WOLONG_IV, 'decrypt')
    if body[:8] != raw[8:16]:
        raise ValueError('FF2 remake inner revision pattern is invalid.')
    if not hmac.compare_digest(raw[DATA_CHECKSUM:DATA_CHECKSUM + 32], checksum(body)):
        raise ValueError('FF2 remake native body checksum is invalid.')
    return raw[:HEADER_SIZE], body


def encode(header, body):
    result = bytearray(header)
    result[DATA_CHECKSUM:DATA_CHECKSUM + 32] = checksum(body)
    result[HEADER_CHECKSUM:HEADER_CHECKSUM + 32] = bytes(32)
    result[HEADER_CHECKSUM:HEADER_CHECKSUM + 32] = checksum(result)
    return bytes(result) + katana._cbc(body, katana._WOLONG_KEY, katana._WOLONG_IV, 'encrypt')
