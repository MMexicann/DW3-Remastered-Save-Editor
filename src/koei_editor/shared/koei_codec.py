"""Independently implemented word and byte save ciphers; no format probing.

The algorithms and known-answer evidence are recorded in KOEI_FORMATS.md.
These functions are deliberately unaware of gameplay fields and game identity.
"""
from functools import lru_cache
import struct


def word_sum(data):
    if len(data) % 2:
        raise ValueError('Word checksum requires an even byte count.')
    return (sum(data[::2]) + (sum(data[1::2]) << 8)) & 0xffff


def mix_word(state):
    for _ in range(3):
        state = (state * 0x5b1a7851 + 0xce4e) & 0xffffffff
    return state


def word_cipher(data, seed):
    if len(data) % 4:
        raise ValueError('Word cipher requires complete words.')
    output = bytearray(data)
    for offset in range(0, len(output), 4):
        seed = mix_word(seed)
        value = struct.unpack_from('<I', output, offset)[0]
        struct.pack_into('<I', output, offset, value ^ seed)
    return bytes(output)


@lru_cache(maxsize=2)
def byte_stream(size, seed):
    output = bytearray(size)
    for offset in range(size):
        seed = (seed * 0x41c64e6d + 0x3039) & 0xffffffff
        output[offset] = (seed >> 16) & 0xff
    return bytes(output)


def byte_cipher(data, seed):
    return bytes(value ^ mask for value, mask in zip(data, byte_stream(len(data), seed)))
