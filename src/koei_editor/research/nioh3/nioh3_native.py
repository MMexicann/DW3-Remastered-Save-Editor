"""Source-only Nioh 3 PC native user-save integrity qualification.

Independently implemented format facts from alfizari/Nioh-3-Save-Editor
(Apache-2.0), corroborated by Master-Bayesian/Nioh3-Scroll-Generator (GPL-3.0).
No source implementation, game assets or player saves are distributed.

This module deliberately has no gameplay field writer, file I/O or library card:
current published inventory offsets do not qualify the acquired native files.
"""
from dataclasses import dataclass
import struct

import koei_editor.research.katana.katana_codec as katana_codec
from koei_editor.games.dw3.models import SaveError


USER_SIZE = 0x9001B0
HEADER_SIZE = 0x158
BODY_START, BODY_END = 0x190, 0x900190
CHECKSUM_SEED_OFFSET, CHECKSUM_OFFSET = BODY_END, BODY_END + 4
SUPPORTED_REVISIONS = frozenset((0x01030001, 0x01040000))


@dataclass(frozen=True)
class Document:
    raw: bytes
    payload: bytes
    revision: int
    encrypted: bool = False
    integrity_verified: bool = True

    @property
    def writable(self):
        # Integrity qualification alone does not establish a gameplay field map.
        return False


def body_checksum(payload):
    """Native signed-qword block folding; preserves the per-save seed.

    Blocks cover exactly 0x900000 bytes. Each 0x400-byte block contributes its
    signed little-endian 64-bit sum, then the accumulator is XORed with the
    stored 32-bit seed and reduced to 64 bits. The final end-around fold uses
    division by 0xffffffff, rather than an ordinary upper-word shift.
    """
    if not isinstance(payload, (bytes, bytearray)) or len(payload) != USER_SIZE:
        raise SaveError('Nioh 3 user checksum requires the qualified fixed-size native payload.')
    seed = struct.unpack_from('<I', payload, CHECKSUM_SEED_OFFSET)[0]
    accumulator = 0
    for position in range(BODY_START, BODY_END, 0x400):
        contribution = sum(struct.unpack_from('<128q', payload, position))
        accumulator = ((accumulator + contribution) ^ seed) % (1 << 64)
    high = accumulator // 0xffffffff
    # The published fold adds the bitwise low word, not an ordinary modulo remainder.
    return (high + (accumulator & 0xffffffff)) & 0xffffffff


def decode_plaintext(raw):
    """Validate only the independently acquired decoded native PC profiles.

    This entry point requires decoded input. Use decode() for a qualified encrypted
    copy. System data, other revisions, altered lengths and corrupt bodies fail
    closed. No checksum repair or account rebinding is offered.
    """
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != USER_SIZE:
        raise SaveError('Nioh 3 native user data must contain exactly 0x9001B0 bytes.')
    raw = bytes(raw)
    if raw[:8] != b'RNNUSR\0\0':
        raise SaveError('Select decoded Nioh 3 PC user data; encrypted/system files are unsupported.')
    revision = struct.unpack_from('<I', raw, 8)[0]
    if revision not in SUPPORTED_REVISIONS or struct.unpack_from('<I', raw, 0x15c)[0] != revision:
        raise SaveError('Nioh 3 user revision markers do not match the acquired native profiles.')
    if struct.unpack_from('<II', raw, 0x18) != (HEADER_SIZE, USER_SIZE - HEADER_SIZE):
        raise SaveError('Nioh 3 native header/body lengths do not match the file.')
    if struct.unpack_from('<I', raw, CHECKSUM_OFFSET)[0] != body_checksum(raw):
        raise SaveError('Nioh 3 native user body integrity check failed.')
    return Document(raw, raw, revision)


def decode(raw):
    """Qualify a native encrypted/decrypted USER copy without rebinding it.

    Reuse the project's independently authored Katana cipher primitives. This
    inspector retains wrapped body-key material in the decrypted header; the
    final eight bytes lie outside the cipher. Both spans are preserved exactly.
    The acquired reference has zeroed key bytes; all remaining header/body/tail
    bytes match the decoded encrypted USER pair independently.
    """
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != USER_SIZE:
        raise SaveError('Nioh 3 native user data must contain exactly 0x9001B0 bytes.')
    raw = bytes(raw)
    if raw[:8] == b'RNNUSR\0\0':
        return decode_plaintext(raw)
    header = katana_codec._header_crypt(raw[:HEADER_SIZE])
    revision = struct.unpack_from('<I', header, 8)[0]
    if (header[:8] != b'RNNUSR\0\0' or revision not in SUPPORTED_REVISIONS or
            struct.unpack_from('<II', header, 0x18) != (HEADER_SIZE, USER_SIZE - HEADER_SIZE)):
        raise SaveError('Wrong encrypted Nioh 3 title, user layout or supported revision.')
    profile = katana_codec.Profile(HEADER_SIZE, (b'RNNUSR\0\0', b'RNNSYS\0\0'), revision,
                                  length_offset=0x18, key_offset=0x49)
    decoded = katana_codec._nioh_decrypt(raw, profile)
    payload = header + decoded[HEADER_SIZE:-8] + raw[-8:]
    qualified = decode_plaintext(payload)
    return Document(raw, qualified.payload, revision, True)


def serialize(document, changes):
    """Exact no-op roundtrip only until a genuine gameplay layout qualifies."""
    if (type(document) is not Document or type(document.raw) is not bytes or
            type(document.payload) is not bytes or type(document.revision) is not int or
            type(document.encrypted) is not bool or type(document.integrity_verified) is not bool):
        raise SaveError('Foreign or mutable Nioh 3 native inspection snapshot.')
    original = decode(document.raw)
    if original != document:
        raise SaveError('The Nioh 3 native inspection snapshot was changed.')
    if changes:
        raise SaveError('Nioh 3 gameplay writes remain unavailable: native record layout is unqualified.')
    return document.raw
