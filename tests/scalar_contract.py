"""Reusable behavioral checks for an explicitly registered scalar adapter.

Subclass together with unittest.TestCase; supply game_id and fixture_bytes().
Fixtures must be copied/generated test data, never live player saves. Declare
payload_integrity_offsets only when the native checksum lives inside payload.
"""
from pathlib import Path
import tempfile

from game_registry import get_game
from models import SaveError


class ScalarContractTests:
    payload_integrity_offsets = frozenset()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.game = get_game(self.game_id)
        self.adapter = self.game.get_scalar_adapter()
        self.raw = self.fixture_bytes()
        self.source = self.folder / ('input-copy' + self.game.extension)
        self.source.write_bytes(self.raw)
        self.document = self.adapter.read_save(self.source)

    def editable_value(self):
        for field in self.adapter.fields_for(self.document):
            original = field.value(self.document.payload)
            for value in (field.minimum, field.maximum):
                if value != original:
                    try:
                        self.adapter.stage(self.document, {}, field.id, value)
                    except SaveError:
                        continue  # Some mapped fields have record dependencies.
                    return field, original, value
        self.fail('Fixture must contain an editable existing record.')

    def test_noop_stage_unstage_review_and_surgical_roundtrip(self):
        self.assertEqual(self.adapter.serialize(self.document, {}), self.raw)
        field, original, value = self.editable_value()
        pending = {}
        changes = self.adapter.stage(self.document, pending, field.id, value)
        self.assertEqual(pending, {})
        self.assertEqual(changes, {field.id: value})
        self.assertEqual(self.adapter.stage(self.document, changes, field.id, original), {})
        self.assertEqual(changes, {field.id: value})
        self.assertEqual([(row.id, before, after) for row, before, after in self.adapter.review(self.document, changes)],
                         [(field.id, original, value)])
        encoded = self.adapter.serialize(self.document, changes)
        reopened = self.adapter.decode(encoded)
        self.assertEqual(reopened.payload, self.adapter.changed_payload(self.document, changes))
        self.assertEqual(field.value(reopened.payload), value)
        allowed = set(range(field.offset, field.offset + field.size)) | set(self.payload_integrity_offsets)
        touched = {offset for offset, (before, after) in enumerate(zip(self.document.payload, reopened.payload))
                   if before != after}
        self.assertTrue(touched)
        self.assertLessEqual(touched, allowed)
        self.assertEqual(len(reopened.payload), len(self.document.payload))
        self.assertEqual(self.document.raw, self.raw)
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_unknown_fields_invalid_values_and_foreign_identity_rejected(self):
        field, _original, _value = self.editable_value()
        for key, value in (('__unmapped__', 1), (field.id, field.maximum + 1), (field.id, True)):
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                self.adapter.stage(self.document, {}, key, value)
        from dataclasses import replace
        tampered = replace(self.document, payload=self.document.payload[:-1] + bytes([self.document.payload[-1] ^ 1]))
        with self.assertRaises(SaveError):
            self.adapter.serialize(tampered, {})
        foreign = replace(self.document, format=replace(self.document.format, id='different_platform'))
        for action in (lambda: self.adapter.fields_for(foreign),
                       lambda: self.adapter.stage(foreign, {}, field.id, field.minimum),
                       lambda: self.adapter.serialize(foreign, {}),
                       lambda: self.adapter.save_as(foreign, {}, self.folder / ('foreign' + self.game.extension))):
            with self.assertRaises(SaveError):
                action()
        self.assertFalse((self.folder / ('foreign' + self.game.extension)).exists())

    def test_backup_restore_new_destination_and_changed_source_safety(self):
        snapshot = self.adapter.backup(self.document)
        self.assertEqual(snapshot.read_bytes(), self.raw)
        edited = self.adapter.save_as(self.document, {}, self.folder / ('output' + self.game.extension))
        self.assertEqual(edited.raw, self.raw)
        with self.assertRaises(FileExistsError):
            self.adapter.save_as(self.document, {}, edited.source)
        self.assertEqual(edited.source.read_bytes(), self.raw)
        restored = self.adapter.restore(snapshot, self.folder / ('restored' + self.game.extension))
        self.assertEqual(restored.read_bytes(), self.raw)
        altered = self.raw[:-1] + bytes([self.raw[-1] ^ 1])
        self.source.write_bytes(altered)
        destination = self.folder / ('changed-source' + self.game.extension)
        with self.assertRaises(SaveError):
            self.adapter.save_as(self.document, {}, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(self.source.read_bytes(), altered)
