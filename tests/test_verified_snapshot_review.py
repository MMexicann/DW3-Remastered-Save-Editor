"""Independent immutable-snapshot/restore checks with generated PC layouts."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import copy_storage
from models import SaveError
import verified_editor as backend
from tests.test_verified_editors import synthetic_raw


def reseed(document, seed):
    inner = (backend.byte_cipher(document.payload, document.format.inner_seed)
             if document.format.inner_seed is not None else document.payload)
    raw = struct.pack('<HH', backend.word_sum(inner), seed) + backend.word_cipher(inner, seed)
    if document.format.inner_seed is not None:
        raw += bytes([(sum(document.payload) & 255) ^ (backend.mix_word(seed) & 255)])
    return raw


class VerifiedSnapshotReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {game: backend.decode(synthetic_raw(game), game)
                         for game in ('dw8xl', 'pw3')}

    def test_equal_mutable_bytes_are_rejected_before_noop_return_or_encoding(self):
        for game, document in self.documents.items():
            for name in ('raw', 'payload'):
                forged = replace(document, **{name: bytearray(getattr(document, name))})
                for changes in ({}, {document.format.fields[0].id: 51}):
                    with self.subTest(game=game, mutable=name, changed=bool(changes)):
                        with self.assertRaises(SaveError):
                            backend.serialize(forged, changes)

    def test_max_preserves_existing_below_minimum_bar_and_skill_slot_values(self):
        document = self.documents['pw3']
        payload = bytearray(document.payload)
        fields = [field for field in backend.fields_for(document) if field.minimum > 0]
        self.assertTrue(fields)
        for field in fields:
            payload[field.offset:field.offset + field.size] = bytes(field.size)
        document = backend.decode(reseed(replace(document, payload=bytes(payload)), document.seed), 'pw3')
        changes = backend.maximums(document, {})
        for field in fields:
            self.assertNotIn(field.id, changes)
        reopened = backend.decode(backend.serialize(document, changes), 'pw3')
        for field in fields:
            self.assertEqual(field.value(reopened.payload), 0)

    def test_boolean_and_float_seed_are_rejected_even_when_numerically_equal(self):
        for game, document in self.documents.items():
            for seed in (0, 1):
                valid = backend.decode(reseed(document, seed), game)
                self.assertEqual(backend.serialize(valid, {}), valid.raw)
                for invalid in (bool(seed), float(seed)):
                    with self.subTest(game=game, original_seed=seed, invalid_type=type(invalid)):
                        with self.assertRaises(SaveError):
                            backend.serialize(replace(valid, seed=invalid), {})

    def test_foreign_document_and_layout_raise_save_error(self):
        document = self.documents['pw3']
        values = (None, object(), SimpleNamespace(**vars(document)),
                  replace(document, format=None),
                  replace(document, format=replace(document.format, id=[])),
                  replace(document, format=replace(document.format, size=document.format.size + 4)))
        for value in values:
            with self.subTest(document_type=type(value)):
                with self.assertRaises(SaveError):
                    backend.serialize(value, {})

    def test_restore_qualifies_same_bytes_written_after_backup_and_manifest_swap(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for game, document in self.documents.items():
                source = folder / (game + '.dat')
                source.write_bytes(document.raw)
                backup = backend.backup(backend.read_save(source, game))
                destination = folder / (game + '-restored.dat')
                genuine_restore = copy_storage.restore_snapshot

                def swap_backup(*args, **kwargs):
                    # A coherent new manifest must not authorize a corrupt native file.
                    damaged = bytearray(backup.read_bytes())
                    damaged[4 + 101] ^= 1
                    damaged = bytes(damaged)
                    backup.write_bytes(damaged)
                    manifest_path = backup.with_suffix('.json')
                    metadata = json.loads(manifest_path.read_text())
                    metadata['sha256'] = hashlib.sha256(damaged).hexdigest()
                    manifest_path.write_text(json.dumps(metadata))
                    return genuine_restore(*args, **kwargs)

                with self.subTest(game=game), patch.object(backend, 'restore_snapshot', side_effect=swap_backup):
                    with self.assertRaises(SaveError):
                        backend.restore(backup, destination, game)
                self.assertFalse(destination.exists())

    def test_unchanged_restore_preserves_snapshot_and_rejects_wrong_game(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for game, document in self.documents.items():
                source = folder / (game + '.dat')
                source.write_bytes(document.raw)
                backup = backend.backup(backend.read_save(source, game))
                restored = folder / (game + '-restored.dat')
                backend.restore(backup, restored, game)
                self.assertEqual(hashlib.sha256(restored.read_bytes()).digest(),
                                 hashlib.sha256(document.raw).digest())
                self.assertEqual(source.read_bytes(), document.raw)
                wrong = folder / (game + '-wrong.dat')
                with self.assertRaises(SaveError):
                    backend.restore(backup, wrong, 'pw3' if game == 'dw8xl' else 'dw8xl')
                self.assertFalse(wrong.exists())


if __name__ == '__main__':
    unittest.main()
