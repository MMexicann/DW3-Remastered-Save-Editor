"""Native AES envelope and current F4 serialization profile.

The fingerprint authenticates the decrypted trailer, not the payload. Native
serialization has no additional checksum; see STARS_WO4_RESEARCH.md. Only the
current revision is qualified for gameplay fields. Earlier native revisions
remain available through the separate read-only research inspector.
"""
from dataclasses import dataclass, field
from functools import lru_cache
import struct

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw3.save_codec import CNG_AES

SYSTEM_PAYLOAD_SIZE, SLOT_PAYLOAD_SIZE = 0x79B66, 0x78E41
SYSTEM_BLOCK_SIZE, SLOT_BLOCK_SIZE, SLOT_COUNT = 0x79B84, 0x78E64, 9
SAVE_SIZE = SYSTEM_BLOCK_SIZE + SLOT_COUNT * SLOT_BLOCK_SIZE
PAYLOAD_SIZE = SYSTEM_PAYLOAD_SIZE + SLOT_COUNT * SLOT_PAYLOAD_SIZE
REVISION = 0x170302F4
SENTINEL = b'FingerPrint01234'
KEY_SEEDS = (0x27C6BAFB, 0xB3C7CC4C, 0x899930C6, 0x7242DA7E, 0x77318BB8,
             0x9223B091, 0x7E031D1B, 0x37439CE5, 0xFF8F999F, 0x3A211944)


def _lcg_bytes(seed, multiplier, increment, shift):
    output = bytearray()
    for _ in range(16):
        seed = (seed * multiplier + increment) & 0xFFFFFFFF
        output.append((seed >> shift) & 255)
    return bytes(output)


def key_for_block(index):
    if type(index) is not int or not 0 <= index <= 9:
        raise ValueError('Key index must be an integer from 0 through 9.')
    return _lcg_bytes(KEY_SEEDS[index], 0x343FD, 0x269EC3, 24)


def iv_from_seed(seed):
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError('IV seed must be an unsigned DWORD.')
    return _lcg_bytes(seed, 0x15A4E35, 1, 16)


@dataclass(frozen=True)
class Block:
    index: int
    file_offset: int
    iv_seed: int
    payload: bytes = field(repr=False)
    padding: bytes = field(repr=False)


def _raw_bytes(raw):
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise SaveError('All-Stars input must be a byte buffer.')
    if isinstance(raw, memoryview) and (raw.ndim != 1 or raw.itemsize != 1):
        raise SaveError('All-Stars input requires a one-dimensional byte buffer.')
    if len(raw) != SAVE_SIZE:
        raise SaveError('Unsupported All-Stars PC file size; expected 4,955,400 bytes.')
    return bytes(raw)


def inspect_envelope(raw):
    """Decode ten native blocks without asserting gameplay revision support."""
    raw = _raw_bytes(raw)
    blocks = []
    with CNG_AES('CBC') as aes:
        for position in range(10):
            index = 9 if position == 0 else position - 1
            offset = 0 if position == 0 else SYSTEM_BLOCK_SIZE + index * SLOT_BLOCK_SIZE
            size = SYSTEM_BLOCK_SIZE if position == 0 else SLOT_BLOCK_SIZE
            payload_size = SYSTEM_PAYLOAD_SIZE if position == 0 else SLOT_PAYLOAD_SIZE
            seed = struct.unpack_from('<I', raw, offset + size - 4)[0]
            plain = aes.transform(raw[offset:offset + size - 4], key_for_block(index),
                                  direction='decrypt', iv=iv_from_seed(seed))
            if plain[-16:] != SENTINEL:
                raise SaveError(f'All-Stars encrypted fingerprint failed for block {index}.')
            blocks.append(Block(index, offset, seed, plain[:payload_size],
                                plain[payload_size:-16]))
    return tuple(blocks)


def validate_payload(payload):
    if type(payload) is not bytes or len(payload) != PAYLOAD_SIZE:
        raise SaveError('A complete immutable All-Stars serialized payload is required.')
    revision, selected, secondary = struct.unpack_from('<3I', payload)
    if revision != REVISION:
        raise SaveError('Only the qualified current All-Stars PC revision 0x170302F4 is writable.')
    if selected > 8 or secondary > 8:
        raise SaveError('Unsupported All-Stars campaign selection in the native header.')


@lru_cache(maxsize=4)
def _decode(raw):
    blocks = inspect_envelope(raw)
    payload = b''.join(block.payload for block in blocks)
    validate_payload(payload)
    return payload, blocks


def decode(raw):
    return _decode(_raw_bytes(raw))


def encode(original_raw, payload):
    """Preserve original seeds, padding and every unmodified encrypted block."""
    original, blocks = decode(original_raw)
    validate_payload(payload)
    if payload == original:
        return bytes(original_raw)
    output, cursor = bytearray(), 0
    with CNG_AES('CBC') as aes:
        for block in blocks:
            size = len(block.payload)
            changed = payload[cursor:cursor + size]
            if changed == block.payload:
                encrypted_size = SYSTEM_BLOCK_SIZE if block.index == 9 else SLOT_BLOCK_SIZE
                output.extend(original_raw[block.file_offset:block.file_offset + encrypted_size])
            else:
                output.extend(aes.transform(changed + block.padding + SENTINEL,
                                            key_for_block(block.index), direction='encrypt',
                                            iv=iv_from_seed(block.iv_seed)))
                output.extend(struct.pack('<I', block.iv_seed))
            cursor += size
    return bytes(output)
