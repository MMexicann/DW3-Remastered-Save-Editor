"""Research-only Pirate Warriors 4 PC word envelope recovered statically.

See PIRATE_ABYSS_RESEARCH.md. One freely shared PC slot has passed the outer
envelope roundtrip; native schema identity, gameplay fields and game loading
remain unqualified. This module is deliberately absent
from the game registry and exposes no filesystem or gameplay edit operations.
The caller must choose the observed region explicitly; a checksum match alone
does not prove the file's game, region or system/slot classification.
"""
from dataclasses import dataclass
import struct

from koei_codec import word_sum


OBSERVED_SIZES = (0x2804, 0x27161C)
REGION_STEPS = {'WW': 1, 'JP': 1, 'AS': 4, 'EU': 3, 'NA': 3, 'EA': 1}
# A genuine publicly shared PC slot passed the outer-envelope roundtrip only.
# This does not qualify the inner block tree, gameplay writes or a revision.
PC_SAMPLE_VERIFIED = True
NATIVE_IDENTITY_VERIFIED = False


def _bytes(value, label):
    if type(value) not in (bytes, bytearray, memoryview):
        raise ValueError(f'{label} requires byte data.')
    size = value.nbytes if type(value) is memoryview else len(value)
    if size not in OBSERVED_SIZES:
        raise ValueError('The candidate must have an executable-observed envelope size.')
    return value.tobytes() if type(value) is memoryview else bytes(value)


def _steps(region):
    if type(region) is not str or region not in REGION_STEPS:
        raise ValueError('Explicit executable-observed region WW/JP/AS/EU/NA/EA required.')
    return REGION_STEPS[region]


def _cipher(payload, seed, steps):
    """XOR complete u32 words, advancing the LCG steps times per word."""
    output = bytearray(payload)
    for offset in range(0, len(output), 4):
        for _ in range(steps):
            seed = (seed * 0x5B1A7851 + 0xCE4E) & 0xFFFFFFFF
        value = struct.unpack_from('<I', output, offset)[0]
        struct.pack_into('<I', output, offset, value ^ seed)
    return bytes(output)


def _decode(raw, region):
    steps = _steps(region)
    if type(raw) is not bytes or len(raw) not in OBSERVED_SIZES:
        raise ValueError('An immutable envelope of an observed size is required.')
    expected, seed = struct.unpack_from('<HH', raw)
    payload = _cipher(raw[4:], seed, steps)
    if word_sum(payload) != expected:
        raise ValueError('Candidate checksum mismatch; no corruption repair is performed.')
    return payload


@dataclass(frozen=True)
class CandidateDocument:
    """Cipher evidence snapshot, without qualified native title identity."""
    raw: bytes
    payload: bytes
    region: str

    def unchanged_roundtrip(self):
        """Re-encrypt only a checked unchanged payload; never repair integrity."""
        if type(self.raw) is not bytes or type(self.payload) is not bytes:
            raise ValueError('Candidate snapshots must contain immutable bytes.')
        if _decode(self.raw, self.region) != self.payload:
            raise ValueError('The candidate snapshot was modified.')
        checksum, seed = struct.unpack_from('<HH', self.raw)
        encoded = struct.pack('<HH', checksum, seed) + _cipher(
            self.payload, seed, _steps(self.region))
        if encoded != self.raw:
            raise ValueError('Candidate unchanged roundtrip mismatch.')
        return encoded


def decode_candidate(raw, *, region):
    """Decode explicit PW4 research input; arithmetic is not title validation."""
    _steps(region)
    frozen = _bytes(raw, 'Candidate envelope')
    return CandidateDocument(frozen, _decode(frozen, region), region)
