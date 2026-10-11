"""Genuine original NGII revision-6 extracted story profile; STFS is excluded.

Independently implemented checksum and record facts from public documentation,
corroborated against genuine Xenia stories and an original-game CON package.
No third-party implementation is incorporated. See docs/NINJA_GAIDEN_RESEARCH.md.
"""
from functools import lru_cache
import struct

from koei_editor.games.dw3.models import SaveError

GAMEPLAY_SIZE = 30848
CHECKSUM_OFFSET = GAMEPLAY_SIZE
SAVE_SIZE = 31744
# Native size, revision 6 and repeated binary markers in genuine original NGII
# stories. This is a qualified profile signature, not an inferred title string.
PROFILE_HEADER = bytes.fromhex(
    '00007880 00000006 00000000 01234567 01000000 01234567 00000000 00000000')


def freeze(raw):
    if type(raw) not in (bytes, bytearray, memoryview):
        raise SaveError('An original Ninja Gaiden II extracted story copy is required.')
    try:
        length = raw.nbytes if isinstance(raw, memoryview) else len(raw)
        if length != SAVE_SIZE:
            raise SaveError('This revision requires a 31,744-byte extracted story copy. '
                            'CON/STFS packages and other editions are excluded.')
        return bytes(raw)
    except (TypeError, ValueError) as error:
        raise SaveError('A contiguous Ninja Gaiden II story snapshot is required.') from error


def checksum(raw):
    """Modulo-2**32 sum of native big-endian words, excluding the stored sum."""
    if type(raw) is not bytes or len(raw) != SAVE_SIZE:
        raise SaveError('A complete frozen story profile is required for its checksum.')
    return sum(word[0] for word in struct.iter_unpack('>I', raw[:CHECKSUM_OFFSET])) & 0xFFFFFFFF


@lru_cache(maxsize=4)
def _decode(raw):
    if raw[:len(PROFILE_HEADER)] != PROFILE_HEADER:
        raise SaveError('Not the qualified original Ninja Gaiden II revision-6 story header. '
                        'Sigma, Sigma 2, Black and system saves are different formats.')
    # Every genuine original story retains its Dragon Sword in the first native
    # item record. Level codes are independently published by ike9000e. This
    # reinforces title/record qualification rather than accepting checksum-only
    # byte arrays. Unusual or future profiles require separate qualification.
    if raw[48:52] not in (b'\0\x01\x01\0', b'\0\x01\x01\x01',
                          b'\0\x01\x01\x02', b'\0\x07\x01\0'):
        raise SaveError('The original NGII story Dragon Sword record is not qualified.')
    if struct.unpack_from('>I', raw, CHECKSUM_OFFSET)[0] != checksum(raw):
        raise SaveError('Ninja Gaiden II native gameplay word checksum does not match.')
    return raw


def decode(raw):
    return _decode(freeze(raw))


def rebuild(payload):
    """Rebuild only the proved native gameplay sum after a qualified field edit."""
    frozen = freeze(payload)
    result = bytearray(frozen)
    struct.pack_into('>I', result, CHECKSUM_OFFSET, checksum(frozen))
    return decode(result)
