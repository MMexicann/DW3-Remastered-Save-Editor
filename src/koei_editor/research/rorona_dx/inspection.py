"""Bounded, read-only inspection of the independently acquired PC archive layout.

The structural fingerprint is not native integrity or a supported game profile.
No gameplay names, editable fields, checksum repair or save writer are provided.
See docs/ARLAND_DX_RESEARCH.md for provenance and remaining qualification.
"""
from dataclasses import dataclass
import struct

from koei_editor.games.dw3.models import SaveError


SAVE_SIZE = 380928
MAGIC = 20100403
HEADER_SIZE = 32
CHUNK_SIZES = (
    39392, 8416, 4, 6112, 138252, 128, 100816, 4, 5248, 1, 8,
    68, 132, 3584, 8, 9376, 47984, 4137, 128, 768, 384, 120,
    256, 234, 4, 4, 64, 7048, 32, 188, 832, 488,
)
TRAILER_TAG = 1024
TRAILER_SIZE = 6420  # Includes the trailer's eight-byte header.


@dataclass(frozen=True)
class Chunk:
    tag: int
    header_offset: int
    payload_offset: int
    size: int


@dataclass(frozen=True)
class Inspection:
    raw: bytes
    chunks: tuple[Chunk, ...]
    trailer_offset: int
    trailer_size: int
    editable: bool = False
    qualified_game_profile: bool = False
    integrity_qualified: bool = False


def inspect(raw: bytes) -> Inspection:
    """Match the complete observed layout without interpreting gameplay bytes.

    Reserved header words and every chunk/trailer payload remain opaque. The
    source archive establishes these lengths and tags, but not a checksum.
    """
    if type(raw) is not bytes or len(raw) != SAVE_SIZE:
        raise SaveError('Rorona DX layout inspection requires immutable, exact-size candidate bytes.')
    if struct.unpack_from('<I', raw)[0] != MAGIC:
        raise SaveError('Unrecognized Rorona DX candidate header.')
    offset = HEADER_SIZE
    chunks = []
    for expected_tag, expected_size in enumerate(CHUNK_SIZES, 1):
        if offset > len(raw) - 8:
            raise SaveError('Truncated Rorona DX candidate chunk header.')
        tag, size = struct.unpack_from('<II', raw, offset)
        if tag != expected_tag or size != expected_size or size > len(raw) - offset - 8:
            raise SaveError('Unrecognized Rorona DX candidate chunk layout.')
        chunks.append(Chunk(tag, offset, offset + 8, size))
        offset += 8 + size
    if offset > len(raw) - 8:
        raise SaveError('Missing Rorona DX candidate trailer.')
    tag, size = struct.unpack_from('<II', raw, offset)
    if tag != TRAILER_TAG or size != TRAILER_SIZE or size != len(raw) - offset:
        raise SaveError('Unrecognized Rorona DX candidate trailer bounds.')
    return Inspection(raw, tuple(chunks), offset, size)


def unchanged(inspection: Inspection) -> bytes:
    """Return the exact input after rechecking this immutable inspection.

    This is a no-edit research roundtrip, not a gameplay serialization API.
    """
    if type(inspection) is not Inspection or inspect(inspection.raw) != inspection:
        raise SaveError('Rorona DX candidate inspection was changed or forged.')
    return inspection.raw
