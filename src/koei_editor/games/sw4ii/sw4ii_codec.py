"""Independent native PC SW4-II revision 0x31A4 codec.

Static inspection of the public English v1.0 Van editor establishes the exact
native polynomial section spans; two genuine copies independently qualify the
triple-step stream and all four checksums. No external editor code is included.
SW4 DX uses a distinct stream/revision/layout. See SW4II_FORMAT.md for evidence.
"""
from functools import lru_cache
import struct

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.koei_codec import word_cipher, word_sum

SAVE_SIZE, PAYLOAD_OFFSET, PAYLOAD_SIZE = 0xC8210, 0x210, 0xC8000
REVISION = 0x31A4
CHECKSUM_OFFSETS = (4, 0xA8, 0x104E, 0x5D86E)
SECTIONS = ((8, 0xA8), (0xAC, 0xA0C), (0xA0C, 0x104E),
            (0x1052, 0xCC36), (0xCC36, 0xD92E), (0xD92E, 0x5D86E))


def checksums(payload):
    a, b, c, d, e, f = (sum(payload[start:end]) for start, end in SECTIONS)
    first = ((d + a) * b + e) & 0x7fffffff
    second = ((d + f + b) * a) & 0x7fffffff
    third = (a + b + c + d) & 0x7fffffff
    return first, second, third, (first + second + third) & 0x7fffffff


def qualify_payload(payload, integrity=True):
    if len(payload) != PAYLOAD_SIZE or struct.unpack_from('<I', payload)[0] != REVISION:
        raise SaveError('Samurai Warriors 4-II requires native PC revision 0x31A4.')
    if any(struct.unpack_from('<I', payload, 0x1052 + index * 0x8C)[0] != index
           for index in range(76)):
        raise SaveError('Samurai Warriors 4-II native officer identities are invalid.')
    if integrity and any(struct.unpack_from('<I', payload, offset)[0] != expected
                         for offset, expected in zip(CHECKSUM_OFFSETS, checksums(payload))):
        raise SaveError('Samurai Warriors 4-II gameplay section checksum failed.')


@lru_cache(maxsize=4)
def decode_envelope(raw):
    if len(raw) != SAVE_SIZE:
        raise SaveError(f'Samurai Warriors 4-II PC requires exactly {SAVE_SIZE:,} bytes.')
    checksum, seed = struct.unpack_from('<HH', raw, PAYLOAD_OFFSET - 4)
    payload = word_cipher(raw[PAYLOAD_OFFSET:], seed)
    if word_sum(payload) != checksum:
        raise SaveError('Samurai Warriors 4-II native envelope checksum failed.')
    qualify_payload(payload)
    return payload, seed


def encode_envelope(original, payload):
    old_payload, seed = decode_envelope(original)
    if payload == old_payload:
        return original
    result = bytearray(payload)
    qualify_payload(result, integrity=False)
    for offset, checksum in zip(CHECKSUM_OFFSETS, checksums(result)):
        struct.pack_into('<I', result, offset, checksum)
    payload = bytes(result)
    qualify_payload(payload)
    raw = (original[:PAYLOAD_OFFSET - 4] + struct.pack('<HH', word_sum(payload), seed)
           + word_cipher(payload, seed))
    if decode_envelope(raw)[0] != payload:
        raise SaveError('Samurai Warriors 4-II edited native verification failed.')
    return raw
