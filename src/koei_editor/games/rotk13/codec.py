"""Independently verified PC XIII revision-14 additive save encoding.

The header and body restart the same generator independently. This is addition,
not XOR, and is not the Switch Power Up Kit layout. See ROTK13_FORMAT.md.
"""
from functools import lru_cache
import struct

from koei_editor.games.dw3.models import SaveError

SAVE_SIZE = 0x400000
HEADER_SIZE = 0x400
REVISION = 14
MAGIC = b'SAN13 SAVEDATA\0'
CHECKSUM_OFFSET = 0x14


@lru_cache(maxsize=1)
def _stream():
    state = 0
    result = bytearray(SAVE_SIZE - HEADER_SIZE)
    for index in range(len(result)):
        state = (state * 0x41C64E6D + 0x3039) & 0xFFFFFFFF
        result[index] = (state >> 16) & 0xFF
    return bytes(result)


def header_checksum(header):
    """Native unsigned byte sum; the stored checksum itself is excluded."""
    return (sum(header[:CHECKSUM_OFFSET]) + sum(header[CHECKSUM_OFFSET + 2:HEADER_SIZE])) & 0xFFFF


def qualify_header(header):
    if (type(header) is not bytes or len(header) != HEADER_SIZE
            or header[:len(MAGIC)] != MAGIC
            or struct.unpack_from('<H', header, 0x16)[0] != REVISION):
        raise SaveError('Requires an original Windows PC XIII revision-14 campaign save.')
    if struct.unpack_from('<H', header, CHECKSUM_OFFSET)[0] != header_checksum(header):
        raise SaveError('The XIII save preview checksum is invalid; reopen an undamaged copy.')


def decode_layers(raw):
    if type(raw) is not bytes or len(raw) != SAVE_SIZE:
        raise SaveError('Requires a complete 4 MiB original PC XIII .s13 campaign copy.')
    return _decode_layers(raw)


@lru_cache(maxsize=4)
def _decode_layers(raw):
    stream = _stream()
    header = bytes((value - mask) & 0xFF for value, mask in zip(raw[:HEADER_SIZE], stream))
    qualify_header(header)
    body = bytes((value - mask) & 0xFF for value, mask in zip(raw[HEADER_SIZE:], stream))
    if struct.unpack_from('<I', body)[0] != REVISION:
        raise SaveError('The XIII body revision does not match the qualified preview.')
    return header, body


def encode_layers(header, body):
    qualify_header(header)
    if (type(body) is not bytes or len(body) != SAVE_SIZE - HEADER_SIZE
            or struct.unpack_from('<I', body)[0] != REVISION):
        raise SaveError('Requires a complete frozen XIII revision-14 body.')
    stream = _stream()
    return (bytes((value + mask) & 0xFF for value, mask in zip(header, stream))
            + bytes((value + mask) & 0xFF for value, mask in zip(body, stream)))
