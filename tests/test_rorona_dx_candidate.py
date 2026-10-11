"""Procedural structure checks and optional genuine archive-layout qualification."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.rorona_dx import inspection as candidate


def procedural_candidate():
    """Distinctive opaque bytes, not a manufactured playable save."""
    raw = bytearray((i * 17 + 29) % 256 for i in range(candidate.SAVE_SIZE))
    struct.pack_into('<I', raw, 0, candidate.MAGIC)
    offset = candidate.HEADER_SIZE
    for tag, size in enumerate(candidate.CHUNK_SIZES, 1):
        struct.pack_into('<II', raw, offset, tag, size)
        offset += 8 + size
    struct.pack_into('<II', raw, offset, candidate.TRAILER_TAG, candidate.TRAILER_SIZE)
    return bytes(raw)


class RoronaCandidateTests(unittest.TestCase):
    def test_complete_layout_opaque_preservation_and_no_gameplay_claim(self):
        raw = procedural_candidate()
        document = candidate.inspect(raw)
        self.assertEqual(candidate.unchanged(document), raw)
        self.assertEqual(tuple(chunk.tag for chunk in document.chunks), tuple(range(1, 33)))
        self.assertEqual(document.trailer_offset + document.trailer_size, len(raw))
        self.assertEqual(document.chunks[2].payload_offset, 0xBAF8)
        self.assertFalse(document.editable)
        self.assertFalse(document.qualified_game_profile)
        self.assertFalse(document.integrity_qualified)
        # Unknown reserved words and payload/trailer bytes are not normalized.
        self.assertNotEqual(raw[4:32], bytes(28))
        self.assertNotEqual(raw[document.trailer_offset + 8:], bytes(document.trailer_size - 8))

    def test_foreign_system_wrong_size_revision_and_mutable_input_rejected(self):
        raw = procedural_candidate()
        for bad in (raw[:-1], raw + b'\0', raw[:36864], bytes(len(raw)), bytearray(raw), memoryview(raw)):
            with self.subTest(kind=type(bad), size=len(bad)), self.assertRaises(SaveError):
                candidate.inspect(bad)
        bad = bytearray(raw)
        struct.pack_into('<I', bad, 0, candidate.MAGIC + 1)
        with self.assertRaises(SaveError):
            candidate.inspect(bytes(bad))

    def test_each_tag_length_and_trailer_bounds_rejected(self):
        raw = procedural_candidate()
        doc = candidate.inspect(raw)
        for chunk in doc.chunks:
            for delta, value in ((0, chunk.tag + 1), (4, chunk.size + 1), (4, 0xFFFFFFFF)):
                bad = bytearray(raw)
                struct.pack_into('<I', bad, chunk.header_offset + delta, value)
                with self.subTest(tag=chunk.tag, delta=delta, value=value), self.assertRaises(SaveError):
                    candidate.inspect(bytes(bad))
        for delta, value in ((0, 0), (4, candidate.TRAILER_SIZE - 8), (4, candidate.TRAILER_SIZE + 8)):
            bad = bytearray(raw)
            struct.pack_into('<I', bad, doc.trailer_offset + delta, value)
            with self.assertRaises(SaveError):
                candidate.inspect(bytes(bad))

    def test_forged_inspection_does_not_pass_roundtrip(self):
        raw = procedural_candidate()
        doc = candidate.inspect(raw)
        for bad in (None, replace(doc, raw=bytearray(raw)), replace(doc, editable=True),
                    replace(doc, integrity_qualified=True), replace(doc, chunks=doc.chunks[:-1]),
                    replace(doc, trailer_size=doc.trailer_size - 8)):
            with self.subTest(kind=type(bad)), self.assertRaises(SaveError):
                candidate.unchanged(bad)

    def test_optional_genuine_copied_archive_layout(self):
        selected = os.environ.get('RORONA_DX_CANDIDATE_DIR')
        if not selected:
            self.skipTest('No privately copied Rorona DX candidate directory supplied.')
        files = tuple(Path(selected).rglob('gamedata*'))
        self.assertTrue(files, 'No gameplay slot copies found in selected directory.')
        self.assertLessEqual(len(files), 99)
        for path in files:
            with self.subTest(slot=path.name):
                with path.open('rb') as source:
                    raw = source.read(candidate.SAVE_SIZE + 1)
                document = candidate.inspect(raw)
                self.assertEqual(candidate.unchanged(document), raw)
                self.assertFalse(document.integrity_qualified)


if __name__ == '__main__':
    unittest.main()
