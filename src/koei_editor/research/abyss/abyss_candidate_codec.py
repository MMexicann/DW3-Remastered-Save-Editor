"""Read-only Warriors: Abyss encrypted PC envelope candidate.

Statically recovered AES-256-CBC and owner-key derivation are documented in
PIRATE_ABYSS_RESEARCH.md. The inner serialization and its integrity are not
qualified against any native save. No mutable encoding, file operations,
account reassignment, GUI registration or gameplay fields are provided.
Owner context is supplied explicitly and is neither stored nor returned.
"""
from dataclasses import dataclass
import hmac
import struct

from koei_editor.games.dw3.save_codec import CNG_AES


OUTER_MAGIC = b'470558d4d8015d9f'
INNER_MAGIC = b'a1423bc7d48e148b'
IV = bytes.fromhex('e1c1c49f9a3019341ea820f99fd09a83')
OWNER_MASK = 0xFABE9C015F6E379A
OBSERVED_SIZES = (0x2800, 0x30000)
OBSERVED_REVISION = 0xA4
PC_SAMPLE_VERIFIED = False
GAMEPLAY_INTEGRITY_VERIFIED = False


def _owner_key(owner_context):
    if type(owner_context) is not int or not 0 <= owner_context <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError('Explicit unsigned 64-bit save-owner context required.')
    return str(owner_context ^ OWNER_MASK).encode('ascii').ljust(32, b'\0')


def _bytes(value):
    if type(value) not in (bytes, bytearray, memoryview):
        raise ValueError('The candidate envelope requires byte data.')
    size = value.nbytes if type(value) is memoryview else len(value)
    if size not in OBSERVED_SIZES:
        raise ValueError('Only executable-observed aligned system/game buffers are investigated.')
    return value.tobytes() if type(value) is memoryview else bytes(value)


def _decode(raw, owner_context):
    key = _owner_key(owner_context)
    if not raw.startswith(OUTER_MAGIC):
        raise ValueError('Missing encrypted Abyss candidate marker.')
    with CNG_AES('CBC') as provider:
        plaintext = provider.transform(raw[16:], key, direction='decrypt', iv=IV)
    if not hmac.compare_digest(plaintext[:16], INNER_MAGIC):
        raise ValueError('Candidate encrypted marker mismatch; owner context or input is invalid.')
    payload = plaintext[16:]
    if struct.unpack_from('<I', payload)[0] != OBSERVED_REVISION:
        raise ValueError('Only the statically observed Abyss candidate revision is investigated.')
    return payload


@dataclass(frozen=True)
class CandidateDocument:
    """Read-only decrypted snapshot; inner gameplay integrity remains unknown."""
    raw: bytes
    payload: bytes

    @property
    def writable(self):
        return False

    @property
    def integrity_verified(self):
        return False

    def unchanged_roundtrip(self, *, owner_context):
        """Require original owner context and unchanged bytes before re-encryption."""
        if type(self.raw) is not bytes or type(self.payload) is not bytes:
            raise ValueError('Candidate snapshots must contain immutable bytes.')
        raw = _bytes(self.raw)
        if _decode(raw, owner_context) != self.payload:
            raise ValueError('The candidate snapshot was modified.')
        with CNG_AES('CBC') as provider:
            encoded = OUTER_MAGIC + provider.transform(
                INNER_MAGIC + self.payload, _owner_key(owner_context),
                direction='encrypt', iv=IV)
        if encoded != raw:
            raise ValueError('Candidate unchanged roundtrip mismatch.')
        return encoded


def decode_candidate(raw, *, owner_context):
    """Inspect a copied candidate without retaining owner/account information."""
    _owner_key(owner_context)
    frozen = _bytes(raw)
    return CandidateDocument(frozen, _decode(frozen, owner_context))
