"""DW7 XL native format regressions; generated data is not game-load evidence."""
from dataclasses import FrozenInstanceError, replace
import hashlib
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import koei_editor.games.dw7xl.dw7xl_codec as codec
import koei_editor.games.dw7xl.dw7xl_parser as backend
from koei_editor.games.dw3.models import SaveError
from tests.scalar_contract import ScalarContractTests


def reference_encode(payload, seed=0xD4A2):
    """Independent arithmetic expression of the two native cipher loops."""
    values = list(struct.unpack('<' + 'I' * ((len(payload) - 3) // 4), payload[:-3]))
    state = seed
    words = []
    for value in values:
        for _ in (0, 1):
            state = (1528461393 * state + 52814) % 4294967296
        words.append(value ^ state)
    tail = seed % 256
    tail_bytes = []
    for value in payload[-3:]:
        for _ in (0, 1):
            tail = (81 * tail + 78) % 256
        tail_bytes.append(value ^ tail)
    checksum = sum(int.from_bytes(payload[i:i + 2], 'little')
                   for i in range(0, len(payload) - 1, 2)) % 65536
    return struct.pack('<HH', checksum, seed) + struct.pack('<' + 'I' * len(words), *words) + bytes(tail_bytes)


def synthetic_raw(seed=0xD4A2):
    payload = bytearray((i * 73 + 41) % 256 for i in range(codec.PAYLOAD_SIZE))
    payload[:4] = codec.MAGIC
    for field in backend.FORMAT.fields:
        payload[field.offset:field.offset + field.size] = field.minimum.to_bytes(field.size, 'little')
    return reference_encode(payload, seed)


class DW7XLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = synthetic_raw()

    def setUp(self):
        self.document = backend.decode(self.raw)

    def test_native_size_magic_and_two_step_cipher_roundtrip(self):
        for seed in (0, 1, 0xD4A2, 65535):
            raw = synthetic_raw(seed)
            payload, decoded_seed = codec.decode(raw)
            self.assertEqual(decoded_seed, seed)
            self.assertEqual(codec.encode(payload, seed), raw)
            self.assertEqual(payload[:4], codec.MAGIC)
            self.assertEqual(backend.serialize(backend.decode(raw), {}), raw)

    def test_header_word_stream_and_trailing_stream_known_answers(self):
        payload = self.document.payload
        seed = self.document.seed
        raw = codec.encode(payload, seed)
        state = seed
        for _ in range(2):
            state = (state * 1528461393 + 52814) % 4294967296
        self.assertEqual(int.from_bytes(raw[4:8], 'little'), int.from_bytes(payload[:4], 'little') ^ state)
        tail = seed & 255
        for i, value in enumerate(payload[-3:]):
            for _ in range(2):
                tail = (tail * 81 + 78) % 256
            self.assertEqual(raw[-3 + i], value ^ tail)

    def test_ciphertext_checksum_and_seed_corruption_rejected(self):
        for offset in (0, 1, 2, 3, 4, 18, len(self.raw) - 3, len(self.raw) - 2):
            changed = bytearray(self.raw)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                backend.decode(changed)

    def test_native_last_odd_byte_is_uncovered_and_preserved(self):
        changed = self.raw[:-1] + bytes([self.raw[-1] ^ 1])
        document = backend.decode(changed)
        self.assertNotEqual(document.payload[-1], self.document.payload[-1])
        self.assertEqual(backend.serialize(document, {}), changed)
        edited = backend.serialize(document, {'gold': 123})
        self.assertEqual(edited[-1], changed[-1])

    def test_foreign_magic_with_valid_checksum_rejected(self):
        changed = bytearray(self.document.payload)
        changed[:4] = b'\x00\x02\x10\x13'
        raw = reference_encode(changed)
        with self.assertRaisesRegex(SaveError, 'title/revision'):
            backend.decode(raw)

    def test_wrong_sizes_and_nonbyte_inputs_rejected_before_cipher(self):
        for raw in (b'', self.raw[:-1], self.raw + b'x', 470307, True, [0] * 8, 'save.dat'):
            with self.subTest(type=type(raw)), self.assertRaises(SaveError):
                backend.decode(raw)

    def test_mutable_inputs_frozen_and_memoryviews_count_bytes(self):
        mutable = bytearray(self.raw)
        document = backend.decode(memoryview(mutable))
        mutable[0] ^= 1
        self.assertEqual(document.raw, self.raw)
        self.assertIs(type(document.raw), bytes)
        self.assertIs(type(document.payload), bytes)

    def test_targeted_edits_preserve_unknown_bytes_seeds_and_unrelated_fields(self):
        edits = {'gold': 456789, 'officer_0_health': 875,
                 'officer_64_skill_points': 9876, 'officer_20_speed': 92}
        document = self.document
        expected = bytearray(document.payload)
        allowed = set()
        for key, value in edits.items():
            field = backend.FIELD_MAP[key]
            expected[field.offset:field.offset + field.size] = value.to_bytes(field.size, 'little')
            allowed.update(range(field.offset, field.offset + field.size))
        output = backend.serialize(document, edits)
        reread = backend.decode(output)
        self.assertEqual(reread.payload, expected)
        self.assertEqual(reread.seed, document.seed)
        self.assertEqual(output[2:4], document.raw[2:4])
        actual = {i for i, (a, b) in enumerate(zip(document.payload, reread.payload)) if a != b}
        self.assertLessEqual(actual, allowed)
        self.assertEqual(document.raw, self.raw)

    def test_staging_unstage_and_review_are_immutable(self):
        original = {}
        pending = backend.stage(self.document, original, 'gold', 123)
        self.assertEqual(original, {})
        self.assertEqual(pending, {'gold': 123})
        self.assertEqual(backend.stage(self.document, pending, 'gold', 0), {})
        rows = backend.review(self.document, pending)
        self.assertEqual([(field.id, before, after) for field, before, after in rows], [('gold', 0, 123)])

    def test_unknown_fields_bool_and_native_bounds_rejected(self):
        for key, value in (('unmapped', 1), ('gold', True), ('gold', 1000000),
                           ('officer_0_attack', 0), ('officer_0_attack', 1401),
                           ('officer_1_skill_points', 10000)):
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, value)
            with self.subTest(serialized_key=key), self.assertRaises(SaveError):
                backend.serialize(self.document, {key: value})

    def test_max_preserves_higher_existing_values_and_unknown_systems(self):
        payload = bytearray(self.document.payload)
        struct.pack_into('<I', payload, backend.FIELD_MAP['gold'].offset, 4000000)
        struct.pack_into('<H', payload, backend.FIELD_MAP['officer_0_health'].offset, 1234)
        struct.pack_into('<H', payload, backend.FIELD_MAP['officer_1_attack'].offset, 0)
        document = backend.decode(reference_encode(payload))
        pending = backend.maximums(document, {})
        self.assertNotIn('gold', pending)
        self.assertNotIn('officer_0_health', pending)
        self.assertNotIn('officer_1_attack', pending)
        result = backend.decode(backend.serialize(document, pending))
        self.assertEqual(backend.FIELD_MAP['gold'].value(result.payload), 4000000)
        self.assertEqual(backend.FIELD_MAP['officer_0_health'].value(result.payload), 1234)
        self.assertEqual(backend.FIELD_MAP['officer_1_attack'].value(result.payload), 0)
        self.assertEqual(backend.stage(document, {'gold': 123}, 'gold', 4000000), {})
        touched = set()
        for key in pending:
            field = backend.FIELD_MAP[key]
            touched.update(range(field.offset, field.offset + field.size))
        actual = {i for i, (a, b) in enumerate(zip(document.payload, result.payload)) if a != b}
        self.assertLessEqual(actual, touched)
        self.assertEqual(result.payload[backend.OFFICER_BASE + backend.OFFICER_COUNT * backend.OFFICER_STRIDE:],
                         document.payload[backend.OFFICER_BASE + backend.OFFICER_COUNT * backend.OFFICER_STRIDE:])

    def test_forged_snapshots_and_platforms_rejected(self):
        class EqualFormat:
            def __eq__(self, other):
                return True

        d = self.document
        for forged in (replace(d, raw=bytearray(d.raw)), replace(d, payload=bytearray(d.payload)),
                       replace(d, payload=d.payload[:-1] + bytes([d.payload[-1] ^ 1])),
                       replace(d, seed=True), replace(d, seed=d.seed ^ 1),
                       replace(d, format=replace(d.format, id='dw7_ps3')), replace(d, format=EqualFormat())):
            with self.subTest(type=type(forged.raw)), self.assertRaises(SaveError):
                backend.serialize(forged, {})
        with self.assertRaises(FrozenInstanceError):
            d.seed = 1
        with self.assertRaises(SaveError):
            backend.decode(self.raw, 'dw8xl')

    def test_read_only_inspection_does_not_create_fields_or_guess_levels(self):
        self.assertEqual(len(backend.fields_for(self.document)), 456)
        self.assertFalse(any('level' in f.id or 'story' in f.id for f in backend.fields_for(self.document)))
        self.assertEqual(len(backend.inspection_rows(self.document)), 130)
        self.assertEqual(backend.serialize(self.document, {}), self.raw)

    def test_active_equipped_weapon_requires_an_existing_owned_reference(self):
        payload = bytearray(self.document.payload)
        officer = backend.OFFICER_BASE
        struct.pack_into('<HHH', payload, officer + 18, 2, 3, 0)
        struct.pack_into('<H', payload, backend.WEAPON_BASE + 3 * backend.WEAPON_STRIDE + 4, 0x21)
        document = backend.decode(reference_encode(payload))
        key = 'officer_0_active_weapon'
        changes = backend.stage(document, {}, key, 1)
        changed = backend.decode(backend.serialize(document, changes))
        expected = bytearray(document.payload)
        struct.pack_into('<H', expected, officer + 22, 1)
        self.assertEqual(changed.payload, bytes(expected))
        self.assertEqual(backend.stage(document, changes, key, 0), {})
        self.assertNotIn(key, backend.maximums(document, {}, 'Equipment'))
        for reference, flags in ((65535, 1), (backend.WEAPON_COUNT, 1), (3, 0x20)):
            broken = bytearray(payload)
            struct.pack_into('<H', broken, officer + 20, reference)
            struct.pack_into('<H', broken, backend.WEAPON_BASE + 3 * backend.WEAPON_STRIDE + 4, flags)
            malformed = backend.decode(reference_encode(broken))
            with self.subTest(reference=reference, flags=flags):
                with self.assertRaises(SaveError):
                    backend.stage(malformed, {}, key, 1)
                with self.assertRaises(SaveError):
                    backend.serialize(malformed, {key: 1})

    def test_inventory_inspection_preserves_unusual_meter_and_flag_bits(self):
        payload = bytearray(self.document.payload)
        struct.pack_into('<HH', payload, backend.WEAPON_BASE + 4, 0xF121, 65000)
        document = backend.decode(reference_encode(payload))
        rows = backend.weapons(document)
        self.assertEqual(len(rows), 1738)
        self.assertEqual(rows[0], {'slot': 1, 'owned': True, 'flags': 0xF121, 'seal_meter': 65000})
        self.assertEqual(backend.serialize(document, {}), document.raw)

    def test_live_folders_and_resolved_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            live = root / 'KoeiTecmo' / 'Dynasty Warriors 7 DX' / 'Savedata'
            live.mkdir(parents=True)
            source = live / 'save.dat'
            source.write_bytes(self.raw)
            link = root / 'alias.dat'
            link.symlink_to(source)
            for path in (source, link):
                with self.subTest(path=path), self.assertRaises(SaveError):
                    backend.read_save(path)
            copy = root / 'input.dat'
            copy.write_bytes(self.raw)
            document = backend.read_save(copy)
            with self.assertRaises(SaveError):
                backend.save_as(document, {}, live / 'new.dat')
            forged = replace(document, source=link)
            with self.assertRaises(SaveError):
                backend.backup(forged)
            with self.assertRaises(SaveError):
                backend.save_as(forged, {}, root / 'new.dat')
            snapshot = backend.backup(document)
            with self.assertRaises(SaveError):
                backend.restore(snapshot, live / 'restore.dat')


class DW7XLScalarContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'dw7xl'

    def fixture_bytes(self):
        return synthetic_raw()

    def test_backups_restore_new_destinations_and_changed_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.dat'
            source.write_bytes(self.raw)
            document = backend.read_save(source)
            snapshot = backend.backup(document)
            self.assertEqual(snapshot.read_bytes(), self.raw)
            output = backend.save_as(document, {'gold': 42}, root / 'edited.dat')
            self.assertEqual(backend.FIELD_MAP['gold'].value(output.payload), 42)
            self.assertEqual(source.read_bytes(), self.raw)
            restored = backend.restore(snapshot, root / 'restored.dat')
            self.assertEqual(restored.read_bytes(), self.raw)
            with self.assertRaises(FileExistsError):
                backend.save_as(document, {}, output.source)
            source.write_bytes(self.raw[:-1] + bytes([self.raw[-1] ^ 1]))
            with self.assertRaisesRegex(SaveError, 'changed on disk'):
                backend.save_as(document, {}, root / 'changed-source.dat')
            self.assertFalse((root / 'changed-source.dat').exists())

    @unittest.skipUnless(os.environ.get('DW7XL_SAVE_COPY'), 'Genuine copied PC fixture not configured')
    def test_genuine_copied_fixture_noop_and_targeted_roundtrip(self):
        document = backend.read_save(Path(os.environ['DW7XL_SAVE_COPY']))
        self.assertEqual(backend.serialize(document, {}), document.raw)
        before_hash = hashlib.sha256(document.source.read_bytes()).hexdigest()
        old = backend.FIELD_MAP['gold'].value(document.payload)
        value = 12345 if old != 12345 else 12346
        edited = backend.decode(backend.serialize(document, {'gold': value}))
        self.assertEqual(backend.FIELD_MAP['gold'].value(edited.payload), value)
        allowed = set(range(0xC7C, 0xC80))
        actual = {i for i, (a, b) in enumerate(zip(document.payload, edited.payload)) if a != b}
        self.assertLessEqual(actual, allowed)
        self.assertEqual(hashlib.sha256(document.source.read_bytes()).hexdigest(), before_hash)

    @unittest.skipUnless(os.environ.get('DW7XL_SAVE_COPY'), 'Genuine copied PC fixture not configured')
    def test_genuine_stats_skill_points_and_owned_active_weapon_are_surgical(self):
        document = backend.read_save(Path(os.environ['DW7XL_SAVE_COPY']))
        changes = {}
        for suffix in ('health', 'attack', 'defense', 'power', 'speed', 'skill_points'):
            key = 'officer_0_' + suffix
            field = backend.FIELD_MAP[key]
            old = field.value(document.payload)
            value = old - 1 if old > field.minimum else old + 1
            changes = backend.stage(document, changes, key, value)
        choice = backend.FIELD_MAP['officer_0_active_weapon']
        changes = backend.stage(document, changes, choice.id, 1 - choice.value(document.payload))
        expected = bytearray(document.payload)
        for key, value in changes.items():
            field = backend.FIELD_MAP[key]
            expected[field.offset:field.offset + field.size] = field.encoded(value)
        edited = backend.decode(backend.serialize(document, changes))
        self.assertEqual(edited.payload, bytes(expected))
        self.assertEqual(edited.seed, document.seed)
        self.assertEqual(document.source.read_bytes(), document.raw)


if __name__ == '__main__':
    unittest.main()
