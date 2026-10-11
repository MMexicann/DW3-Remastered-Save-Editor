"""Adversarial procedural Origins pending-edit validation; no player saves."""
from copy import deepcopy
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.origins import origins_parser as backend
from tests.test_origins_parser import fixture


class OriginsPendingSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = backend.decode(fixture())

    def test_max_cannot_launder_or_retain_invalid_pending_edits(self):
        for pending in ({'gold': -1}, {'gold': True}, {'gold': '10'},
                        {'gold': 1_000_000}, {'__unmapped__': 1}):
            original = deepcopy(pending)
            for group in (None, 'Resources', 'unmatched group'):
                with self.subTest(pending=pending, group=group), self.assertRaises(SaveError):
                    backend.maximums(self.document, pending, group)
            with self.assertRaises(SaveError):
                backend.limit_values(self.document, pending, ['skill_points'])
            self.assertEqual(pending, original)

    def test_staging_rejects_invalid_other_fields_without_mutating_input(self):
        for pending in ({'gold': -1}, {'gold': True}, {'__unmapped__': 1}):
            original = deepcopy(pending)
            with self.subTest(pending=pending), self.assertRaises(SaveError):
                backend.stage(self.document, pending, 'skill_points', 1)
            self.assertEqual(pending, original)

    def test_malformed_pending_containers_and_keys_raise_save_error(self):
        for pending in (None, [], [('gold', 1)], {'gold': 1, 3: 1}, {None: 1}):
            for operation in (
                    lambda: backend.stage(self.document, pending, 'gold', 1),
                    lambda: backend.limit_values(self.document, pending, []),
                    lambda: backend.maximums(self.document, pending, 'unmatched group'),
                    lambda: backend.review(self.document, pending),
                    lambda: backend.serialize(self.document, pending)):
                with self.subTest(pending=pending), self.assertRaises(SaveError):
                    operation()

    def test_valid_mixed_edits_remain_immutable_and_unusual_original_can_unstage(self):
        document = backend.decode(fixture(gold=1_000_001, skill_points=1001))
        unchanged = {'gold': 1_000_001, 'skill_points': 1001}
        self.assertEqual(backend.stage(document, unchanged, 'gold', 1_000_001),
                         {'skill_points': 1001})
        self.assertEqual(backend.serialize(document, unchanged), document.raw)
        self.assertEqual(backend.maximums(document, unchanged, 'unmatched group'), unchanged)
        self.assertEqual(backend.limit_values(document, unchanged, ['gold', 'skill_points']), {})
        pending = backend.stage(document, {}, 'gold', 10)
        mixed = backend.stage(document, pending, 'skill_points', 20)
        self.assertEqual(pending, {'gold': 10})
        self.assertEqual(backend.stage(document, mixed, 'gold', 1_000_001),
                         {'skill_points': 20})
        self.assertEqual(backend.stage(document, mixed, 'skill_points', 1001),
                         {'gold': 10})
        reopened = backend.decode(backend.serialize(document, mixed))
        allowed = set(range(0x69b, 0x69f)) | set(range(0xa87, 0xa89))
        self.assertLessEqual({i for i, (before, after) in
                             enumerate(zip(document.payload, reopened.payload)) if before != after}, allowed)


if __name__ == '__main__':
    unittest.main()
