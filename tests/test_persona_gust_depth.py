"""New resource controls: procedural preservation and optional native evidence."""
from functools import lru_cache
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.p5strikers_pc import codec as p5codec, parser as p5
from koei_editor.games.p5strikers_pc.catalog import INCENSES, REMEDIES, SKILL_CARDS
from koei_editor.games.ryza import parser as ryza
from tests.test_p5strikers_pc import procedural_payload
from tests.test_ryza_format import node, procedural_payload as ryza_payload, procedural_raw


@lru_cache(maxsize=1)
def persona_document():
    payload = bytearray(procedural_payload())
    for index, (relative, _name) in enumerate(INCENSES + REMEDIES + SKILL_CARDS):
        payload[p5._base(1) + relative:p5._base(1) + relative + 2] = bytes((index % 9 + 1, 0))
    return p5.decode(p5codec.encode(p5codec.with_checksum(bytes(payload)), 0x123456))


def skill_document(value=500, version=bytes.fromhex('000000020004'), width=4, duplicate=False, unframed=False):
    payload = ryza_payload()
    roots = ryza._nodes(payload, 32, len(payload))
    tree = next(n for n in roots if n.name == b'AlchemyTree')
    point = node('SkillPoint', struct.pack('>II', width, value))
    body = (node('ver', version) + point + (point if duplicate else b'')
            + node('SkillState', bytes(range(32))))
    if unframed:
        body = b'\xA5\xC3'  # Unknown opaque tree data must not block mapped item edits.
    replacement = node('AlchemyTree', body)
    return ryza.decode(procedural_raw(payload[:tree.start] + replacement + payload[tree.end:]), 'atelier_ryza2')


class PersonaStackDepthTests(unittest.TestCase):
    def test_new_categories_stay_existing_stacks_and_preserve_growth(self):
        document = persona_document()
        fields = [f for f in p5.fields_for(document)
                  if f.group in ('Incenses', 'Ailment remedies', 'Skill cards')]
        self.assertEqual(len(fields), 40)
        changes = {f.id: 11 for f in fields}
        edited = p5.decode(p5.serialize(document, changes))
        allowed = {f.offset for f in fields} | {len(document.payload) - 4}
        touched = {i for i, pair in enumerate(zip(document.payload, edited.payload)) if pair[0] != pair[1]}
        self.assertTrue(touched <= allowed)
        self.assertEqual(p5.progression_records(edited), p5.progression_records(document))
        self.assertEqual(edited.seed, document.seed)
        self.assertEqual(p5.maximums(document, changes), changes)
        self.assertEqual(len(p5.review(document, changes)), len(fields))
        for f in fields:
            self.assertEqual(p5.stage(document, changes, f.id, f.value(document.payload)),
                             {k: v for k, v in changes.items() if k != f.id})
            self.assertFalse(f.maxable)

    def test_empty_unusual_and_adjacent_flag_records_remain_inspection(self):
        document = persona_document()
        payload = bytearray(document.payload)
        offsets = [relative for relative, _ in (INCENSES[0], REMEDIES[0], SKILL_CARDS[0])]
        for relative, pair in zip(offsets, (b'\0\0', b'\x64\0', b'\x03\x80')):
            offset = p5._base(1) + relative
            payload[offset:offset + 2] = pair
        opened = p5.decode(p5codec.encode(p5codec.with_checksum(bytes(payload)), document.seed))
        self.assertEqual(p5.serialize(opened, {}), opened.raw)
        for relative in offsets:
            key = f'slot_1_item_{relative:x}'
            self.assertNotIn(key, p5.field_map(opened))
            with self.assertRaises(SaveError):
                p5.stage(opened, {}, key, 5)

    def test_card_and_incense_guidance_keeps_item_application_separate(self):
        document = persona_document()
        for relative, _ in INCENSES:
            self.assertIn('game applies the item', p5.field_hint(document, f'slot_1_item_{relative:x}'))
        for relative, _ in SKILL_CARDS:
            key = f'slot_1_item_{relative:x}'
            self.assertIn('learned skill sets remain under game control', p5.field_hint(document, key))
            for value in (0, 100, True):
                with self.assertRaises(SaveError):
                    p5.stage(document, {}, key, value)


class RyzaSkillResourceTests(unittest.TestCase):
    def test_reductions_preserve_skill_ownership_and_envelope(self):
        document = skill_document()
        f = ryza.field_map(document)['skill_points']
        changes = ryza.stage(document, {}, f.id, 123)
        edited = ryza.decode(ryza.serialize(document, changes), 'atelier_ryza2')
        self.assertEqual(edited.payload[f.offset:f.offset + 4], b'\0\0\0{')
        touched = {i for i, pair in enumerate(zip(document.payload, edited.payload)) if pair[0] != pair[1]}
        self.assertTrue(touched <= set(range(f.offset, f.offset + 4)))
        self.assertEqual((edited.seed, edited.header, edited.trailer, edited.footer),
                         (document.seed, document.header, document.trailer, document.footer))
        self.assertEqual(ryza.stage(document, changes, f.id, 500), {})
        self.assertEqual(ryza.maximums(document, changes), changes)
        self.assertEqual(ryza.limit_values(document, changes, (f.id,)), {})
        for value in (-1, 501, True):
            with self.assertRaises(SaveError):
                ryza.stage(document, {}, f.id, value)

    def test_unknown_scalar_profiles_preserve_existing_quality_controls(self):
        for options in ({'version': b'\0\0\0\3\0\4'}, {'width': 2}, {'duplicate': True},
                        {'value': 0xffffffff}, {'unframed': True}):
            document = skill_document(**options)
            self.assertNotIn('skill_points', ryza.field_map(document))
            self.assertEqual(len(ryza.fields_for(document)), 3)
            self.assertEqual(ryza.serialize(document, {}), document.raw)

    def test_higher_opened_balance_is_preserved_and_zero_is_valid(self):
        document = skill_document(2_000_000_000)
        changes = ryza.stage(document, {}, 'skill_points', 0)
        self.assertEqual(ryza.stage(document, changes, 'skill_points', 2_000_000_000), {})
        self.assertEqual(ryza.serialize(document, {}), document.raw)
        zero = skill_document(0)
        self.assertEqual(ryza.field_map(zero)['skill_points'].maximum, 0)
        self.assertEqual(ryza.stage(zero, {}, 'skill_points', 0), {})


class NativeResourceDepthTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('P5S_PC_SAVE_COPIES'), 'No private native PC copies selected')
    def test_native_incense_and_card_stacks_surgical_multi_slot_edit(self):
        for filename in os.environ['P5S_PC_SAVE_COPIES'].split(os.pathsep):
            document = p5.read_save(Path(filename))
            fields = [f for f in p5.fields_for(document) if f.group in ('Incenses', 'Skill cards')]
            self.assertEqual({f.group for f in fields}, {'Incenses', 'Skill cards'})
            changes = {f.id: 2 if f.value(document.payload) == 1 else 1 for f in fields}
            edited = p5.decode(p5.serialize(document, changes))
            allowed = {f.offset for f in fields} | {len(document.payload) - 4}
            self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(document.payload, edited.payload))))
            self.assertEqual(p5.progression_records(document), p5.progression_records(edited))
            self.assertEqual(p5.serialize(document, {}), document.raw)

    @unittest.skipUnless(os.environ.get('RYZA2_SAVE_COPY'), 'No private native Ryza 2 copy selected')
    def test_native_sp_field_and_surgical_reduction(self):
        document = ryza.read_save(Path(os.environ['RYZA2_SAVE_COPY']), 'atelier_ryza2')
        f = ryza.field_map(document)['skill_points']
        self.assertGreater(f.value(document.payload), 0)
        edited = ryza.decode(ryza.serialize(document, {f.id: 0}), 'atelier_ryza2')
        self.assertTrue(all(a == b or i in range(f.offset, f.offset + 4)
                            for i, (a, b) in enumerate(zip(document.payload, edited.payload))))
        self.assertEqual(f.value(edited.payload), 0)
        self.assertEqual(ryza.serialize(document, {}), document.raw)


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A Tk display is required')
class ResourceDepthGuiTests(unittest.TestCase):
    def test_new_p5_categories_and_ryza_sp_undo_review_save_restore(self):
        import tkinter as tk
        from koei_editor.games.p5strikers_pc.editor import Editor as PersonaEditor
        from koei_editor.games.ryza.editor import Ryza2Editor
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        examples = ((PersonaEditor, persona_document(), p5,
                     ('slot_1_item_869c6', 'slot_1_item_871ca')),
                    (Ryza2Editor, skill_document(), ryza, ('skill_points',)))
        for editor_type, original, backend, keys in examples:
            with self.subTest(game=original.format.id), tempfile.TemporaryDirectory() as folder:
                suffix = '.bin' if backend is p5 else '.dat'
                source = Path(folder) / ('source' + suffix)
                source.write_bytes(original.raw)
                editor = editor_type(root)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)), \
                        patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.open()
                    errors.assert_not_called()
                    for key in keys:
                        field = backend.field_map(editor.document)[key]
                        value = field.minimum if field.value(editor.document.payload) != field.minimum else field.minimum + 1
                        editor.group.set(field.group)
                        editor.search.set(field.label)
                        editor.refresh()
                        self.assertIn(key, editor.fields.get_children())
                        editor.fields.selection_set(key)
                        editor.value.set(str(value))
                        editor.apply_selected()
                        self.assertEqual(editor.changes[key], value)
                        before = dict(editor.changes)
                        editor.max_visible()
                        self.assertEqual(editor.changes, before)
                        editor.undo()
                        self.assertNotIn(key, editor.changes)
                        editor.fields.selection_set(key)
                        editor.value.set(str(value))
                        editor.apply_selected()
                    editor.review()
                    self.assertEqual(len(backend.review(editor.document, editor.changes)), len(keys))
                    staged = dict(editor.changes)
                    target = Path(folder) / ('edited' + suffix)
                    editor.save_to(target)
                    errors.assert_not_called()
                    reopened = backend.read_save(target, original.format.id)
                    for key, value in staged.items():
                        self.assertEqual(backend.field_map(reopened)[key].value(reopened.payload), value)
                    restored = backend.restore(editor.backup, Path(folder) / ('restored' + suffix), original.format.id)
                    self.assertEqual(restored.read_bytes(), original.raw)
                    self.assertEqual(source.read_bytes(), original.raw)
