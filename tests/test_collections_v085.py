"""Movie/music gallery unlocks preserve native acknowledgement state."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT
sys.path.insert(0, str(PROJECT))

from koei_editor.games.dw3.models import Change, SaveError
from koei_editor.games.dw3.save_parser import parse_bytes, read_save
from koei_editor.games.dw3.save_writer import serialize
import koei_editor.games.dw3.collection_editor as collection

FIXTURE = WORKSPACE / 'work' / 'original-upload' / 'GameStatusData.sav'


@unittest.skipUnless(FIXTURE.exists(), 'The supplied workspace save is required.')
class CollectionUnlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_save(FIXTURE)
        cls.digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == cls.digest

    def test_gallery_catalogs_exclude_audio_only_rows_and_movie_placeholders(self):
        state = collection.collection_state(self.document)
        self.assertEqual([row['id'] for row in state['movies']['rows']], list(range(50)))
        self.assertTrue(state['music']['editable'])
        self.assertEqual(state['music']['total'], 42)
        self.assertEqual([row['id'] for row in state['music']['rows']], list(range(42)))
        self.assertEqual([c.index for c in collection.unlock_music_changes(self.document)], list(range(42)))
        self.assertEqual([c.index for c in collection.unlock_movie_changes(self.document)], list(range(50)))

    def test_unlock_changes_only_movie_array_and_preserves_old_acknowledgements(self):
        edit = next(p for p in self.document.properties['OptionData']['value'] if p['name'] == 'Edit')
        props = edit['value']
        current = next(p for p in props if p['name'] == 'bPlayMovie')
        old = next((p for p in props if p['name'] == 'bPlayMovie_Old'), None)
        before = bytes(self.document.plaintext)
        raw, audit = serialize(self.document, [Change('collection', 1, 'Movie', True)])
        result = parse_bytes(raw)
        edited = next(p for p in next(p for p in result.properties['OptionData']['value'] if p['name'] == 'Edit')['value'] if p['name'] == 'bPlayMovie')
        self.assertTrue(edited['value']['values'][1])
        self.assertEqual(edited['value']['values'][:1] + edited['value']['values'][2:], current['value']['values'][:1] + current['value']['values'][2:])
        self.assertEqual(edited['data_size'], current['data_size'])
        self.assertEqual(sum(a != b for a, b in zip(before, result.plaintext)), 1)
        if old is not None:
            self.assertEqual(next(p for p in next(p for p in result.properties['OptionData']['value'] if p['name'] == 'Edit')['value'] if p['name'] == 'bPlayMovie_Old')['value'], old['value'])
        self.assertEqual(audit['plaintext_changes'][0]['reason'], 'Unlock movie gallery')

    def test_movie_action_is_idempotent_and_id_bounds_are_strict(self):
        raw, _ = serialize(self.document, collection.unlock_movie_changes(self.document))
        result = parse_bytes(raw)
        again, audit = serialize(result, collection.unlock_movie_changes(result))
        self.assertEqual(again, raw)
        self.assertEqual(audit['plaintext_changes'], [])
        for invalid in (50, 51, 99, -1, True, False, 1.0):
            with self.subTest(index=invalid), self.assertRaises(SaveError):
                serialize(self.document, [Change('collection', invalid, 'Movie', True)])

    def test_missing_movie_array_is_inserted_with_native_false_defaults(self):
        from koei_editor.games.dw3.save_codec import encrypt
        edit = next(p for p in self.document.properties['OptionData']['value'] if p['name'] == 'Edit')
        movie = next(p for p in edit['value'] if p['name'] == 'bPlayMovie')
        start = movie['tag_offset']
        end = movie['data_offset'] + movie['data_size']
        removed = end - start
        plain = bytearray(self.document.plaintext[:4 + self.document.parsed['payload_size']])
        del plain[start:end]
        option = self.document.properties['OptionData']
        for parent in (edit, option):
            struct.pack_into('<i', plain, parent['size_offset'], parent['data_size'] - removed)
        struct.pack_into('>I', plain, 0, struct.unpack_from('>I', plain, 0)[0] - removed)
        plain.extend(bytes((-len(plain)) % 16))
        sparse = parse_bytes(encrypt(bytes(plain)))
        raw, _ = serialize(sparse, [Change('collection', 1, 'Movie', True)])
        result = parse_bytes(raw)
        edit_after = next(p for p in result.properties['OptionData']['value'] if p['name'] == 'Edit')
        movie_after = next(p for p in edit_after['value'] if p['name'] == 'bPlayMovie')
        self.assertEqual(movie_after['value']['count'], 100)
        self.assertTrue(movie_after['value']['values'][1])
        self.assertEqual(movie_after['value']['values'][:1] + movie_after['value']['values'][2:], [False] * 99)
    def test_malformed_movie_array_is_view_only_and_rejected_for_edits(self):
        edit = next(p for p in self.document.properties['OptionData']['value'] if p['name'] == 'Edit')
        prop = next(p for p in edit['value'] if p['name'] == 'bPlayMovie')
        damaged = bytearray(self.document.plaintext)
        struct.pack_into('<i', damaged, prop['data_offset'], 99)
        from koei_editor.games.dw3.save_codec import encrypt
        invalid = parse_bytes(encrypt(bytes(damaged)))
        state = collection.collection_state(invalid)
        self.assertFalse(state['movies']['editable'])
        with self.assertRaises(SaveError):
            serialize(invalid, [Change('collection', 1, 'Movie', True)])




