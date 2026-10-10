"""The MUSIC gallery uses IDs 0..41; other BGM slots and NEW markers survive."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from models import Change, SaveError
from save_parser import parse_bytes, read_save
from save_writer import serialize
from save_codec import encrypt
import collection_editor as collection

FIXTURE = PROJECT / 'work' / 'original-upload' / 'GameStatusData.sav'


def sound(document):
    return next(p for p in document.properties['OptionData']['value'] if p['name'] == 'Sound')


def array(document, name='bPlayBGM'):
    return next(p for p in sound(document)['value'] if p['name'] == name)


def without_collection_array(document, owner_name='Sound', array_name='bPlayBGM'):
    owner = next(p for p in document.properties['OptionData']['value'] if p['name'] == owner_name)
    prop = next(p for p in owner['value'] if p['name'] == array_name)
    first, last = prop['tag_offset'], prop['data_offset'] + prop['data_size']
    removed = last - first
    plain = bytearray(document.plaintext[:4 + document.parsed['payload_size']])
    del plain[first:last]
    for parent in (owner, document.properties['OptionData']):
        struct.pack_into('<i', plain, parent['size_offset'], parent['data_size'] - removed)
    struct.pack_into('>I', plain, 0, struct.unpack_from('>I', plain, 0)[0] - removed)
    plain.extend(bytes((-len(plain)) % 16))
    return parse_bytes(encrypt(bytes(plain)))


class MusicCatalogTests(unittest.TestCase):
    def test_native_displayed_catalog_is_exactly_42(self):
        self.assertEqual([r['id'] for r in collection.DATA['music']['rows']], list(range(42)))
        self.assertTrue(all(r['name'] for r in collection.DATA['music']['rows']))
        self.assertEqual(collection.DATA['music']['total'], 100)


@unittest.skipUnless(FIXTURE.exists(), 'The explicitly supplied copied save is required.')
class MusicUnlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_save(FIXTURE)
        cls.digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == cls.digest

    def test_full_unlock_patches_only_displayed_music_flags(self):
        document = self.document
        before = array(document)
        old = array(document, 'bPlayBGM_Old')
        result_bytes, audit = serialize(document, collection.unlock_music_changes(document))
        result = parse_bytes(result_bytes)
        after = array(result)
        self.assertEqual(after['value']['values'][:42], [True] * 42)
        self.assertEqual(after['value']['values'][42:], before['value']['values'][42:])
        self.assertEqual(array(result, 'bPlayBGM_Old')['value'], old['value'])
        self.assertEqual(len(document.plaintext), len(result.plaintext))
        actual = {i for i, (a, b) in enumerate(zip(document.plaintext, result.plaintext)) if a != b}
        expected = {before['data_offset'] + 4 + i for i in range(42) if not before['value']['values'][i]}
        self.assertEqual(actual, expected)
        self.assertEqual(collection.collection_state(result)['music']['owned'], 42)
        self.assertTrue(all(p['reason'] == 'Unlock music gallery' for p in audit['plaintext_changes']))

    def test_single_unlock_preview_and_original_value_use_same_slot(self):
        selected = next(i for i in range(42) if not array(self.document)['value']['values'][i])
        change = Change('collection', selected, 'Music', True)
        self.assertFalse(collection.original_value(self.document, change))
        self.assertTrue(collection.collection_state(self.document, [change])['music']['rows'][selected]['unlocked'])
        raw, _ = serialize(self.document, [change])
        result = parse_bytes(raw)
        expected = list(array(self.document)['value']['values'])
        expected[selected] = True
        self.assertEqual(array(result)['value']['values'], expected)
        self.assertEqual(array(result, 'bPlayBGM_Old')['value'], array(self.document, 'bPlayBGM_Old')['value'])

    def test_bulk_unlock_is_idempotent_and_audio_only_ids_are_rejected(self):
        raw, _ = serialize(self.document, collection.unlock_music_changes(self.document))
        result = parse_bytes(raw)
        again, audit = serialize(result, collection.unlock_music_changes(result))
        self.assertEqual(again, raw)
        self.assertEqual(audit['plaintext_changes'], [])
        for invalid in (42, 44, 45, 50, 93, 99, 100, -1, True, False, 1.0):
            with self.subTest(index=invalid), self.assertRaises(SaveError):
                serialize(self.document, [Change('collection', invalid, 'Music', True)])
        for value in (False, 1, 'true'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                serialize(self.document, [Change('collection', 1, 'Music', value)])

    def test_sparse_save_creates_current_music_flags_and_preserves_acknowledgements(self):
        sparse = without_collection_array(self.document)
        old_before = array(sparse, 'bPlayBGM_Old')['value']
        raw, audit = serialize(sparse, [Change('collection', 3, 'Music', True)])
        result = parse_bytes(raw)
        expected = [False] * 100
        expected[3] = True
        self.assertEqual(array(result)['value']['values'], expected)
        self.assertEqual(array(result, 'bPlayBGM_Old')['value'], old_before)
        self.assertEqual(array(result)['value']['count'], 100)
        self.assertTrue(collection.collection_state(result)['music']['editable'])

    def test_bad_current_array_is_view_only_and_cannot_be_written(self):
        prop = array(self.document)
        damaged = bytearray(self.document.plaintext)
        struct.pack_into('<i', damaged, prop['data_offset'], 99)
        invalid = parse_bytes(encrypt(bytes(damaged)))
        self.assertFalse(collection.collection_state(invalid)['music']['editable'])
        with self.assertRaises(SaveError):
            collection.unlock_music_changes(invalid)
        with self.assertRaises(SaveError):
            serialize(invalid, [Change('collection', 1, 'Music', True)])

    def test_music_and_movies_can_be_unlocked_in_one_batch(self):
        changes = collection.unlock_music_changes(self.document) + collection.unlock_movie_changes(self.document)
        raw, _ = serialize(self.document, changes)
        state = collection.collection_state(parse_bytes(raw))
        self.assertEqual(state['music']['owned'], 42)
        self.assertEqual(state['movies']['owned'], 50)

    def test_missing_music_and_movie_arrays_can_be_inserted_together(self):
        sparse = without_collection_array(self.document)
        sparse = without_collection_array(sparse, 'Edit', 'bPlayMovie')
        old_music = array(sparse, 'bPlayBGM_Old')['value']
        changes = collection.unlock_music_changes(sparse) + collection.unlock_movie_changes(sparse)
        raw, _ = serialize(sparse, changes)
        result = parse_bytes(raw)
        state = collection.collection_state(result)
        self.assertEqual(state['music']['owned'], 42)
        self.assertEqual(state['movies']['owned'], 50)
        self.assertEqual(array(result)['value']['values'][42:], [False] * 58)
        self.assertEqual(array(result, 'bPlayBGM_Old')['value'], old_music)
        again, audit = serialize(result, changes)
        self.assertEqual(again, raw)
        self.assertEqual(audit['plaintext_changes'], [])


if __name__ == '__main__':
    unittest.main()
