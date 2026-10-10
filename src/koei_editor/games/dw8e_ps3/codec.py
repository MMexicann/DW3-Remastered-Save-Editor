"""Independently qualified US PS3 SYSTEM game-layer envelope.

Only already PFD-decrypted gameplay exports are accepted. This module does not
read keys or accounts and does not construct console authentication metadata.
"""
from functools import lru_cache

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.koei_codec import byte_cipher

SAVE_SIZE = 251036
PAYLOAD_SIZE = SAVE_SIZE - 1
SYSTEM_SEED = 0x14082801
REVISION = bytes.fromhex('f1280814')


def decode(raw):
    if type(raw) is not bytes or len(raw) != SAVE_SIZE:
        raise SaveError('Requires a decrypted PS3 DW8 Empires SYSTEM APP.BIN of 251,036 bytes; '
                        'campaign, native PC and encrypted console exports are separate profiles.')
    return _decode(raw)


@lru_cache(maxsize=4)
def _decode(raw):
    payload = byte_cipher(raw[:-1], SYSTEM_SEED)
    if sum(payload) & 255 != raw[-1]:
        raise SaveError('DW8 Empires PS3 SYSTEM game byte checksum mismatch.')
    if payload[:4] != REVISION:
        raise SaveError('Unsupported DW8 Empires PS3 SYSTEM title/revision.')
    return payload


def encode(payload):
    if type(payload) is not bytes or len(payload) != PAYLOAD_SIZE or payload[:4] != REVISION:
        raise SaveError('DW8 Empires PS3 SYSTEM payload size/revision must be preserved.')
    raw = byte_cipher(payload, SYSTEM_SEED) + bytes([sum(payload) & 255])
    if decode(raw) != payload:
        raise SaveError('DW8 Empires PS3 SYSTEM serialization verification failed.')
    return raw
