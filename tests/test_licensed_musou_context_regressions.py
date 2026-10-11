"""Procedural regressions for mandatory PS3 title/slot companion safety.

No player save or account metadata is included. Swaps occur before the final
write qualification, covering both initially valid and later changed metadata.
"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from koei_editor.games.dw3.models import SaveError
from koei_editor.games.gundam1_ps3 import parser as gundam
from koei_editor.games.kens_rage1_ps3 import parser as rage1
from koei_editor.games.kens_rage2_ps3 import parser as rage2
from tests.test_gundam1_ps3 import fixture as gf, metadata as gm
from tests.test_kens_rage1_ps3 import procedural_save as rf1, metadata as rm1
from tests.test_kens_rage2_ps3 import procedural_save as rf2, metadata as rm2

class LicensedMusouContextRegressionTests(unittest.TestCase):
    def restore_with_switched_context(self, backend, fixture, metadata, foreign):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);source=base/'DATA.BIN'
            source.write_bytes(fixture());companion=base/'PARAM.SFO'
            companion.write_bytes(metadata())
            doc=backend.read_save(source);backup=backend.backup(doc)
            destination=base/'restored.bin';actual=backend.restore_snapshot
            def switched(*args, **kwargs):
                companion.write_bytes(metadata(foreign))
                return actual(*args, **kwargs)
            with patch.object(backend, 'restore_snapshot', switched):
                with self.assertRaises(SaveError):
                    backend.restore(backup,destination)
            self.assertFalse(destination.exists())
    def test_rage1_rechecks_mandatory_title_before_restore_write(self):
        self.restore_with_switched_context(rage1,rf1,rm1,'BLUS30058-00')
    def test_rage2_rechecks_mandatory_title_before_restore_write(self):
        self.restore_with_switched_context(rage2,rf2,rm2,'BLUS30058-00')
    def test_gundam_foreign_title_changed_after_first_check_rejected(self):
        self.restore_with_switched_context(gundam,gf,gm,'BLES01801-00')
    def test_gundam_same_title_different_slot_after_first_check_rejected(self):
        self.restore_with_switched_context(gundam,gf,gm,'BLUS30058-02')
    def test_gundam_valid_same_title_different_slot_before_restore_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);source=base/'DATA.BIN';source.write_bytes(gf())
            companion=base/'PARAM.SFO';companion.write_bytes(gm())
            doc=gundam.read_save(source);backup=gundam.backup(doc)
            companion.write_bytes(gm('BLUS30058-02'));destination=base/'restored.bin'
            with self.assertRaises(SaveError):gundam.restore(backup,destination)
            self.assertFalse(destination.exists())

    def save_with_switched_context(self, backend, fixture, metadata, foreign):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);source=base/'DATA.BIN';source.write_bytes(fixture())
            companion=base/'PARAM.SFO';companion.write_bytes(metadata())
            doc=backend.read_save(source);destination=base/'edited.bin';actual=backend.backup
            def switched(document):
                backup=actual(document)
                companion.write_bytes(metadata(foreign))
                return backup
            with patch.object(backend,'backup',switched):
                with self.assertRaises(SaveError):backend.save_as(doc,{},destination)
            self.assertFalse(destination.exists())
            self.assertEqual(source.read_bytes(),doc.raw)
    def test_rage1_rechecks_context_after_backup_before_save_write(self):
        self.save_with_switched_context(rage1,rf1,rm1,'BLUS30288-00')
    def test_rage2_rechecks_context_after_backup_before_save_write(self):
        self.save_with_switched_context(rage2,rf2,rm2,'BLUS30288-00')
    def test_gundam_rechecks_context_before_write_not_after_destination_created(self):
        self.save_with_switched_context(gundam,gf,gm,'BLUS30288-00')
    def test_gundam_same_title_different_slot_after_backup_rejected_before_write(self):
        self.save_with_switched_context(gundam,gf,gm,'BLUS30058-02')

    def test_supported_but_different_destination_title_or_slot_rejected(self):
        for backend,fixture,metadata,other in (
                (gundam,gf,gm,'BLES00147-00'),
                (rage1,rf1,rm1,'BLES01062-00'),
                (rage2,rf2,rm2,'BLES01801-01')):
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as folder:
                base=Path(folder);source=base/'DATA.BIN';raw=fixture();source.write_bytes(raw)
                (base/'PARAM.SFO').write_bytes(metadata());doc=backend.read_save(source)
                elsewhere=base/'other';elsewhere.mkdir()
                (elsewhere/'PARAM.SFO').write_bytes(metadata(other));destination=elsewhere/'edited.bin'
                with self.assertRaises(SaveError):backend.save_as(doc,{},destination)
                self.assertFalse(destination.exists());self.assertEqual(source.read_bytes(),raw)

    def test_opened_source_identity_is_frozen_before_backup_or_self_test_copy(self):
        for backend,fixture,metadata,other in (
                (gundam,gf,gm,'BLUS30058-02'),
                (rage1,rf1,rm1,'BLES01062-00'),
                (rage2,rf2,rm2,'BLES01801-01')):
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as folder:
                base=Path(folder);source=base/'DATA.BIN';raw=fixture();source.write_bytes(raw)
                companion=base/'PARAM.SFO';companion.write_bytes(metadata())
                doc=backend.read_save(source);companion.write_bytes(metadata(other))
                with self.assertRaises(SaveError):backend.backup(doc)
                destination=base/'self-test'/'copy.bin'
                with self.assertRaises(SaveError):backend.prepare_self_test_copy(doc,destination)
                self.assertFalse(destination.parent.exists());self.assertEqual(source.read_bytes(),raw)

    def test_destination_swapped_independently_after_backup_rejected_before_write(self):
        for backend,fixture,metadata in ((gundam,gf,gm),(rage1,rf1,rm1),(rage2,rf2,rm2)):
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as folder:
                base=Path(folder);source=base/'DATA.BIN';source.write_bytes(fixture())
                (base/'PARAM.SFO').write_bytes(metadata());doc=backend.read_save(source)
                elsewhere=base/'output';elsewhere.mkdir();companion=elsewhere/'PARAM.SFO'
                companion.write_bytes(metadata());destination=elsewhere/'edited.bin';actual=backend.backup
                def switched(document):
                    backup=actual(document);companion.write_bytes(metadata('BLUS30288-00'));return backup
                with patch.object(backend,'backup',switched):
                    with self.assertRaises(SaveError):backend.save_as(doc,{},destination)
                self.assertFalse(destination.exists());self.assertEqual(source.read_bytes(),doc.raw)

    def test_invalid_selected_keys_raise_saveerror_without_changing_pending_edits(self):
        for backend,fixture in ((gundam,gf),(rage1,rf1),(rage2,rf2)):
            doc=backend.decode(fixture());pending={}
            for key in ([], {}, None, 1):
                with self.subTest(game=backend.GAME_ID,key=type(key).__name__):
                    with self.assertRaises(SaveError):backend.stage(doc,pending,key,1)
                    with self.assertRaises(SaveError):backend.limit_values(doc,pending,[key])
                    self.assertEqual(pending,{})

if __name__=='__main__':unittest.main()
