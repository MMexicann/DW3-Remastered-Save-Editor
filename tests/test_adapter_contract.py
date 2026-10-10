"""Shared contracts exercise real backends and explicit dispatch/session safety."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from koei_editor.shared.adapter_contract import BoundScalarAdapter, SESSION_ACTIONS, validate_session
from koei_editor.game_registry import get_game
from koei_editor.games.dw3.models import SaveError
from tests.scalar_contract import ScalarContractTests
from tests.test_verified_editors import synthetic_raw
from tests.test_dw4hyper_format import procedural_raw as hyper_raw
from tests.test_dw4xl_format import procedural_psu
from tests.test_atelier_sophie2_format import procedural_raw as sophie_raw


class DW8ContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'dw8xl'
    fixture_bytes = staticmethod(lambda: synthetic_raw('dw8xl'))


class PW3ContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'pw3'
    fixture_bytes = staticmethod(lambda: synthetic_raw('pw3'))


class HyperContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'dw4hyper'
    fixture_bytes = staticmethod(hyper_raw)


class PS2ContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'dw4xl_ps2'
    fixture_bytes = staticmethod(procedural_psu)
    payload_integrity_offsets = frozenset((0, 1))


class SophieContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'atelier_sophie2'
    fixture_bytes = staticmethod(sophie_raw)


class AdapterDispatchTests(unittest.TestCase):
    def test_wrong_extension_and_game_never_invoke_backend_read(self):
        adapter = get_game('dw8xl').get_scalar_adapter()
        with patch.object(adapter.backend, 'read_save') as read:
            for path, identity in (('copy.psu', None), ('copy.dat', 'pw3')):
                with self.assertRaises(SaveError):
                    adapter.read_save(path, identity)
            read.assert_not_called()

    def test_snapshot_profile_identity_rejects_equal_and_permissive_metadata(self):
        adapter = get_game('dw8xl').get_scalar_adapter()
        document = adapter.decode(synthetic_raw('dw8xl'))
        class PermissiveProfile:
            id = 'dw8xl'
            def __eq__(self, _other): return True
        for layout in (replace(document.format), PermissiveProfile()):
            with self.subTest(profile=type(layout).__name__), \
                    patch.object(adapter.backend, 'fields_for') as fields:
                with self.assertRaises(SaveError):
                    adapter.fields_for(replace(document, format=layout))
                fields.assert_not_called()

    def test_bulk_staging_keeps_snapshot_and_does_not_repeat_native_cipher(self):
        adapter = get_game('dw8xl').get_scalar_adapter()
        document = adapter.decode(synthetic_raw('dw8xl'))
        changes = {}
        with patch.object(adapter.backend, 'decode', wraps=adapter.backend.decode) as decode:
            for field in adapter.fields_for(document):
                changes = adapter.stage(document, changes, field.id, field.maximum)
        self.assertGreater(len(changes), 100)
        self.assertEqual(document.raw, synthetic_raw('dw8xl'))
        # A full decode per field makes Max Visible block the UI for seconds.
        self.assertLessEqual(decode.call_count, 1)

    def test_incomplete_or_mismatched_backend_rejected_before_read(self):
        with self.assertRaisesRegex(SaveError, 'incomplete scalar backend'):
            BoundScalarAdapter('dw8xl', '.dat', SimpleNamespace())
        adapter = get_game('dw8xl').get_scalar_adapter()
        with patch.object(adapter.backend, 'get_format', return_value=SimpleNamespace(id='pw3')):
            with self.assertRaisesRegex(SaveError, 'different game/platform format'):
                BoundScalarAdapter('dw8xl', '.dat', adapter.backend)

    def test_new_scalar_registration_dispatches_self_test_without_game_branch(self):
        import koei_editor.game_registry as game_registry
        import koei_editor.shared.verified_self_test as verified_self_test
        import koei_editor.games.dw4hyper.dw4hyper_parser as dw4hyper_parser
        new = replace(get_game('dw4hyper'), id='contributor_example')
        layout = replace(dw4hyper_parser.FORMAT, id=new.id)
        with patch.object(game_registry, 'ALL_ADAPTERS', game_registry.ALL_ADAPTERS + (new,)), \
                patch.object(dw4hyper_parser, 'get_format', return_value=layout), \
                patch.object(verified_self_test, '_run', return_value={'success': True}) as run:
            self.assertEqual(verified_self_test.run(new.id, 'copy.dat', 'output'), {'success': True})
        bound, identity, source, output = run.call_args.args
        self.assertEqual(bound.game_id, new.id)
        self.assertIs(bound.backend, dw4hyper_parser)
        self.assertEqual((identity, source, output), (new.id, 'copy.dat', 'output'))

    def test_registered_editor_mismatch_rejected_before_constructor(self):
        game = get_game('pw3')
        constructor = Mock(game_id='dw8xl')
        with patch('koei_editor.game_registry.import_module', return_value=SimpleNamespace(Editor=constructor)):
            with self.assertRaises(SaveError):
                game.create_editor(None, None)
        constructor.assert_not_called()

    def test_editor_backend_or_extension_mismatch_rejected_before_constructor(self):
        game = get_game('pw3')
        backend = game.get_scalar_adapter().backend
        for declared_backend, extension in ((object(), '.dat'), (backend, '.psu')):
            constructor = Mock(game_id=game.id, backend=declared_backend, save_extension=extension)
            editor_module = SimpleNamespace(Editor=constructor)
            with patch('koei_editor.game_registry.import_module', side_effect=lambda name: editor_module if name == game.editor_module else backend):
                with self.assertRaises(SaveError):
                    game.create_editor(None, None)
            constructor.assert_not_called()

    def test_cli_uses_declared_scalar_capability_for_new_registration(self):
        import koei_editor.application as application
        import koei_editor.game_registry as game_registry
        new = replace(get_game('dw4hyper'), id='contributor_cli')
        report = {'format_sample_verified': False, 'fields_checked': 3}
        arguments = ['application.py', '--game', new.id, '--self-test', 'copy.dat', 'output']
        with patch.object(game_registry, 'ALL_ADAPTERS', game_registry.ALL_ADAPTERS + (new,)), \
                patch.object(application, 'ALL_ADAPTERS', application.ALL_ADAPTERS + (new,)), \
                patch.object(sys, 'argv', arguments), patch('koei_editor.shared.verified_self_test.run', return_value=report) as run, \
                patch.object(application.tk, 'Tk') as tk_root, patch('builtins.print'):
            application.main()
        run.assert_called_once_with(new.id, 'copy.dat', 'output')
        tk_root.assert_not_called()

    def test_session_validation_and_active_only_dispatch_hidden_close_cancel(self):
        from koei_editor.application import Application
        def session(game_id):
            values = {name: Mock(return_value=True) for name in SESSION_ACTIONS}
            return SimpleNamespace(game_id=game_id, document=None, changes={}, theme_name=Mock(), **values)
        first, second = session('first'), session('second')
        validate_session(first, 'first')
        with self.assertRaises(SaveError):
            validate_session(first, 'second')
        invalid = session('invalid')
        invalid.undo = None
        with self.assertRaises(SaveError):
            validate_session(invalid, 'invalid')
        app = Application.__new__(Application)
        app.sessions = {'first': (None, first), 'second': (None, second)}
        app.active_game = 'second'
        app.root = Mock()
        self.assertEqual(app.dispatch('undo'), 'break')
        first.undo.assert_not_called()
        second.undo.assert_called_once()
        app.active_game = None
        app.dispatch('undo')
        self.assertEqual(second.undo.call_count, 1)
        first.changes['pending'] = 123
        first.dirty_ok.return_value = False
        app.close()
        app.root.destroy.assert_not_called()
        self.assertEqual(first.changes, {'pending': 123})
