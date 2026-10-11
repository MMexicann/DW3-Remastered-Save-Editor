"""Adversarial procedural inputs; these buffers are not player-save evidence."""
from dataclasses import replace
import json
import math
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.fatal_frame2_remake import parser as ff2
from koei_editor.games.ryza import parser as ryza
from koei_editor.games.sophie import parser as sophie
from tests import test_fatal_frame2_remake as ff2_cases
from tests import test_ryza_format as ryza_cases
from tests import test_sophie_format as sophie_cases


class StringSubclass(str):
    pass


class GustInputRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = (
            (sophie, sophie.decode(sophie_cases.fixture())),
            (ryza, ryza.decode(ryza_cases.procedural_raw(), 'atelier_ryza2')),
            (ff2, ff2.decode(ff2_cases.procedural_raw())),
        )

    def test_selected_keys_reject_unhashable_and_nonstring_inputs(self):
        for parser, document in self.documents:
            field = parser.fields_for(document)[0]
            changes = parser.stage(document, {}, field.id, field.minimum)
            before = dict(changes)
            for key in (None, True, 7, [], {}, StringSubclass(field.id)):
                with self.subTest(parser=parser.GAME_ID, key=type(key).__name__):
                    with self.assertRaises(SaveError):
                        parser.stage(document, changes, key, field.minimum)
                    with self.assertRaises(SaveError):
                        parser.field_hint(document, key)
                    self.assertEqual(changes, before)
            self.assertEqual(parser.serialize(document, {}), document.raw)

    def test_batch_selection_is_atomic_for_malformed_key(self):
        for parser, document in self.documents:
            field = parser.fields_for(document)[0]
            changes = parser.stage(document, {}, field.id, field.minimum)
            before = dict(changes)
            for key in ([], {}, True, StringSubclass(field.id)):
                with self.subTest(parser=parser.GAME_ID, key=type(key).__name__):
                    with self.assertRaises(SaveError):
                        parser.limit_values(document, changes, [field.id, key])
                    self.assertEqual(changes, before)

    def test_pending_keys_are_validated_before_unstaging(self):
        for parser, document in self.documents:
            field = parser.fields_for(document)[0]
            for key in (None, True, 7, StringSubclass(field.id)):
                changes = {key: field.minimum}
                before = dict(changes)
                with self.subTest(parser=parser.GAME_ID, key=type(key).__name__):
                    with self.assertRaises(SaveError):
                        parser.stage(document, changes, field.id, field.value(document.payload))
                    with self.assertRaises(SaveError):
                        parser.serialize(document, changes)
                    self.assertEqual(changes, before)

    def test_ryza_requires_canonical_format_identity(self):
        document = self.documents[1][1]

        class EqualFormat(ryza.Format):
            def __eq__(self, other):
                return True

        formats = (replace(document.format), EqualFormat(**vars(document.format)),
                   replace(document.format, id=[]))
        for layout in formats:
            altered = replace(document, format=layout)
            for operation in (
                lambda: ryza.fields_for(altered),
                lambda: ryza.stage(altered, {}, 'container_0_quality', 1),
                lambda: ryza.serialize(altered, {}),
                lambda: ryza.maximums(altered, {}),
            ):
                with self.subTest(layout=type(layout).__name__), self.assertRaises(SaveError):
                    operation()
        self.assertEqual(ryza.serialize(document, {}), document.raw)

    def test_overflow_json_floats_rejected_before_exposing_fields(self):
        for token in (b'1e999', b'-1e999', b'1.0e999'):
            encoded = b'{"unknown":' + token + b'}'
            with self.subTest(token=token), self.assertRaises(SaveError):
                ff2._json(bytes(16) + encoded + b'\0')

    def test_finite_unknown_json_lexemes_survive_surgical_edit(self):
        encoded = json.dumps(ff2_cases.system_json(), separators=(',', ':')).encode()
        unknown = b',"UnmappedFloatLexemes":[1.2300e+03,-0.0,1e308,1e-300]}'
        encoded = encoded[:-1] + unknown
        raw = ff2_cases.make_raw(ff2_cases.system_json(), json_bytes=encoded)
        document = ff2.decode(raw)
        root, original_json = ff2._json(document.payload)
        self.assertTrue(all(math.isfinite(value) for value in root['UnmappedFloatLexemes']))
        self.assertTrue(original_json.endswith(unknown))
        field, = ff2.fields_for(document)
        changes = ff2.stage(document, {}, field.id, 7)
        modified = ff2.changed_payload(document, changes)
        expected = (document.payload[:field.offset] + b'7'.rjust(field.size, b' ')
                    + document.payload[field.offset + field.size:])
        self.assertEqual(modified, expected)
        reopened = ff2.decode(ff2.serialize(document, changes))
        self.assertEqual(reopened.payload, expected)
        self.assertTrue(ff2._json(reopened.payload)[1].endswith(unknown))

    def test_overflow_float_in_valid_native_envelope_is_rejected(self):
        encoded = json.dumps(ff2_cases.system_json(), separators=(',', ':')).encode()
        encoded = encoded[:-1] + b',"UnmappedFloat":1e999}'
        raw = ff2_cases.make_raw(ff2_cases.system_json(), json_bytes=encoded)
        with self.assertRaises(SaveError):
            ff2.decode(raw)
