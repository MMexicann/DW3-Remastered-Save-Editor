"""Release archive integrity and publication boundaries; synthetic files only."""
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import patch
import zipfile

from tools import package_release as release

PROJECT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.area = (PROJECT / 'work/package-tests').resolve()
        self.area.mkdir(parents=True, exist_ok=True)
        self.root = self.area / uuid.uuid4().hex
        self.root.mkdir()
        self.sources = {name: b'Public document\n' for name in release.WINDOWS_DOCS}
        self.sources.update({name: b'# Public build helper\n' for name in release.TOOL_FILES})
        self.sources.update({f'src/koei_editor/data/{name}': b'{}' for name in release.RUNTIME_DATA})
        self.sources.update({
            'src/koei_editor/__init__.py': b'# Runtime package\n',
            'src/koei_editor/application.py': b"VERSION = '1.0'\n",
            'src/koei_editor/game_registry.py': b'# Registered game modules\n',
            'src/koei_editor/__main__.py': b'from .application import main\n',
            'tools/build_windows.py': b"VERSION = '1.0'\n",
            'pyproject.toml': b'[project]\nname = "synthetic-public-editor"\nversion = "1.0"\n',
            'launch.pyw': b'from koei_editor.application import main\nmain()\n',
            'docs/RELEASE_NOTES.md': b'# v1.0\n',
            '.github/workflows/windows-release.yml': b'name: Windows release\n',
            'licenses/Python-LICENSE.txt': b'License text\n',
            'tests/test_public.py': b'# Synthetic public test\n',
        })
        self.add_sources(self.sources)
        (self.root / 'dist').mkdir()
        (self.root / 'dist/UniversalKoeiTecmoSaveEditor-v1.0.exe').write_bytes(b'MZ synthetic editor executable')
        self.write_manifest()

    def tearDown(self):
        assert self.root.resolve().is_relative_to(self.area)
        shutil.rmtree(self.root)

    def add_sources(self, additions):
        self.sources.update(additions)
        for name, data in additions.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def write_manifest(self, extra=()):
        entries = [{'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                   for name, data in self.sources.items()]
        entries.extend(extra)
        (self.root / release.MANIFEST).write_text(json.dumps({'version': '1.0', 'files': entries}), encoding='utf-8')

    def archive_fixture(self):
        blobs = dict(release.embedded_metadata(self.sources))
        blobs['PYZ.pyz'] = b'compressed archive'
        module = [b'public Python module']
        pyz = SimpleNamespace(toc={'koei_editor.application': (0, 0, 0)}, extract=lambda name, raw=False: module[0])
        archive = SimpleNamespace(toc={name: (0, 0, 0, 0, 'z' if name == 'PYZ.pyz' else 'x') for name in blobs},
                                  extract=lambda name: blobs[name], open_embedded_archive=lambda name: pyz)
        return archive, blobs, module

    def test_archives_contain_only_verified_sources_and_user_downloads(self):
        (self.root / 'work').mkdir()
        (self.root / 'work/private.sav').write_bytes(b'private fixture')
        with patch.object(release, 'verify_executable', return_value=1) as verified:
            assets = release.package(self.root)
        verified.assert_called_once_with(self.root)
        with zipfile.ZipFile(assets[0]) as archive:
            reviewed_docs = {name for name in self.sources if name.startswith('docs/') and name.endswith('.md')}
            self.assertEqual(set(archive.namelist()), set(release.WINDOWS_DOCS) | reviewed_docs |
                             {'licenses/Python-LICENSE.txt', 'UniversalKoeiTecmoSaveEditor-v1.0.exe'})
        with zipfile.ZipFile(assets[1]) as archive:
            prefix = 'UniversalKoeiTecmoSaveEditor-v1.0-Source/'
            self.assertEqual(set(archive.namelist()), {prefix + name for name in self.sources} | {prefix + release.MANIFEST})
            for name, data in self.sources.items():
                self.assertEqual(archive.read(prefix + name), data)
        self.assertEqual(assets[2].read_bytes(), (self.root / 'dist/UniversalKoeiTecmoSaveEditor-v1.0.exe').read_bytes())
        with zipfile.ZipFile(assets[0]) as archive:
            self.assertEqual(assets[2].read_bytes(), archive.read(assets[2].name))
        self.assertEqual(assets[3].read_text().splitlines(),
                         [f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}' for path in assets[:3]])
        with patch.object(release, 'verify_executable', return_value=1):
            second = release.package(self.root, self.root / 'second-output')
        self.assertEqual(assets[1].read_bytes(), second[1].read_bytes())
        with patch.object(release, 'verify_executable', return_value=1), self.assertRaises(ValueError):
            release.package(self.root)

    def test_hash_mismatch_prevents_any_release_output(self):
        (self.root / 'README.md').write_text('Changed after manifest', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'hash or length mismatch'):
            release.package(self.root)
        self.assertFalse((self.root / 'release').exists())

    def test_windows_zip_ships_reviewed_documentation_index_and_supplier_checklist_only(self):
        additions = {'docs/README.md': b'[Remaining inputs](REMAINING_INPUTS.md)\n',
                     'docs/REMAINING_INPUTS.md': b'# Exact further input requirements\n',
                     'docs/releases/v0.9.md': b'# Reviewed historical release\n'}
        self.add_sources(additions)
        self.write_manifest()
        (self.root / 'docs/private-investigation.md').write_bytes(b'Unreviewed research')
        with patch.object(release, 'verify_executable', return_value=1):
            windows_zip = release.package(self.root)[0]
        with zipfile.ZipFile(windows_zip) as archive:
            for name, data in additions.items():
                self.assertEqual(archive.read(name), data)
            self.assertNotIn('docs/private-investigation.md', archive.namelist())
            self.assertNotIn('src/koei_editor/application.py', archive.namelist())

    def test_traversal_and_private_file_entries_are_rejected_before_reading(self):
        for name in ('../private.sav', 'work/private.sav', 'tests/fixture.sav', 'C:/private.sav',
                     'src/koei_editor/games/../private.sav', 'licenses/private.exe', '.git/config',
                     'tests/.runs/test_example.py', 'src/koei_editor/data/account.json',
                     'src/koei_editor/data/sample.dat', 'tools/private_dump.py', 'src/foreign/codec.py',
                     'application.py', 'SOURCE_MANIFEST.json', release.MANIFEST):
            with self.subTest(name=name), self.assertRaises(ValueError):
                release.public_path(name)

    def test_contributor_scaffold_and_test_helper_paths_are_narrowly_allowed(self):
        self.assertEqual(release.public_path('.gitattributes').as_posix(), '.gitattributes')
        for name in release.ADAPTER_TEMPLATE_FILES | release.PUBLIC_TEST_HELPERS | release.PUBLIC_GUIDES:
            with self.subTest(name=name):
                self.assertEqual(release.public_path(name).as_posix(), name)
        for name in ('tools/adapter_template/private.dat', 'tools/adapter_template/fixture.json',
                     'tools/adapter_template/another_parser.py', 'tools/adapter_template/nested/new_game_parser.py',
                     'tools/adapter_template/INSTRUCTIONS.md/../private.dat', 'tools/adapter_template/.private.txt',
                     'tools/adapter_template/new_game_parser.py.bak', 'tests/another_helper.py',
                     'tests/scalar_contract.py/../private.dat', 'tests/helpers/scalar_contract.py'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                release.public_path(name)

    def test_present_git_text_policy_is_required_and_packaged_byte_exactly(self):
        policy = b'*.py text eol=lf\n*.json text eol=lf\n'
        (self.root / '.gitattributes').write_bytes(policy)
        with self.assertRaisesRegex(ValueError, 'Required public sources.*gitattributes'):
            release.verified_sources(self.root)
        self.add_sources({'.gitattributes': policy})
        self.write_manifest()
        with patch.object(release, 'verify_executable', return_value=1):
            assets = release.package(self.root)
        with zipfile.ZipFile(assets[1]) as archive:
            self.assertEqual(archive.read('UniversalKoeiTecmoSaveEditor-v1.0-Source/.gitattributes'), policy)

    def test_personal_path_duplicate_and_mismatched_versions_are_rejected(self):
        self.add_sources({'README.md': ('Local path ' + 'C:' + '/Users/' + 'PrivateOwner/' + 'Documents').encode()})
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'personal home path'):
            release.verified_sources(self.root)
        self.add_sources({'README.md': b'Public document\n'})
        self.write_manifest([{'path': 'src/koei_editor/application.py', 'bytes': 0, 'sha256': '0' * 64}])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            release.verified_sources(self.root)
        self.write_manifest()
        (self.root / 'tools/build_windows.py').write_text("VERSION='2.0'\n", encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'versions do not match'):
            release.verified_sources(self.root)

    def test_embedded_metadata_and_compressed_modules_are_verified(self):
        archive, blobs, module = self.archive_fixture()
        reader = lambda executable: archive
        self.assertEqual(release.verify_executable(self.root, reader), len(blobs))
        module[0] = ('C:' + '/Users/' + 'PrivateOwner/' + 'file.py').encode()
        with self.assertRaisesRegex(ValueError, 'Personal home path'):
            release.verify_executable(self.root, reader)
        module[0] = b'public Python module'
        data_name = 'koei_editor/data/game_metadata.json'
        blobs[data_name] = b'wrong metadata'
        with self.assertRaisesRegex(ValueError, 'differs from manifest'):
            release.verify_executable(self.root, reader)
        blobs[data_name] = self.sources['src/' + data_name]
        archive.toc['private.sav'] = (0, 0, 0, 0, 'x')
        with self.assertRaisesRegex(ValueError, 'Private or unsafe'):
            release.verify_executable(self.root, reader)


if __name__ == '__main__':
    unittest.main()
