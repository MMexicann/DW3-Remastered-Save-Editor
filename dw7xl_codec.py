"""Native Windows DW7 XL Definitive Edition save envelope.

Independently recovered from the supplied SM6EN executable's save routines;
the public koko-tsuu/dw7xl_save_converter PC sample corroborates the arithmetic.
DW7 advances the word stream TWO times, unlike DW8 XL's three. The native
checksum covers complete 16-bit payload pairs, leaving the final odd byte
uncovered; no additional checksum is invented or silently repaired.
"""
import struct

from models import SaveError


SAVE_SIZE = 0x72D23
PAYLOAD_SIZE = SAVE_SIZE - 4
MAGIC = b'\x00\x02\x08\x11'


def _bytes(value, label, size):
    if type(value) not in (bytes, bytearray, memoryview):
        raise SaveError(f'{label} requires byte data.')
    actual = value.nbytes if type(value) is memoryview else len(value)
    if actual != size:
        raise SaveError(f'{label} requires exactly {size:,} bytes.')
    return value.tobytes() if type(value) is memoryview else bytes(value)


def checksum(payload):
    """Sum all complete little-endian 16-bit pairs, modulo 65536."""
    return sum(word[0] for word in struct.iter_unpack('<H', payload[:-1])) & 0xFFFF


def _cipher(payload, seed):
    result = bytearray(payload)
    state = seed
    end = len(payload) - len(payload) % 4
    for offset in range(0, end, 4):
        state = (state * 0x5B1A7851 + 0xCE4E) & 0xFFFFFFFF
        state = (state * 0x5B1A7851 + 0xCE4E) & 0xFFFFFFFF
        word = struct.unpack_from('<I', payload, offset)[0] ^ state
        struct.pack_into('<I', result, offset, word)
    # The native trailing-byte loop restarts from the ORIGINAL seed's low byte,
    # independently of the preceding word loop's final state.
    tail = seed & 0xFF
    for offset in range(end, len(payload)):
        tail = ((tail * 0x51 + 0x4E) * 0x51 + 0x4E) & 0xFF
        result[offset] ^= tail
    return bytes(result)


def decode(raw):
    """Validate the native size, word checksum and serialized version marker."""
    raw = _bytes(raw, 'DW7 XL Definitive Edition PC save', SAVE_SIZE)
    expected, seed = struct.unpack_from('<HH', raw)
    payload = _cipher(raw[4:], seed)
    if checksum(payload) != expected:
        raise SaveError('DW7 XL PC word checksum failed.')
    if payload[:4] != MAGIC:
        raise SaveError('Unsupported DW7 XL PC title/revision marker.')
    return payload, seed


def encode(payload, seed):
    """Encode a qualified same-size payload, retaining the opened save's seed."""
    payload = _bytes(payload, 'DW7 XL PC payload', PAYLOAD_SIZE)
    if type(seed) is not int or not 0 <= seed <= 0xFFFF:
        raise SaveError('DW7 XL PC seed requires an unsigned 16-bit integer.')
    if payload[:4] != MAGIC:
        raise SaveError('Unsupported DW7 XL PC title/revision marker.')
    return struct.pack('<HH', checksum(payload), seed) + _cipher(payload, seed)
