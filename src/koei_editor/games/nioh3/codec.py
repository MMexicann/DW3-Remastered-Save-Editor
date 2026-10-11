"""Native Nioh 3 USER integrity and representation preservation.

Format facts were independently verified against publicly shared USER copies
from alfizari/Nioh-3-Save-Editor (Apache-2.0). The existing MIT-attributed Katana
cipher primitives supply the custom CTR transform; no external program runs.
"""
from dataclasses import dataclass
from functools import lru_cache
import struct

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.katana import katana_codec


USER_SIZE = 0x9001B0
HEADER_SIZE = 0x158
BODY_START, BODY_END = 0x190, 0x900190
CHECKSUM_SEED_OFFSET, CHECKSUM_OFFSET = BODY_END, BODY_END + 4
SUPPORTED_REVISIONS = frozenset((0x01030001, 0x01040000))


@dataclass(frozen=True)
class NativeDocument:
    raw: bytes
    payload: bytes
    revision: int
    encrypted: bool


def body_checksum(payload):
    """Fold signed native qwords, retaining the game's per-save XOR seed."""
    if not isinstance(payload, (bytes, bytearray)) or len(payload) != USER_SIZE:
        raise SaveError('Nioh 3 checksum requires a complete native USER payload.')
    seed = struct.unpack_from('<I', payload, CHECKSUM_SEED_OFFSET)[0]
    accumulator = 0
    for position in range(BODY_START, BODY_END, 0x400):
        contribution = sum(struct.unpack_from('<128q', payload, position))
        accumulator = ((accumulator + contribution) ^ seed) & 0xffffffffffffffff
    return (accumulator // 0xffffffff + (accumulator & 0xffffffff)) & 0xffffffff


def validate_plaintext(payload):
    if type(payload) is not bytes or len(payload) != USER_SIZE:
        raise SaveError('Nioh 3 PC USER data must contain exactly 0x9001B0 bytes.')
    if payload[:8] != b'RNNUSR\0\0':
        raise SaveError('Select Nioh 3 PC USER data; SYS and other titles are unsupported.')
    revision = struct.unpack_from('<I', payload, 8)[0]
    if (revision not in SUPPORTED_REVISIONS
            or struct.unpack_from('<I', payload, 0x15c)[0] != revision):
        raise SaveError('Nioh 3 native USER revision markers do not match a qualified profile.')
    if struct.unpack_from('<II', payload, 0x18) != (HEADER_SIZE, USER_SIZE - HEADER_SIZE):
        raise SaveError('Nioh 3 native header/body lengths do not match the file.')
    if struct.unpack_from('<I', payload, CHECKSUM_OFFSET)[0] != body_checksum(payload):
        raise SaveError('Nioh 3 native USER body integrity check failed.')
    return revision


@lru_cache(maxsize=2)
def _decode(raw):
    if raw[:8] == b'RNNUSR\0\0':
        return NativeDocument(raw, raw, validate_plaintext(raw), False)
    header = katana_codec._header_crypt(raw[:HEADER_SIZE])
    revision = struct.unpack_from('<I', header, 8)[0]
    if (header[:8] != b'RNNUSR\0\0' or revision not in SUPPORTED_REVISIONS
            or struct.unpack_from('<II', header, 0x18) != (HEADER_SIZE, USER_SIZE - HEADER_SIZE)):
        raise SaveError('Wrong encrypted Nioh 3 PC title, USER layout or qualified revision.')
    profile = katana_codec.Profile(HEADER_SIZE, (b'RNNUSR\0\0', b'RNNSYS\0\0'), revision,
                                  length_offset=0x18, key_offset=0x49)
    decoded = katana_codec._nioh_decrypt(raw, profile)
    # Retain wrapped keys and the eight bytes excluded from the native cipher.
    payload = header + decoded[HEADER_SIZE:-8] + raw[-8:]
    validate_plaintext(payload)
    return NativeDocument(raw, payload, revision, True)


def decode(raw):
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != USER_SIZE:
        raise SaveError('Nioh 3 PC USER data must contain exactly 0x9001B0 bytes.')
    return _decode(bytes(raw))


def encode(original_raw, payload):
    """Rebuild integrity and preserve the original header, seed and tail.

    Native encryption is XOR with an unchanged custom CTR stream. Applying the
    decoded delta to the original ciphertext preserves that stream, wrapped key
    material and excluded tail exactly. It does not create or rebind an account.
    """
    original = decode(original_raw)
    if type(payload) is not bytes or len(payload) != USER_SIZE:
        raise SaveError('Nioh 3 edits must preserve the complete native USER size.')
    if payload == original.payload:
        return original.raw
    for start, end in ((0, BODY_START), (BODY_END, CHECKSUM_OFFSET),
                       (CHECKSUM_OFFSET + 4, USER_SIZE)):
        if payload[start:end] != original.payload[start:end]:
            raise SaveError('Nioh 3 edits must preserve native identity, seeds, keys and tail.')
    result = bytearray(payload)
    struct.pack_into('<I', result, CHECKSUM_OFFSET, body_checksum(result))
    result = bytes(result)
    validate_plaintext(result)
    if original.encrypted:
        encoded = bytes(raw ^ before ^ after
                        for raw, before, after in zip(original.raw, original.payload, result))
    else:
        encoded = result
    if decode(encoded).payload != result:
        raise SaveError('Nioh 3 native re-encoding failed integrity/representation validation.')
    return encoded
