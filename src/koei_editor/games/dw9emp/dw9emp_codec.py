"""Narrow native plaintext SYSTEMDATA profile from Steam 1.0.1.1.

Native loader/writer pass the full serialized buffer directly to ReadFile and
WriteFile. The complete SYSTEM serializer tree has no checksum or cipher. This
profile deliberately excludes older revisions, campaign files and CAW exports.
It is source-backed: independent native saves and edited game loads have not
been tested. See docs/DYNASTY_RESEARCH.md for native evidence and limitations.
"""
from koei_editor.games.dw3.models import SaveError


SAVE_SIZE = 0x2F1C28
REVISION = 0x210602F0
HAS_NATIVE_CHECKSUM = False
SAMPLE_VERIFIED = False
GAME_LOAD_VERIFIED = False

# Current kind-2 native call order and each component's cursor-count guard.
# Constructor counts are fixed for this profile, not fields read from the save.
# Most components remain semantically unknown and are preserved verbatim.
SERIALIZED_PREFIX = (
    ('revision', 1, 4), ('649690', 1, 0xD9C5),
    ('650C70', 100, 0x4725), ('63BD40', 2, 0x3D),
    ('63FA20', 90, 0x21), ('647850', 1026, 0x2C),
    ('5EF890', 200, 0x12), ('5F1000', 64, 0xD5),
    ('5F6D10', 1010, 0xE), ('644EB0', 299, 0x28),
    ('5FC7F0', 35, 0x46),
)
CAW_BASE = sum(count * width for _component, count, width in SERIALIZED_PREFIX)
CAW_STRIDE, CAW_COUNT = 0x1C9 + 0x25 + 0x24, 900
SERIALIZED_SUFFIX = (('688810', 4, 0x8107), ('671B80', 30, 0x2D),
                     ('6416F0', 1040, 0x1E), ('63ACA0', 120, 0x2A),
                     ('trailing values', 15, 1))
SERIALIZED_END = CAW_BASE + CAW_COUNT * CAW_STRIDE + sum(
    count * width for _component, count, width in SERIALIZED_SUFFIX)
CAPACITY_TAIL_SIZE = SAVE_SIZE - SERIALIZED_END


def decode(raw):
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise SaveError('DW9 Empires requires a complete binary SYSTEMDATA copy.')
    frozen = bytes(raw)
    if len(frozen) != SAVE_SIZE:
        raise SaveError('Only the native PC DW9 Empires current SYSTEMDATA '
                        f'profile ({SAVE_SIZE:,} bytes) is supported.')
    if int.from_bytes(frozen[:4], 'little') != REVISION:
        raise SaveError('Unsupported DW9 Empires system revision or foreign save. '
                        'This adapter requires native PC revision 0x210602F0.')
    return frozen


def encode(payload):
    """Validate and preserve native plaintext; there is no integrity to repair."""
    return decode(payload)
