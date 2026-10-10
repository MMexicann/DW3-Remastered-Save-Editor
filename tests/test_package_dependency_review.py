"""Independent checks for omissions in registered adapter source closure."""
import unittest

import package_release as release
import tests.test_universal_packaging as packaging_fixture


class RegisteredDependencyReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = packaging_fixture.UniversalPackagingTests('test_universal_sources_cannot_omit_game_module_from_manifest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def _sources(self, modules):
        self.fixture.sources.update(modules)
        for name, raw in modules.items():
            path = self.fixture.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.fixture.write_manifest()

    def test_keyword_editor_and_parser_modules_cannot_be_omitted(self):
        self._sources({
            'game_registry.py': b"Game(id='new', editor_module='new_editor', parser_module='new_parser')\n",
            'new_editor.py': b'# Editor\n',
            'new_parser.py': b'# Parser\n',
        })
        release.verified_sources(self.fixture.root)
        for name in ('new_editor.py', 'new_parser.py'):
            original = self.fixture.sources.pop(name)
            self.fixture.write_manifest()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Required public sources.*' + name):
                release.verified_sources(self.fixture.root)
            self.fixture.sources[name] = original

    def test_unsupported_local_package_dependency_cannot_silently_disappear(self):
        self._sources({
            'game_registry.py': b"Game('new', '', '', '', '', '.dat', '', 'new_editor', 'new_parser')\n",
            'new_editor.py': b'import new_parser\n',
            'new_parser.py': b'import new_package.codec\n',
        })
        # Public packaging deliberately supports flat application modules only.
        # A local package still must trigger a missing-source/error result;
        # importing it must not be silently ignored by the closure verifier.
        package = self.fixture.root / 'new_package'
        package.mkdir()
        (package / '__init__.py').write_bytes(b'# Public package\n')
        (package / 'codec.py').write_bytes(b'# Required codec\n')
        for import_statement in (b'import new_package.codec\n',
                                 b'from new_package import codec\n',
                                 b'import new_package\n'):
            self._sources({'new_parser.py': import_statement})
            with self.subTest(import_statement=import_statement), self.assertRaises(ValueError):
                release.verified_sources(self.fixture.root)


if __name__ == '__main__':
    unittest.main()
