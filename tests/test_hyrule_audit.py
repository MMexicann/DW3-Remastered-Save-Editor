"""Independent adversarial checks; procedural exports, no game-load claims."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.hyrule_warriors import parser as hw
from koei_editor.games.age_of_calamity import parser as aoc
from tests.test_hyrule_formats import procedural_hw, procedural_aoc


class HyruleSafetyAuditTests(unittest.TestCase):
    def pairs(self):
        return ((hw, procedural_hw), (aoc, procedural_aoc))

    def test_max_rejects_invalid_pending_values_before_bulk_action(self):
        for backend, fixture in self.pairs():
            doc = backend.decode(fixture())
            for changes in ({'rupees': -1}, {'rupees': True}, {'rupees': '5'},
                            {'rupees': 10_000_000}, {'unknown_system': 1}):
                with self.subTest(game=backend.GAME_ID, changes=changes), self.assertRaises(SaveError):
                    backend.maximums(doc, changes)
                with self.subTest(game=backend.GAME_ID, changes=changes), self.assertRaises(SaveError):
                    backend.limit_values(doc, changes, ['rupees'])

    def test_high_originals_and_unknown_record_bytes_survive_bulk_action(self):
        for backend, fixture in self.pairs():
            raw = bytearray(fixture())
            raw[backend.RUPEES_OFFSET:backend.RUPEES_OFFSET + 4] = (0xFFFFFFFF).to_bytes(4, backend.BYTEORDER)
            if backend is hw:
                offset = hw.WEAPON_OFFSET
                raw[offset] = 0xF3  # Unknown weapon state must remain inspection only.
            else:
                offset = aoc.WEAPON_OFFSET
                raw[offset + 0x4C] = 7  # Unknown protection value must remain inspection only.
            doc = backend.decode(bytes(raw))
            staged = backend.maximums(doc, {})
            self.assertNotIn('rupees', staged)
            result = backend.serialize(doc, staged)
            allowed = {byte for key in staged for byte in range(backend.field_map(doc)[key].offset,
                       backend.field_map(doc)[key].offset + backend.field_map(doc)[key].size)}
            with self.subTest(game=backend.GAME_ID):
                self.assertLessEqual({index for index, pair in enumerate(zip(doc.raw, result)) if pair[0] != pair[1]}, allowed)
                self.assertEqual(result[offset:offset + backend.WEAPON_STRIDE], doc.raw[offset:offset + backend.WEAPON_STRIDE])
                self.assertEqual(backend.stage(doc, {}, 'rupees', 0xFFFFFFFF), {})

    def test_mutable_or_foreign_snapshots_are_rejected_for_backup_and_save(self):
        for backend, fixture in self.pairs():
            doc = backend.decode(fixture())
            for forged in (replace(doc, raw=bytearray(doc.raw)), replace(doc, payload=memoryview(doc.payload)),
                           replace(doc, format=replace(doc.format, id='foreign'))):
                with self.subTest(game=backend.GAME_ID), self.assertRaises(SaveError):
                    backend.backup(forged)
                with self.subTest(game=backend.GAME_ID), self.assertRaises(SaveError):
                    backend.serialize(forged, {})

    def test_hash_consistent_wrong_layout_backup_cannot_restore(self):
        for backend, fixture in self.pairs():
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source = root / ('original' + backend.EXTENSION)
                source.write_bytes(fixture())
                backup = backend.backup(backend.read_save(source))
                corrupted = bytearray(backup.read_bytes())
                corrupted[:4] = b'BAD!'
                backup.write_bytes(corrupted)
                record_path = backup.with_suffix('.json')
                record = json.loads(record_path.read_text())
                record['sha256'] = hashlib.sha256(corrupted).hexdigest()
                record_path.write_text(json.dumps(record))
                target = root / ('restored' + backend.EXTENSION)
                with self.subTest(game=backend.GAME_ID), self.assertRaises(SaveError):
                    backend.restore(backup, target)
                self.assertFalse(target.exists())

    def test_extensionless_backup_names_and_sidecars_are_distinct(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'svdt-copy'
            source.write_bytes(procedural_aoc())
            doc = aoc.read_save(source)
            first, second = aoc.backup(doc), aoc.backup(doc)
            self.assertEqual(first.suffix, '')
            self.assertEqual(second.suffix, '')
            self.assertNotEqual(first, second)
            self.assertNotEqual(first, first.with_suffix('.json'))
            for backup in (first, second):
                self.assertEqual(backup.read_bytes(), doc.raw)
                self.assertEqual(json.loads(backup.with_suffix('.json').read_text())['size_bytes'], len(doc.raw))
            restored = aoc.restore(first, root / 'svdt-restored')
            self.assertEqual(restored.suffix, '')
            self.assertEqual(restored.read_bytes(), doc.raw)
            with self.assertRaises(FileExistsError):
                aoc.restore(first, restored)


class ManualOnlyExpansionAuditTests(unittest.TestCase):
    def test_ps3_manual_max_rejects_bad_staging_and_preserves_unusual_originals(self):
        from koei_editor.games.dw7_ps3 import parser as dw7
        from koei_editor.games.sw4_ps3 import parser as sw4
        from tests.test_ps3_expansion import fixture
        for backend in (dw7, sw4):
            raw = bytearray(fixture(backend))
            gold = backend.FORMAT.fields[0]
            raw[gold.offset:gold.offset + gold.size] = (0xFFFFFFFF).to_bytes(4, 'big')
            doc = backend.decode(backend.seal(bytes(raw)))
            self.assertEqual(backend.maximums(doc, {}), {})
            self.assertEqual(backend.serialize(doc, backend.maximums(doc, {})), doc.raw)
            self.assertEqual(backend.stage(doc, {}, 'gold', 0xFFFFFFFF), {})
            for changes in ({'gold': -1}, {'gold': True}, {'gold': 1000000}, {'story': 1}):
                with self.subTest(game=backend.GAME_ID, changes=changes), self.assertRaises(SaveError):
                    backend.maximums(doc, changes)


if __name__ == '__main__':
    unittest.main()
