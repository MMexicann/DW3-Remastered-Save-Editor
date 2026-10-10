"""Read-only, static-source Warriors All-Stars PC envelope research.

Recovered from the supplied native executable without executing it. These
routines qualify the observed block boundaries and encrypted sentinel only;
they do not qualify gameplay revisions, semantic records or full integrity.
No editor registration, field writer or disk I/O is provided. See
STARS_WO4_RESEARCH.md for provenance and missing native-save validation.
"""
from dataclasses import dataclass, field
import struct

from save_codec import CNG_AES


SYSTEM_PAYLOAD_SIZE = 0x79B66
SLOT_PAYLOAD_SIZE = 0x78E41
SYSTEM_BLOCK_SIZE = 0x79B84
SLOT_BLOCK_SIZE = 0x78E64
SLOT_COUNT = 9
CANDIDATE_FILE_SIZE = SYSTEM_BLOCK_SIZE + SLOT_COUNT * SLOT_BLOCK_SIZE
_SENTINEL = b'FingerPrint01234'
# Low DWORDs of IEEE754 doubles after ten x=(1-x)*(4*x) iterations,
# starting at (index+1)*0.5/10. Constants avoid platform float differences.
_KEY_SEEDS = (0x4551FCBA, 0xF2FD87BD, 0x63B2BCDC, 0xF2FD8C96, 0,
              0xA0F56D5C, 0xE81A2FA9, 0x449AA6D3, 0xA916755C, 0)


def _lcg_bytes(seed, multiplier, increment, shift):
    output = bytearray()
    for _ in range(16):
        seed = (seed * multiplier + increment) & 0xFFFFFFFF
        output.append((seed >> shift) & 255)
    return bytes(output)


def key_for_block(index):
    """Index 9 is the global block; indices 0 through 8 are slot blocks."""
    if type(index) is not int or not 0 <= index <= 9:
        raise ValueError('Candidate key index must be an integer from 0 through 9.')
    return _lcg_bytes(_KEY_SEEDS[index], 0x343FD, 0x269EC3, 24)


def iv_from_seed(seed):
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError('Candidate IV seed must be an unsigned DWORD.')
    return _lcg_bytes(seed, 0x15A4E35, 1, 16)


def _raw_bytes(raw):
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise TypeError('Candidate data must be a byte buffer.')
    if isinstance(raw, memoryview) and (raw.ndim != 1 or raw.itemsize != 1):
        raise ValueError('Candidate data must be a one-dimensional byte buffer.')
    if len(raw) != CANDIDATE_FILE_SIZE:
        raise ValueError('Candidate has a different size from the inspected PC layout.')
    return bytes(raw)


@dataclass(frozen=True)
class CandidateBlock:
    index: int
    file_offset: int
    iv_seed: int
    payload: bytes = field(repr=False)
    padding: bytes = field(repr=False)


@dataclass(frozen=True)
class CandidateDocument:
    raw: bytes = field(repr=False)
    blocks: tuple[CandidateBlock, ...]
    native_fixture_verified: bool = field(default=False, init=False)
    revision_verified: bool = field(default=False, init=False)
    integrity_verified: bool = field(default=False, init=False)
    writable: bool = field(default=False, init=False)


def inspect_candidate(raw):
    """Decode the ten observed spans, requiring every encrypted sentinel.

    Preserves padding exactly, including unusual nonzero bytes. A valid sentinel
    does not protect the entire preceding payload, and is not a checksum. This
    function must never be used as the acceptance check for gameplay editing.
    """
    raw = _raw_bytes(raw)
    blocks = []
    with CNG_AES('CBC') as aes:
        for position in range(SLOT_COUNT + 1):
            index = 9 if position == 0 else position - 1
            offset = 0 if position == 0 else SYSTEM_BLOCK_SIZE + index * SLOT_BLOCK_SIZE
            size = SYSTEM_BLOCK_SIZE if position == 0 else SLOT_BLOCK_SIZE
            payload_size = SYSTEM_PAYLOAD_SIZE if position == 0 else SLOT_PAYLOAD_SIZE
            block = raw[offset:offset + size]
            seed = struct.unpack_from('<I', block, size - 4)[0]
            plain = aes.transform(block[:-4], key_for_block(index),
                                  direction='decrypt', iv=iv_from_seed(seed))
            if plain[-16:] != _SENTINEL:
                raise ValueError(f'Candidate encrypted sentinel failed for block {index}.')
            blocks.append(CandidateBlock(index, offset, seed, plain[:payload_size],
                                         plain[payload_size:-16]))
    return CandidateDocument(raw, tuple(blocks))


def reencode_unchanged(document):
    """Rebuild only an unchanged decoded snapshot; reject payload/padding edits."""
    if not isinstance(document, CandidateDocument):
        raise TypeError('An inspected candidate document is required.')
    if type(document.raw) is not bytes or type(document.blocks) is not tuple:
        raise ValueError('Candidate snapshots must contain immutable bytes and block tuples.')
    for block in document.blocks:
        if (type(block) is not CandidateBlock or type(block.payload) is not bytes
                or type(block.padding) is not bytes):
            raise ValueError('Candidate blocks must contain immutable byte snapshots.')
    original = inspect_candidate(document.raw)
    if document != original:
        raise ValueError('Candidate gameplay writes are unavailable until qualified.')
    output = bytearray()
    with CNG_AES('CBC') as aes:
        for block in original.blocks:
            output.extend(aes.transform(block.payload + block.padding + _SENTINEL,
                                        key_for_block(block.index), direction='encrypt',
                                        iv=iv_from_seed(block.iv_seed)))
            output.extend(struct.pack('<I', block.iv_seed))
    encoded = bytes(output)
    if encoded != original.raw:
        raise ValueError('Candidate no-edit reconstruction did not preserve the input.')
    return encoded
