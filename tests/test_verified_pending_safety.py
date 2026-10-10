"""Adversarial pending-edit and snapshot boundaries on generated PC copies."""
from dataclasses import replace
from types import MappingProxyType
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.game_registry import get_game
from koei_editor.shared import verified_editor as backend
from tests.test_verified_editors import synthetic_raw
from tests.test_verified_snapshot_review import reseed


class VerifiedPendingSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {game: backend.decode(synthetic_raw(game), game)
                         for game in ('dw8xl', 'pw3')}

    def test_malformed_pending_edits_cannot_survive_stage_unstage_or_max(self):
        for game, document in self.documents.items():
            adapter = get_game(game).get_scalar_adapter()
            field = adapter.fields_for(document)[0]
            original = field.value(document.payload)
            malformed = (None, [], [(field.id, 1)], field.id,
                         {'unmapped': 1}, {field.id: True},
                         {field.id: field.maximum + 1})
            for changes in malformed:
                actions = (lambda: adapter.stage(document, changes, field.id, field.minimum),
                           lambda: adapter.stage(document, changes, field.id, original),
                           lambda: adapter.limit_values(document, changes, [field.id]),
                           lambda: adapter.maximums(document, changes),
                           lambda: adapter.review(document, changes),
                           lambda: adapter.changed_payload(document, changes),
                           lambda: adapter.serialize(document, changes))
                for index, action in enumerate(actions):
                    with self.subTest(game=game, changes=changes, action=index):
                        with self.assertRaises(SaveError):
                            action()

    def test_snapshot_tampering_rejected_before_fields_or_staging(self):
        for game, document in self.documents.items():
            adapter = get_game(game).get_scalar_adapter()
            field = adapter.fields_for(document)[0]
            payload = bytearray(document.payload)
            payload[field.offset] ^= 1
            forged = (replace(document, payload=bytes(payload)),
                      replace(document, raw=bytearray(document.raw)),
                      replace(document, payload=bytearray(document.payload)),
                      replace(document, seed=float(document.seed)))
            for snapshot in forged:
                for operation in ('fields_for', 'field_map', 'maximums', 'stage', 'review', 'changed_payload'):
                    arguments = {'fields_for': (), 'field_map': (), 'maximums': ({},),
                                 'stage': ({}, field.id, field.minimum), 'review': ({},),
                                 'changed_payload': ({},)}[operation]
                    with self.subTest(game=game, operation=operation,
                                      seed_type=type(snapshot.seed), payload_type=type(snapshot.payload)):
                        with self.assertRaises(SaveError):
                            getattr(adapter, operation)(snapshot, *arguments)

    def test_valid_read_only_mapping_stages_without_mutating_input(self):
        for game, document in self.documents.items():
            field = backend.fields_for(document)[0]
            value = next(value for value in (field.minimum, field.maximum)
                         if value != field.value(document.payload))
            changes = MappingProxyType({field.id: value})
            self.assertEqual(backend.stage(document, changes, field.id,
                                           field.value(document.payload)), {})
            self.assertEqual(dict(changes), {field.id: value})
            self.assertEqual(len(backend.review(document, changes)), 1)
            self.assertEqual(backend.serialize(document, {}), document.raw)

    def test_unusual_original_pending_values_preserve_bytes_and_can_be_unstaged(self):
        for game, document in self.documents.items():
            field = backend.fields_for(document)[0]
            original = field.maximum + 7
            payload = bytearray(document.payload)
            payload[field.offset:field.offset + field.size] = original.to_bytes(field.size, 'little')
            document = backend.decode(reseed(replace(document, payload=bytes(payload)), document.seed), game)
            pending = {field.id: original}
            self.assertEqual(backend.serialize(document, pending), document.raw)
            self.assertEqual(backend.stage(document, pending, field.id, original), {})
            self.assertEqual(pending, {field.id: original})
            maximums = backend.maximums(document, pending)
            self.assertEqual(maximums[field.id], original)
            reopened = backend.decode(backend.serialize(document, maximums), game)
            self.assertEqual(field.value(reopened.payload), original)
            with self.assertRaises(SaveError):
                backend.stage(document, {field.id: original + 1}, field.id, original)

    def test_unobserved_original_compatibility_survives_other_edits_and_max(self):
        document = self.documents['dw8xl']
        field = backend.field_map(document)['officer_0_compatibility_0']
        payload = bytearray(document.payload)
        payload[field.offset] = 13  # Neither a validated star value nor a valid deliberate edit.
        document = backend.decode(reseed(replace(document, payload=bytes(payload)), document.seed), 'dw8xl')
        pending = {field.id: 13}
        self.assertEqual(backend.serialize(document, pending), document.raw)
        self.assertEqual(backend.stage(document, pending, field.id, 13), {})
        changes = backend.stage(document, pending, 'gold', 123)
        changes = backend.maximums(document, changes)
        reopened = backend.decode(backend.serialize(document, changes), 'dw8xl')
        self.assertEqual(field.value(reopened.payload), 13)
        with self.assertRaises(SaveError):
            backend.serialize(self.documents['dw8xl'], pending)
