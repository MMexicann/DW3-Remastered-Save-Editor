"""Single executable build configuration and bundle privacy contracts."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from tests import test_package_release as legacy
import package_release as release


class UniversalPackagingTests(legacy.PackagingTests):
    # Keep all original integrity checks and add a universal application fixture.
    def setUp(self):
        super().setUp()
        extra = {'application.py': b"VERSION = '1.0'\n", 'appearance.py': b'# Shared appearance\n',
                 'game_registry.py': b'# Registered games\n', 'origins_gui.py': b'# Origins workspace\n',
                 'origins_editor.py': b'# Copy tools\n', 'origins_evidence.json': b'{"editable_fields": []}',
                 'save_safety.py': b'# Copy-only policy\n', 'copy_storage.py': b'# Atomic copies\n',
                 'ORIGINS_FORMAT.md': b'# Verified evidence\n', 'launch.pyw': b'# Launcher\n'}
        self.sources.update(extra)
        for name, data in extra.items():
            (self.root / name).write_bytes(data)
        self.write_manifest()
        (self.root / 'dist/UniversalKoeiTecmoSaveEditor-v1.0.exe').write_bytes(b'MZ synthetic editor executable')

    def test_archives_contain_only_verified_sources_and_user_downloads(self):
        with patch.object(release, 'verify_executable', return_value=1) as verified:
            assets = release.package(self.root)
        verified.assert_called_once_with(self.root)
        with zipfile.ZipFile(assets[0]) as archive:
            self.assertIn('UniversalKoeiTecmoSaveEditor-v1.0.exe', archive.namelist())
            self.assertFalse(any(name.endswith('.dat') for name in archive.namelist()))
        with zipfile.ZipFile(assets[1]) as archive:
            prefix = 'UniversalKoeiTecmoSaveEditor-v1.0-Source/'
            self.assertEqual(set(archive.namelist()), {prefix + name for name in self.sources} |
                             {prefix + 'SOURCE_MANIFEST.json'})
        self.assertEqual(assets[2].read_bytes(), b'MZ synthetic editor executable')

    def test_embedded_metadata_and_compressed_modules_are_verified(self):
        blobs = {'origins_evidence.json': self.sources['origins_evidence.json'], 'PYZ.pyz': b'archive'}
        pyz = SimpleNamespace(toc={'application': (0, 0, 0)}, extract=lambda name, raw=False: b'public code')
        archive = SimpleNamespace(toc={'origins_evidence.json': (0, 0, 0, 0, 'x'),
                                       'PYZ.pyz': (0, 0, 0, 0, 'z')},
                                  extract=lambda name: blobs[name], open_embedded_archive=lambda name: pyz)
        self.assertEqual(release.verify_executable(self.root, lambda _: archive), 2)
        for suffix in ('.dat', '.bin', '.sav', '.key', '.psu', '.ps2', '.psv', '.max', '.cbs', '.vmc', '.sys'):
            archive.toc['sample' + suffix] = (0, 0, 0, 0, 'x')
            with self.assertRaisesRegex(ValueError, 'Private or unsafe'):
                release.verify_executable(self.root, lambda _: archive)
            del archive.toc['sample' + suffix]

    def test_universal_sources_cannot_omit_game_module_from_manifest(self):
        del self.sources['origins_editor.py']
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'Required public sources'):
            release.verified_sources(self.root)

    def test_standalone_adapted_codec_cannot_omit_or_change_its_license(self):
        extra = {'atelier_sophie2_codec.py': b'# MIT adapted codec\n',
                 'atelier_sophie2_parser.py': b'# Parser\n',
                 'atelier_sophie2_editor.py': b'# Adapter\n',
                 'ATELIER_SOPHIE2_FORMAT.md': b'# Layout\n',
                 'licenses/atelier-sophie2-save-editor-MIT.txt': b'MIT adapted-code notice\n'}
        self.sources.update(extra)
        for name, data in extra.items():
            (self.root / name).write_bytes(data)
        self.write_manifest()
        names = ('origins_evidence.json', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
                 'licenses/atelier-sophie2-save-editor-MIT.txt')
        blobs = {name: self.sources[name] for name in names}
        archive = SimpleNamespace(toc={name: (0, 0, 0, 0, 'x') for name in names},
                                  extract=lambda name: blobs[name])
        self.assertEqual(release.verify_executable(self.root, lambda _: archive), 4)
        license_name = names[-1]
        del archive.toc[license_name]
        with self.assertRaisesRegex(ValueError, 'missing from executable'):
            release.verify_executable(self.root, lambda _: archive)
        archive.toc[license_name] = (0, 0, 0, 0, 'x')
        blobs[license_name] = b'Incorrect notice'
        with self.assertRaisesRegex(ValueError, 'differs from manifest'):
            release.verify_executable(self.root, lambda _: archive)

    def test_failed_bundle_validation_prevents_creating_any_downloads(self):
        with patch.object(release, 'verify_executable', side_effect=ValueError('Private artifact')):
            with self.assertRaisesRegex(ValueError, 'Private artifact'):
                release.package(self.root)
        self.assertFalse((self.root / 'release').exists())

    def test_research_documents_stay_in_source_download_only(self):
        extra = {'game_knowledge.py':b'# Authored guide\n', 'GAME_MECHANICS.md':b'# Evidence\n',
                 'KOEI_FORMATS.md':b'# PC layouts\n', 'PC_EDITOR_ATTEMPTS.md':b'# Qualification results\n',
                 'PC_RESEARCH_RETRY.md':b'# Renewed candidate evidence\n'}
        self.sources.update(extra)
        for name,data in extra.items():
            (self.root/name).write_bytes(data)
        self.write_manifest()
        with patch.object(release,'verify_executable',return_value=1):
            assets=release.package(self.root)
        with zipfile.ZipFile(assets[0]) as archive:
            self.assertFalse({'GAME_MECHANICS.md','KOEI_FORMATS.md','ORIGINS_FORMAT.md',
                              'PC_EDITOR_ATTEMPTS.md', 'PC_RESEARCH_RETRY.md'} & set(archive.namelist()))
        with zipfile.ZipFile(assets[1]) as archive:
            self.assertIn('UniversalKoeiTecmoSaveEditor-v1.0-Source/GAME_MECHANICS.md', archive.namelist())


class WindowsBuildConfigurationTests(unittest.TestCase):
    def test_build_uses_one_universal_entry_and_explicit_game_modules(self):
        import build_windows
        args = build_windows.build_args()
        self.assertIn('--onefile', args)
        self.assertIn('--windowed', args)
        self.assertEqual(args[args.index('--name') + 1], 'UniversalKoeiTecmoSaveEditor-v1.3')
        self.assertEqual(Path(args[-1]).name, 'application.py')
        for module in ('gui', 'save_parser', 'origins_gui', 'origins_editor', 'dw8xl_editor', 'pw3_editor',
                       'dw4hyper_editor', 'dw4hyper_parser', 'dw4xl_editor', 'dw4xl_parser'):
            self.assertIn(module, args)
        for module in ('atelier_sophie2_editor', 'atelier_sophie2_parser'):
            self.assertIn(module, args)
        self.assertTrue(any('origins_evidence.json' in argument for argument in args))
        self.assertTrue(any('support_catalog.json' in argument for argument in args))

    def test_application_and_build_have_matching_versions(self):
        self.assertEqual(release.version(PROJECT), '1.3')
        self.assertEqual(release.artifact_name(PROJECT), 'UniversalKoeiTecmoSaveEditor-v1.3')

    def test_publication_requires_a_tag_and_successful_native_build(self):
        workflow = (PROJECT / '.github/workflows/windows-release.yml').read_text()
        self.assertIn("if: github.event_name == 'push' && github.ref_type == 'tag'", workflow)
        self.assertIn('needs: build', workflow)
        self.assertIn('Release tag must match the application version.', workflow)
        self.assertIn('python package_release.py --verify-executable', workflow)
        self.assertIn('sha256sum --check SHA256SUMS.txt', workflow)
        self.assertIn('gh release create', workflow)
        self.assertIn('--verify-tag', workflow)
        self.assertNotIn('gh release edit', workflow)
        self.assertNotIn('gh release upload', workflow)
        self.assertNotIn('git push', workflow)


if __name__ == '__main__':
    unittest.main()
