"""Forged snapshot and changed-backup regressions on procedural copied data."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from models import SaveError
import origins_codec as codec
import origins_parser as parser
from game_registry import get_game
from tests.test_origins_parser import fixture


class OriginsSnapshotSafetyTests(unittest.TestCase):
    def test_forged_revision_cannot_expose_or_stage_absent_dlc_fields(self):
        original = parser.decode(fixture(revision=17))
        forged = replace(original, revision=29)
        adapter = get_game('origins').get_scalar_adapter()
        for action in (lambda: adapter.fields_for(forged),
                       lambda: adapter.stage(forged, {}, 'dlc_skill_points', 999),
                       lambda: adapter.maximums(forged, {}),
                       lambda: parser.field_hint(forged, 'dlc_skill_points')):
            with self.assertRaises(SaveError):
                action()
        self.assertNotIn('dlc_skill_points', parser.field_map(original))
        self.assertEqual(parser.serialize(original, {}), original.raw)

    def test_mutable_buffers_and_non_native_metadata_rejected_before_staging(self):
        original = parser.decode(fixture())
        forged = (replace(original, raw=bytearray(original.raw)),
                  replace(original, payload=bytearray(original.payload)),
                  replace(original, seed=float(original.seed)),
                  replace(original, revision=float(original.revision)))
        for document in forged:
            with self.subTest(raw_type=type(document.raw), seed_type=type(document.seed),
                              revision_type=type(document.revision)), self.assertRaises(SaveError):
                parser.stage(document, {}, 'gold', 0)
        self.assertEqual(parser.serialize(original, {}), original.raw)

    def test_actual_restored_bytes_qualified_after_coherent_backup_manifest_change(self):
        area = Path(__file__).resolve().parents[1] / '.test-runs'
        area.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=area) as folder:
            source = Path(folder) / 'SLOT0000.dat'
            raw = fixture()
            source.write_bytes(raw)
            document = parser.read_save(source)
            snapshot = parser.backup(document)
            destination = Path(folder) / 'restored.dat'
            system = codec.encode(bytes(codec.USER_FILE_SIZE - 4), 9, 'user')
            read = parser.read_save

            def change_after_qualification(path, game_id=parser.GAME_ID):
                qualified = read(path, game_id)
                # Both files now agree on hash/size/game, so a metadata-only
                # restore would accept system data as a native gameplay slot.
                snapshot.write_bytes(system)
                manifest_path = snapshot.with_suffix('.json')
                manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                manifest.update(sha256=hashlib.sha256(system).hexdigest(), size_bytes=len(system))
                manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                return qualified

            with patch.object(parser, 'read_save', side_effect=change_after_qualification):
                with self.assertRaisesRegex(SaveError, 'USER.dat'):
                    parser.restore(snapshot, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(snapshot.read_bytes(), system)
