"""Independently recovered SW4 DX PC envelope and revision 0x39EA integrity.

Static native writer/reader evidence and genuine sample qualification are in
SAMURAI_RESEARCH.md. The cipher is the shared Koei DWORD stream; save headers
and unknown payload bytes are retained, never synthesized by this codec.
"""
from functools import lru_cache
import struct

from koei_codec import word_sum
from origins_codec import word_cipher
from models import SaveError

SAVE_SIZE = 0xC8210
PAYLOAD_OFFSET = 0x210
PAYLOAD_SIZE = 0xC8000
REVISION = 0x39EA
SECTIONS = ((0x8, 0xEC), (0xF8, 0x858), (0x950, 0x32A),
            (0xC7E, 0x71BC), (0x7E3A, 0xD68), (0x8BA2, 0x77F34))
CHECKSUM_OFFSETS = (0x4, 0xF4, 0xC7A, 0x80AD6)


def checksums(payload):
    a, b, c, d, e, f = (sum(payload[start:start + size]) for start, size in SECTIONS)
    first = ((d + a) * b + e) & 0x7fffffff
    second = ((f + d + b) * a) & 0x7fffffff
    third = (d + c + b + a) & 0x7fffffff
    return first, second, third, (first + second + third) & 0x7fffffff


def qualify_payload(payload):
    if len(payload) != PAYLOAD_SIZE:
        raise SaveError('Samurai Warriors 4 DX gameplay payload length is invalid.')
    if struct.unpack_from('<I', payload)[0] != REVISION:
        raise SaveError('Samurai Warriors 4 DX supports native PC revision 0x39EA only; '
                        'older migrating revisions and image slots are not editable.')
    for offset, expected in zip(CHECKSUM_OFFSETS, checksums(payload)):
        if struct.unpack_from('<I', payload, offset)[0] != expected:
            raise SaveError('Samurai Warriors 4 DX gameplay section checksum failed.')
    # Native standard officer table uses 55 consecutive identities, stride 0x44.
    for index in range(55):
        if struct.unpack_from('<I', payload, 0xC7E + index * 0x44)[0] != index:
            raise SaveError('Samurai Warriors 4 DX standard officer identities do not match.')


@lru_cache(maxsize=4)
def decode_envelope(raw):
    if len(raw) != SAVE_SIZE:
        raise SaveError(f'Samurai Warriors 4 DX PC requires exactly {SAVE_SIZE:,} bytes.')
    checksum, seed = struct.unpack_from('<HH', raw, PAYLOAD_OFFSET - 4)
    payload = word_cipher(raw[PAYLOAD_OFFSET:], seed)
    # The writer sums the entire payload, including the retained nonzero tail.
    if word_sum(payload) != checksum:
        raise SaveError('Samurai Warriors 4 DX native envelope checksum failed.')
    qualify_payload(payload)
    return payload, seed


def encode_envelope(original, payload):
    old_payload, seed = decode_envelope(original)
    if payload == old_payload:
        return original
    result = bytearray(payload)
    for offset, checksum in zip(CHECKSUM_OFFSETS, checksums(result)):
        struct.pack_into('<I', result, offset, checksum)
    payload = bytes(result)
    qualify_payload(payload)
    raw = (original[:PAYLOAD_OFFSET - 4] + struct.pack('<HH', word_sum(payload), seed)
           + word_cipher(payload, seed))
    if decode_envelope(raw)[0] != payload:
        raise SaveError('Samurai Warriors 4 DX edited envelope verification failed.')
    return raw
