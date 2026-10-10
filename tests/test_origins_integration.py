"""Native mapped-record integration on generated, integrity-valid slot copies.

The offsets below are independent test expectations, not imports of the mapping
tables. These cases prove dispatch, bounds and surgical writes, not game loading.
"""
from functools import lru_cache
from pathlib import Path
import tempfile
import unittest

from koei_editor.game_registry import get_game
from koei_editor.games.dw3.models import SaveError
import koei_editor.games.origins.origins_codec as codec
import koei_editor.games.origins.origins_parser as parser
from tests.test_origins_parser import fixture


LAYOUTS = {16: (0x136e, 0x1f64b, 0x1567),
           17: (0x136e, 0x1f64c, 0x1567),
           29: (0x1436, 0x1f716, 0x162f)}
HISTORY_BASES = {16: 0x210a1, 17: 0x210a2, 29: 0x21365}
HISTORY_IDS = tuple(range(16)) + (19, 22, 24, 25, 26, 27, 39, 40, 42, 44, 46,
                                 49, 51, 56, 57, 59, 62, 65, 68)


@lru_cache(maxsize=6)
def mapped_fixture(revision, high_resources=False):
    document = parser.decode(fixture(revision, gold=1000001 if high_resources else 3456,
                                     skill_points=1001 if high_resources else 123))
    payload = bytearray(document.payload)
    bonds, peace, weapons = LAYOUTS[revision]
    # Unformed bonds and unoccupied inventory must not become editable records.
    for index in range(101):
        offset = bonds + index * 5
        payload[offset:offset + 5] = b'\x00\xa6\x00\x00\xb7'
    for index in range(1000):
        offset = weapons + index * 27
        payload[offset:offset + 27] = b'\xff\xff' + b'\xa7' * 25
    for index in range(13):
        offset = peace + index * 2
        payload[offset:offset + 2] = (400 + index).to_bytes(2, 'little')
    payload[peace + 4:peace + 6] = (10001).to_bytes(2, 'little')
    for index, level, training in ((7, 2, 1), (9, 4, 1000), (10, 6, 1)):
        offset = bonds + index * 5
        payload[offset] = level
        payload[offset + 2:offset + 4] = training.to_bytes(2, 'little')
    for index, weapon_id, upgrade in ((43, 175, 17), (44, 300, 99),
                                      (45, 1, 100), (46, 230, 0), (47, 7, 17),
                                      (850, 175, 17), (999, 175, 17)):
        offset = weapons + index * 27
        payload[offset:offset + 2] = weapon_id.to_bytes(2, 'little')
        payload[offset + 2] = upgrade
    history = HISTORY_BASES[revision]
    payload[history:history + 1000] = b'\xa7' * 1000
    for index in HISTORY_IDS:
        payload[history + index] = 0
    payload[history] = 1
    payload[history + 19] = 2
    payload[history + 16] = payload[history + 70] = 0
    return codec.encode(bytes(payload), document.seed, 'slot')


class OriginsMappedIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.adapter = get_game('origins').get_scalar_adapter()

    def test_all_revisions_stage_bonds_peace_reinforcement_and_history_surgically(self):
        for revision, (bonds, peace, weapons) in LAYOUTS.items():
            with self.subTest(revision=revision):
                raw = mapped_fixture(revision)
                document = self.adapter.decode(raw)
                self.assertEqual(self.adapter.serialize(document, {}), raw)
                pending = {}
                requested = {'bond_7_level': 5, 'peace_8': 10000,
                             'weapon_0043_upgrade': 99, 'weapon_0046_upgrade': 99,
                             'battle_history_68': 1}
                for key, value in requested.items():
                    pending = self.adapter.stage(document, pending, key, value)
                self.assertEqual(pending, requested)
                expected = bytearray(document.payload)
                expected[bonds + 7 * 5] = 5
                expected[peace + 16:peace + 18] = (10000).to_bytes(2, 'little')
                expected[weapons + 43 * 27 + 2] = 99
                expected[weapons + 46 * 27 + 2] = 99
                expected[HISTORY_BASES[revision] + 68] = 1
                edited_raw = self.adapter.serialize(document, pending)
                edited = self.adapter.decode(edited_raw)
                self.assertEqual(edited.payload, bytes(expected))
                allowed = {bonds + 7 * 5, peace + 16, peace + 17,
                           weapons + 43 * 27 + 2, weapons + 46 * 27 + 2,
                           HISTORY_BASES[revision] + 68}
                touched = {index for index, (before, after) in
                           enumerate(zip(document.payload, edited.payload)) if before != after}
                self.assertEqual(touched, allowed)
                touched_raw = {index for index, (before, after) in
                               enumerate(zip(raw, edited_raw)) if before != after}
                self.assertLessEqual(touched_raw, {0, 1} | {index + 4 for index in allowed})
                self.assertEqual(edited_raw[2:4], raw[2:4])
                self.assertEqual(edited.seed, document.seed)
                self.assertEqual({field.id: after for field, _before, after in
                                  self.adapter.review(document, pending)}, requested)
                self.assertEqual(document.raw, raw)

    def test_bulk_max_preserves_training_and_high_or_unknown_records(self):
        for revision in LAYOUTS:
            with self.subTest(revision=revision):
                document = self.adapter.decode(mapped_fixture(revision, high_resources=True))
                fields = self.adapter.field_map(document)
                self.assertFalse(fields['bond_7_training'].maxable)
                excluded = ('peace_2', 'bond_0_level', 'bond_9_training',
                            'bond_10_level', 'weapon_0044_upgrade',
                            'weapon_0045_upgrade', 'weapon_0047_upgrade',
                            'weapon_0850_upgrade', 'weapon_0999_upgrade',
                            'battle_history_16', 'battle_history_19', 'battle_history_70')
                for key in excluded:
                    self.assertNotIn(key, fields)
                    with self.assertRaises(SaveError):
                        self.adapter.stage(document, {}, key, 1)
                    with self.assertRaises(SaveError):
                        self.adapter.serialize(document, {key: 1})
                pending = self.adapter.stage(document, {}, 'bond_7_training', 3)
                maximums = self.adapter.maximums(document, pending)
                self.assertEqual(maximums['bond_7_training'], 3)
                self.assertEqual(maximums['bond_7_level'], 5)
                self.assertEqual(maximums['bond_9_level'], 5)
                self.assertEqual(maximums['weapon_0043_upgrade'], 99)
                self.assertEqual(maximums['weapon_0046_upgrade'], 99)
                for key in ('gold', 'skill_points'):
                    self.assertNotIn(key, maximums)
                without_training = self.adapter.maximums(document, {})
                self.assertNotIn('bond_7_training', without_training)
                for key in fields:
                    if key.startswith('battle_history_'):
                        self.assertFalse(fields[key].maxable)
                        self.assertNotIn(key, maximums)
                self.assertNotIn('bond_7_training', self.adapter.limit_values(
                    document, {}, fields))
                edited = self.adapter.decode(self.adapter.serialize(document, without_training))
                expected = bytearray(document.payload)
                for key, value in without_training.items():
                    field = fields[key]
                    expected[field.offset:field.offset + field.size] = value.to_bytes(field.size, 'little')
                # Exact body comparison covers unknown flags, traits, references,
                # reserved inventory and every high value, including training.
                self.assertEqual(edited.payload, bytes(expected))
                self.assertEqual(fields['bond_7_training'].value(edited.payload), 1)
                self.assertEqual(fields['gold'].value(edited.payload), 1000001)
                self.assertEqual(fields['skill_points'].value(edited.payload), 1001)

    def test_history_is_manual_monotonic_after_save_and_preserves_other_flags(self):
        for revision in LAYOUTS:
            with self.subTest(revision=revision):
                document = self.adapter.decode(mapped_fixture(revision))
                fields = self.adapter.field_map(document)
                self.assertEqual(sum(key.startswith('battle_history_') for key in fields), 34)
                self.assertEqual(fields['battle_history_0'].minimum, 1)
                self.assertEqual(fields['battle_history_68'].minimum, 0)
                self.assertEqual(self.adapter.stage(document, {}, 'battle_history_0', 1), {})
                for operation in (lambda: self.adapter.stage(document, {}, 'battle_history_0', 0),
                                  lambda: self.adapter.serialize(document, {'battle_history_0': 0}),
                                  lambda: self.adapter.stage(document, {}, 'battle_history_68', 2)):
                    with self.assertRaises(SaveError):
                        operation()
                pending = self.adapter.stage(document, {}, 'battle_history_68', 1)
                self.assertEqual(self.adapter.stage(document, pending, 'battle_history_68', 0), {})
                maximums = self.adapter.maximums(document, pending, 'Battle clear history')
                self.assertEqual(maximums, pending)
                self.assertEqual(self.adapter.limit_values(document, pending,
                                                          ('battle_history_0', 'battle_history_68')), {})
                reopened = self.adapter.decode(self.adapter.serialize(document, pending))
                with self.assertRaises(SaveError):
                    self.adapter.stage(reopened, {}, 'battle_history_68', 0)
                expected = bytearray(document.payload)
                expected[HISTORY_BASES[revision] + 68] = 1
                self.assertEqual(reopened.payload, bytes(expected))

    def test_mapped_changes_save_restore_and_keep_the_opened_copy(self):
        area = Path(__file__).resolve().parents[1] / '.test-runs'
        area.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=area) as folder:
            source = Path(folder) / 'SLOT0000.dat'
            original = mapped_fixture(29)
            source.write_bytes(original)
            document = self.adapter.read_save(source)
            pending = {'bond_7_level': 5, 'peace_8': 10000, 'weapon_0043_upgrade': 99,
                       'weapon_0046_upgrade': 99, 'battle_history_68': 1}
            snapshot = self.adapter.backup(document)
            target = Path(folder) / 'edited.dat'
            edited = self.adapter.save_as(document, pending, target)
            self.assertEqual(edited.source, target)
            self.assertEqual(target.read_bytes(), self.adapter.serialize(document, pending))
            restored = Path(folder) / 'restored.dat'
            self.adapter.restore(snapshot, restored)
            self.assertEqual(restored.read_bytes(), original)
            self.assertEqual(source.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                self.adapter.save_as(document, pending, target)


if __name__ == '__main__':
    unittest.main()
