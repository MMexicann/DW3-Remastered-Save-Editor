"""Qualified native-PC SystemSave envelope; no campaign/profile fallback.

Both native checksum layers, title/revision and exact native size are qualified
against a privately held public SystemSave. The original seed and opaque header
are preserved. Cipher facts are independently implemented using shared primitives.
"""
from functools import lru_cache
import struct

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.koei_codec import byte_cipher, word_cipher, word_sum

SAVE_SIZE = 244952
PAYLOAD_SIZE = 243915
BODY_OFFSET, CHECKSUM_OFFSET, SEED_OFFSET = 0x40C, 0x408, 0x40A
SYSTEM_SEED = 0x14082801
REVISION = bytes.fromhex('f1280814')


def freeze(raw):
    if type(raw) not in (bytes, bytearray, memoryview):
        raise SaveError('DW8 Empires native SYSTEM requires byte data.')
    length = raw.nbytes if type(raw) is memoryview else len(raw)
    if length != SAVE_SIZE:
        raise SaveError('Requires native PC DW8 Empires SystemSave.dat of 244,952 bytes.')
    return raw.tobytes() if type(raw) is memoryview else bytes(raw)


@lru_cache(maxsize=4)
def _decode(raw):
    checksum, seed = struct.unpack_from('<HH', raw, CHECKSUM_OFFSET)
    body = word_cipher(raw[BODY_OFFSET:], seed)
    if word_sum(body) != checksum:
        raise SaveError('DW8 Empires SYSTEM outer checksum failed.')
    payload = byte_cipher(body[:-1], SYSTEM_SEED)
    if (sum(payload) & 255) != body[-1]:
        raise SaveError('DW8 Empires SYSTEM inner byte checksum failed.')
    if payload[:4] != REVISION:
        raise SaveError('Unsupported DW8 Empires SYSTEM title/revision.')
    return payload, seed


def decode(raw):
    return _decode(freeze(raw))


def encode(payload, original):
    frozen = freeze(original)
    old_payload, seed = _decode(frozen)
    if type(payload) is not bytes or len(payload) != PAYLOAD_SIZE or payload[:4] != REVISION:
        raise SaveError('Preserve the native DW8 Empires SYSTEM payload size and revision.')
    if payload == old_payload:
        return frozen
    body = byte_cipher(payload, SYSTEM_SEED) + bytes([sum(payload) & 255])
    header = bytearray(frozen[:BODY_OFFSET])
    struct.pack_into('<H', header, CHECKSUM_OFFSET, word_sum(body))
    raw = bytes(header) + word_cipher(body, seed)
    if decode(raw) != (payload, seed):
        raise SaveError('DW8 Empires SYSTEM edited envelope verification failed.')
    return raw
