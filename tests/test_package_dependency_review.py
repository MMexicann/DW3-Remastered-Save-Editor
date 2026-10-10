"""Independent omission and privacy checks for the nested source package."""
import io
import unittest
import zipfile
from unittest.mock import patch

from tools import package_release as release
from tools import refresh_manifest
from tests import test_universal_packaging as packaging_fixture

BASE = packaging_fixture.BASE


class RegisteredDependencyReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = packaging_fixture.UniversalPackagingTests('test_universal_sources_cannot_omit_game_module_from_manifest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def sources(self, additions):
        self.fixture.add_sources(additions)
        self.fixture.write_manifest()

    def test_keyword_editor_parser_and_relative_package_imports_require_complete_tree(self):
        prefix = BASE + 'games/new/'
        self.sources({
            BASE + 'game_registry.py': b"Game(id='new', editor_module='koei_editor.games.new.editor', parser_module='koei_editor.games.new.parser')\n",
            prefix + '__init__.py': b'from . import codec\n',
            prefix + 'editor.py': b'from . import parser\n',
            prefix + 'parser.py': b'from .codec import decode\n',
            prefix + 'codec.py': b'from ...shared import preferences\n',
        })
        release.verified_sources(self.fixture.root)
        for name in (prefix + '__init__.py', prefix + 'editor.py', prefix + 'parser.py', prefix + 'codec.py', BASE + 'games/__init__.py', BASE + '__init__.py'):
            original = self.fixture.sources.pop(name)
            self.fixture.write_manifest()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Required public sources'):
                release.verified_sources(self.fixture.root)
            self.fixture.sources[name] = original

    def test_local_dependency_outside_runtime_namespace_cannot_disappear(self):
        package = self.fixture.root / 'foreign'
        package.mkdir()
        (package / '__init__.py').write_bytes(b'# Unreviewed package\n')
        (package / 'codec.py').write_bytes(b'# Required codec\n')
        for statement in (b'import foreign.codec\n', b'from foreign import codec\n', b'import foreign\n', b'from ... import escape\n'):
            self.sources({BASE + 'application.py': b"VERSION='1.0'\n" + statement})
            with self.subTest(statement=statement), self.assertRaises(ValueError):
                release.verified_sources(self.fixture.root)

    def test_every_embedded_data_file_requires_a_reviewed_source_entry(self):
        for leaf in release.RUNTIME_DATA:
            name = BASE + 'data/' + leaf
            original = self.fixture.sources.pop(name)
            self.fixture.write_manifest()
            with self.subTest(leaf=leaf), self.assertRaisesRegex(ValueError, 'Required public sources'):
                release.verified_sources(self.fixture.root)
            self.fixture.sources[name] = original

    def test_project_version_is_checked_without_importing_runtime(self):
        (self.fixture.root / 'pyproject.toml').write_bytes(b'[project]\nversion="1.1"\n')
        with self.assertRaisesRegex(ValueError, 'versions do not match'):
            release.version(self.fixture.root)

    def test_unreviewed_json_and_private_python_modules_are_rejected_in_bundle(self):
        archive, blobs, module = self.fixture.archive_fixture()
        archive.toc['koei_editor/data/owner.json'] = (0, 0, 0, 0, 'x')
        with self.assertRaisesRegex(ValueError, 'Unreviewed JSON'):
            release.verify_executable(self.fixture.root, lambda _: archive)
        del archive.toc['koei_editor/data/owner.json']
        pyz = archive.open_embedded_archive('PYZ.pyz')
        pyz.toc['koei_editor.tests.private_fixture'] = (0, 0, 0)
        with self.assertRaisesRegex(ValueError, 'Private or unsafe module'):
            release.verify_executable(self.fixture.root, lambda _: archive)


    def test_library_zip_cannot_hide_player_data_or_traversal_paths(self):
        archive, blobs, module = self.fixture.archive_fixture()
        archive.toc['base_library.zip'] = (0, 0, 0, 0, 'x')
        for name in ('sample.sav', '../private.pyc', 'fixtures/native.pyc', 'AttachedGame.exe', 'owner.json'):
            compressed = io.BytesIO()
            with zipfile.ZipFile(compressed, 'w') as library:
                library.writestr(name, b'opaque private payload')
            blobs['base_library.zip'] = compressed.getvalue()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Private or unsafe|Unreviewed JSON'):
                release.verify_executable(self.fixture.root, lambda _: archive)
        compressed = io.BytesIO()
        with zipfile.ZipFile(compressed, 'w') as library:
            library.writestr('encodings/utf_8.pyc', b'public compiled library')
        blobs['base_library.zip'] = compressed.getvalue()
        release.verify_executable(self.fixture.root, lambda _: archive)

    def test_refresh_never_discovers_private_files_and_rolls_back_failed_candidate(self):
        root = self.fixture.root
        (root / 'private.sav').write_bytes(b'private')
        refresh_manifest.refresh(root)
        self.assertNotIn('private.sav', (root / release.MANIFEST).read_text())
        refreshed = (root / release.MANIFEST).read_bytes()
        with patch.object(refresh_manifest, 'verified_sources', side_effect=ValueError('incomplete candidate')):
            with self.assertRaisesRegex(ValueError, 'incomplete candidate'):
                refresh_manifest.refresh(root)
        self.assertEqual((root / release.MANIFEST).read_bytes(), refreshed)
        self.assertFalse(list((root / 'tools').glob('.SOURCE_MANIFEST.*.tmp')))

    def test_source_symlinks_are_rejected(self):
        root = self.fixture.root
        source = root / 'README.md'
        source.unlink()
        try:
            source.symlink_to(root / 'LICENSE')
        except OSError as exc:
            self.skipTest('Symlink creation unavailable: ' + str(exc))
        with self.assertRaisesRegex(ValueError, 'escapes'):
            release.verified_sources(root)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            refresh_manifest.refresh(root)


    def test_manifest_parent_symlink_is_rejected_before_refresh_or_read(self):
        root = self.fixture.root
        original = root / 'tools'
        relocated = root / 'moved_tools'
        original.rename(relocated)
        try:
            original.symlink_to(relocated, target_is_directory=True)
        except OSError as exc:
            self.skipTest('Symlink creation unavailable: ' + str(exc))
        for operation in (release.verified_sources, refresh_manifest.refresh):
            with self.subTest(operation=operation.__name__), self.assertRaisesRegex(ValueError, 'escapes'):
                operation(root)


if __name__ == '__main__':
    unittest.main()
