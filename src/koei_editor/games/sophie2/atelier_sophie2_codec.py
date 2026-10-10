"""Published Atelier Sophie 2 Steam 1.08 codec, adapted from MIT source.

Reference: https://github.com/Tartarshia/Sophie2SaveEditor at
93d807072a852c73799394af4d32fb164841cd3e (sophie2_codec.py).
Copyright (c) 2026 Sophie2SaveEditor contributors.
License: licenses/atelier-sophie2-save-editor-MIT.txt.

Changes: bounded decompression, index validation, cached bit permutation,
streaming zero-code encoding, and preservation of decoded trailing zero bytes
and the envelope's three opaque footer bytes.
This algorithm's synthetic reference vectors are not genuine-file qualification.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from functools import lru_cache


HEADER_SIZE = 0x100
# Defensive processing bounds, not a claim about a native fixed file size.
MAX_FILE_SIZE = 16 * 1024 * 1024
MAX_DECODED_SIZE = 8 * 1024 * 1024


class SaveFormatError(ValueError):
    pass


@dataclass(frozen=True)
class EnvelopeDetails:
    seed: int
    padded_size: int
    checksum_xor: int
    checksum_sum: int
    footer: bytes


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _next_rand(multiplier: int, state: int) -> tuple[int, int]:
    state = (multiplier * state + 0x2F09) & 0xFFFFFFFF
    return state, (state >> 16) & 0x7FFF


@lru_cache(maxsize=8)
def _permutation(bit_count: int) -> tuple[int, ...]:
    pool = list(range(bit_count))
    permutation = []
    state = 0x3745D
    multiplier = 0x3B9A73C9
    while pool:
        state, value = _next_rand(multiplier, state)
        permutation.append(pool.pop(value % len(pool)))
    return tuple(permutation)


def _shuffle_bits(data: bytearray) -> None:
    size = min(len(data), 0x800)
    start = len(data) - size
    permutation = _permutation(size * 8)
    for index in range(0, len(permutation) // 2 * 2, 2):
        left, right = permutation[index:index + 2]
        left_byte, left_bit = start + left // 8, left % 8
        right_byte, right_bit = start + right // 8, right % 8
        if ((data[left_byte] >> left_bit) & 1) != ((data[right_byte] >> right_bit) & 1):
            data[left_byte] ^= 1 << left_bit
            data[right_byte] ^= 1 << right_bit


def _crypt_stream(data: bytearray, size: int, multiplier: int) -> None:
    position = 0
    cycle = 0
    seeds = [0x9F73, 0xAEE3, 0x394D]
    lengths = [7, 13, 23]
    while position < size:
        for index in range(3):
            state = seeds[index]
            for _ in range(cycle + lengths[index]):
                if position >= size:
                    break
                state = (multiplier * state + 0x2F09) & 0xFFFFFFFF
                data[position] ^= (state >> 16) & 0xFF
                position += 1
            seeds[index] = state
            if position >= size:
                break
        cycle += 1


def _decode_zero_code(data: bytes) -> bytes:
    if len(data) < 4:
        raise SaveFormatError("zero-code header is truncated")
    output_size = struct.unpack_from(">I", data, 0)[0]
    if output_size > MAX_DECODED_SIZE + 261:
        raise SaveFormatError("zero-code output exceeds the processing bound")
    source = data[4:]
    byte_index = 0
    bit_index = 7

    def read_bit() -> int:
        nonlocal byte_index, bit_index
        if byte_index >= len(source):
            raise SaveFormatError("zero-code bitstream is truncated")
        value = (source[byte_index] >> bit_index) & 1
        if bit_index == 0:
            bit_index = 7
            byte_index += 1
        else:
            bit_index -= 1
        return value

    def peek_bit() -> int:
        if byte_index >= len(source):
            raise SaveFormatError("zero-code bitstream is truncated")
        return (source[byte_index] >> bit_index) & 1

    output = bytearray()
    while len(output) < output_size:
        if read_bit() == 1:
            output.append(0)
            continue
        zero_count = 1
        while zero_count < 8 and peek_bit() == 0:
            read_bit()
            zero_count += 1
        if zero_count == 8:
            output.append(0xFF)
            continue
        value = 0
        for _ in range(zero_count + 1):
            value = (value << 1) | read_bit()
        output.append((value - 1) & 0xFF)
    return bytes(output)


def _encode_zero_code(data: bytes) -> bytes:
    encoded = bytearray(struct.pack(">I", len(data)))
    pending = 0
    bit_count = 0
    for value in data:
        adjusted = (value + 1) & 0xFF
        width = (2 * adjusted.bit_length() - 1) if adjusted else 8
        pending = (pending << width) | adjusted
        bit_count += width
        while bit_count >= 8:
            bit_count -= 8
            encoded.append((pending >> bit_count) & 0xFF)
            pending &= (1 << bit_count) - 1
    if bit_count:
        encoded.append((pending << (8 - bit_count)) | ((1 << (8 - bit_count)) - 1))
    return bytes(encoded)


def _decode_palette(data: bytes) -> bytes:
    if not data:
        raise SaveFormatError("palette stream is empty")
    count = data[0] or 256
    if len(data) < 5 + count:
        raise SaveFormatError("palette header is truncated")
    table = data[1:1 + count]
    output_size = struct.unpack_from(">I", data, 1 + count)[0]
    if not 0 < output_size <= MAX_DECODED_SIZE:
        raise SaveFormatError("invalid palette output size")
    indices = data[5 + count:5 + count + output_size]
    if len(indices) != output_size:
        raise SaveFormatError("palette index stream is truncated")
    if len(data) != 5 + count + output_size:
        raise SaveFormatError("unsupported extra bytes after the palette index stream")
    if any(index >= count for index in indices):
        raise SaveFormatError("palette index is outside the table")
    return bytes(table[index] for index in indices)


def _encode_palette(data: bytes) -> bytes:
    if not 0 < len(data) <= MAX_DECODED_SIZE:
        raise SaveFormatError("invalid decoded payload size")
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    table = [value for value in range(256) if counts[value]]
    table.sort(key=lambda value: (-counts[value], -value))
    indices = [0] * 256
    for index, value in enumerate(table):
        indices[value] = index
    return (
        bytes([len(table) & 0xFF])
        + bytes(table)
        + struct.pack(">I", len(data))
        + bytes(indices[value] for value in data)
    )


def decode_body(raw: bytes) -> tuple[bytes, EnvelopeDetails]:
    if len(raw) > MAX_FILE_SIZE - HEADER_SIZE:
        raise SaveFormatError("encrypted body exceeds the processing bound")
    trimmed = raw.rstrip(b"\0")
    padded_size = (len(trimmed) + 15) & ~15
    if padded_size < 16 or padded_size > len(raw):
        raise SaveFormatError("invalid encrypted body size")
    data = bytearray(raw[:padded_size])
    _shuffle_bits(data)

    multiplier = 0x3B9A73C9
    state = 0xD5C1
    for offset in range(0, padded_size, 2):
        value = struct.unpack_from(">H", data, offset)[0]
        state, random1 = _next_rand(multiplier, state)
        if random1 % 3506 >= 1753:
            state, random2 = _next_rand(multiplier, state)
            value ^= random2
        struct.pack_into(">H", data, offset, (value - random1) & 0xFFFF)

    payload_size = padded_size - 16
    if data[payload_size] != 0xFF:
        raise SaveFormatError("encrypted body marker mismatch")
    seed = struct.unpack_from(">I", data, padded_size - 4)[0]
    _crypt_stream(data, payload_size, (seed + 0x3B9A73C9) & 0xFFFFFFFF)

    expected_xor = struct.unpack_from(">I", data, padded_size - 12)[0]
    expected_sum = struct.unpack_from(">I", data, padded_size - 8)[0]
    checksum_xor = 0
    checksum_sum = 0
    for (value,) in struct.iter_unpack(">I", data[:payload_size]):
        checksum_xor ^= value
        checksum_sum = (checksum_sum + value) & 0xFFFFFFFF
    if checksum_xor != expected_xor or checksum_sum != expected_sum:
        raise SaveFormatError("encrypted body checksum mismatch")

    decoded = _decode_palette(_decode_zero_code(bytes(data[:payload_size])))
    footer = bytes(data[payload_size + 1:payload_size + 4])
    return decoded, EnvelopeDetails(seed, padded_size, checksum_xor, checksum_sum, footer)


def encode_body(decoded: bytes, seed: int, footer: bytes = bytes(3)) -> bytes:
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise SaveFormatError("invalid encryption seed")
    if not isinstance(footer, bytes) or len(footer) != 3:
        raise SaveFormatError("envelope footer must be exactly three bytes")
    compressed = _encode_zero_code(_encode_palette(decoded))
    payload_size = (len(compressed) + 15) & ~15
    total_size = payload_size + 16
    data = bytearray(total_size)
    data[:len(compressed)] = compressed

    checksum_xor = 0
    checksum_sum = 0
    for (value,) in struct.iter_unpack(">I", data[:payload_size]):
        checksum_xor ^= value
        checksum_sum = (checksum_sum + value) & 0xFFFFFFFF

    _crypt_stream(data, payload_size, (seed + 0x3B9A73C9) & 0xFFFFFFFF)
    data[payload_size] = 0xFF
    data[payload_size + 1:payload_size + 4] = footer
    struct.pack_into(">I", data, total_size - 12, checksum_xor)
    struct.pack_into(">I", data, total_size - 8, checksum_sum)
    struct.pack_into(">I", data, total_size - 4, seed)

    multiplier = 0x3B9A73C9
    state = 0xD5C1
    for offset in range(0, total_size, 2):
        value = struct.unpack_from(">H", data, offset)[0]
        state, random1 = _next_rand(multiplier, state)
        value = (value + random1) & 0xFFFF
        if random1 % 3506 >= 1753:
            state, random2 = _next_rand(multiplier, state)
            value ^= random2
        struct.pack_into(">H", data, offset, value)
    _shuffle_bits(data)
    return bytes(data)


def decode_file(raw: bytes) -> tuple[bytes, bytes, EnvelopeDetails]:
    if not isinstance(raw, (bytes, bytearray)) or not HEADER_SIZE < len(raw) <= MAX_FILE_SIZE:
        raise SaveFormatError("save file is too small")
    header = raw[:HEADER_SIZE]
    decoded, details = decode_body(raw[HEADER_SIZE:])
    return header, decoded, details


def encode_file(header: bytes, decoded: bytes, seed: int, footer: bytes = bytes(3)) -> bytes:
    if len(header) != HEADER_SIZE:
        raise SaveFormatError("save header must be exactly 0x100 bytes")
    return header + encode_body(decoded, seed, footer)
