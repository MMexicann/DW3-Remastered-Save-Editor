"""Reproduce observed Windows Berserk/AoT outer envelopes, read-only.

The caller selects a documented sample hypothesis. Length and a matching u16
sum do not prove native title/revision, semantic records or all integrity layers.
No gameplay fields, modified encoding, file I/O or adapter registration exist.
See docs/OTHER_KOEI_PC_RESEARCH.md for evidence and enabling inputs.
"""
from dataclasses import dataclass, field
import struct
from types import MappingProxyType

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.koei_codec import word_cipher, word_sum


@dataclass(frozen=True)
class SampleProfile:
    id: str
    observed_size: int
    advances: int


PROFILES = MappingProxyType({
    'berserk': SampleProfile('berserk', 0x135B20, 3),
    'aot1': SampleProfile('aot1', 0xBBE20, 3),
    'aot2_pk': SampleProfile('aot2_pk', 0x38461C, 1),
})


def _profile(profile):
    if type(profile) is not str or profile not in PROFILES:
        raise SaveError('Select an explicit documented Berserk/AoT sample profile.')
    return PROFILES[profile]


def _raw_bytes(raw, profile):
    # A subclass may override __len__/__bytes__ and evade the pre-copy bound.
    if type(raw) not in (bytes, bytearray, memoryview):
        raise SaveError('Envelope diagnostics require a byte buffer.')
    if isinstance(raw, memoryview) and (
            raw.ndim != 1 or raw.itemsize != 1 or not raw.c_contiguous):
        raise SaveError('Envelope diagnostics require a contiguous one-dimensional byte buffer.')
    # Check before copying or decrypting; each hypothesis has one observed size.
    if len(raw) != profile.observed_size:
        raise SaveError('Input size differs from the selected observed sample profile.')
    return bytes(raw)


def _cipher(body, seed, advances):
    if advances == 3:
        return word_cipher(body, seed)
    # AoT2 PK sample: one advance per complete little-endian u32, not AoT1's
    # three advances. The first four file bytes remain outside the cipher.
    output = bytearray(body)
    for offset in range(0, len(output), 4):
        seed = (seed * 0x5B1A7851 + 0xCE4E) & 0xFFFFFFFF
        value = struct.unpack_from('<I', output, offset)[0]
        struct.pack_into('<I', output, offset, value ^ seed)
    return bytes(output)


@dataclass(frozen=True)
class EnvelopeInspection:
    profile_id: str
    raw: bytes = field(repr=False)
    payload: bytes = field(repr=False)
    checksum: int
    seed: int
    # These are deliberately not constructor options. Native-file provenance
    # belongs to the local test record, never to successful cipher arithmetic.
    native_identity_verified: bool = field(default=False, init=False)
    revision_verified: bool = field(default=False, init=False)
    all_integrity_verified: bool = field(default=False, init=False)
    writable: bool = field(default=False, init=False)


def inspect(raw, *, profile):
    """Check the observed outer sum under one explicit sample hypothesis.

    The checksum covers every decrypted u16 after the four-byte sum/seed header.
    It detects the tested corruptions but has additive collisions; it is neither
    a title identifier nor evidence that inner records have no further checksums.
    """
    selected = _profile(profile)
    raw = _raw_bytes(raw, selected)
    checksum, seed = struct.unpack_from('<HH', raw)
    payload = _cipher(raw[4:], seed, selected.advances)
    if word_sum(payload) != checksum:
        raise SaveError('The selected sample profile failed its outer u16 checksum.')
    return EnvelopeInspection(selected.id, raw, payload, checksum, seed)


def reencode_unchanged(document):
    """Independently rebuild a validated unchanged snapshot, preserving its seed.

    Reject forged/mutable snapshots and recompute no integrity metadata. There
    is intentionally no argument for replacement plaintext or staged edits.
    """
    if type(document) is not EnvelopeInspection:
        raise SaveError('An inspected Berserk/AoT envelope snapshot is required.')
    if (type(document.raw) is not bytes or type(document.payload) is not bytes
            or type(document.checksum) is not int or type(document.seed) is not int):
        raise SaveError('Envelope snapshots must contain immutable bytes and integer metadata.')
    if any(getattr(document, name) is not False for name in (
            'native_identity_verified', 'revision_verified',
            'all_integrity_verified', 'writable')):
        raise SaveError('Envelope snapshots cannot claim qualified gameplay support.')
    verified = inspect(document.raw, profile=document.profile_id)
    if document != verified:
        raise SaveError('The envelope snapshot was changed; gameplay writes are unavailable.')
    selected = _profile(verified.profile_id)
    encoded = verified.raw[:4] + _cipher(verified.payload, verified.seed, selected.advances)
    if encoded != verified.raw:
        raise SaveError('Unchanged envelope reconstruction did not preserve the input.')
    return encoded
