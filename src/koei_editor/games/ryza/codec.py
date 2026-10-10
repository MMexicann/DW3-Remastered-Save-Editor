"""Qualified Ryza 1/2 native envelope using the existing Gust codec.

Both independent public Ryza gameplay layouts pass its XOR and additive checks.
This is envelope reuse, not reuse of Sophie 2's gameplay schema. The underlying
codec is adapted from Tartarshia/Sophie2SaveEditor at commit
93d807072a852c73799394af4d32fb164841cd3e under MIT; see
licenses/atelier-sophie2-save-editor-MIT.txt. No third-party binary is required.
"""
from koei_editor.games.sophie2.atelier_sophie2_codec import (
    HEADER_SIZE, MAX_FILE_SIZE, SaveFormatError, decode_file, encode_file,
)
