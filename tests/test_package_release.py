"""Release archive integrity and publication boundary checks; synthetic files only."""
import hashlib
import json
from pathlib import Path
import sys
import shutil
import unittest
import uuid
import zipfile
from types import SimpleNamespace

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
import package_release as release


class PackagingTests(unittest.TestCase):
    def setUp(self):
        area=PROJECT/'work/package-tests';area.mkdir(parents=True,exist_ok=True)
        self.area=area.resolve()
        self.root=area/uuid.uuid4().hex
        self.root.mkdir()
        self.sources={name:b'Public document\n' for name in release.WINDOWS_DOCS}
        self.sources.update({'gui.py':b"VERSION = '1.0'\n",'build_windows.py':b"VERSION = '1.0'\n",
                             'build-requirements.txt':b'pyinstaller==6.22.3\n','package_release.py':b'# Public packaging helper\n',
                             'RELEASE_NOTES.md':b'# v1.0\n','.github/workflows/windows-release.yml':b'name: Windows release\n',
                             'licenses/Python-LICENSE.txt':b'License text\n','tests/test_public.py':b'# Synthetic public test\n'})
        for name,data in self.sources.items():
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        (self.root/'dist').mkdir()
        (self.root/'dist/DW3RemasteredSaveEditor-v1.0.exe').write_bytes(b'MZ synthetic editor executable')
        self.write_manifest()

    def tearDown(self):
        assert self.root.resolve().is_relative_to(self.area)
        shutil.rmtree(self.root)

    def write_manifest(self,extra=()):
        entries=[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
                 for name,data in self.sources.items()]
        entries.extend(extra)
        (self.root/'SOURCE_MANIFEST.json').write_text(json.dumps({'version':'1.0','files':entries}),encoding='utf-8')

    def test_archives_contain_only_verified_sources_and_user_downloads(self):
        (self.root/'work').mkdir();(self.root/'work/private.sav').write_bytes(b'private fixture')
        assets=release.package(self.root)
        with zipfile.ZipFile(assets[0]) as archive:
            self.assertEqual(set(archive.namelist()),set(release.WINDOWS_DOCS)|
                             {'licenses/Python-LICENSE.txt','DW3RemasteredSaveEditor-v1.0.exe'})
        with zipfile.ZipFile(assets[1]) as archive:
            prefix='DW3RemasteredSaveEditor-v1.0-Source/'
            self.assertEqual(set(archive.namelist()),{prefix+name for name in self.sources}|{prefix+'SOURCE_MANIFEST.json'})
            for name,data in self.sources.items():self.assertEqual(archive.read(prefix+name),data)
        self.assertEqual(assets[2].read_bytes(),(self.root/'dist/DW3RemasteredSaveEditor-v1.0.exe').read_bytes())
        with zipfile.ZipFile(assets[0]) as archive:
            self.assertEqual(assets[2].read_bytes(),archive.read(assets[2].name))
        checksums=assets[3].read_text().splitlines()
        self.assertEqual(checksums,[f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}' for path in assets[:3]])
        second=release.package(self.root,self.root/'second-output')
        self.assertEqual(assets[1].read_bytes(),second[1].read_bytes())
        with self.assertRaises(ValueError):release.package(self.root)

    def test_hash_mismatch_prevents_any_release_output(self):
        (self.root/'README.md').write_text('Changed after manifest',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'hash or length mismatch'):release.package(self.root)
        self.assertFalse((self.root/'release').exists())

    def test_traversal_and_private_file_entries_are_rejected_before_reading(self):
        for name in ('../private.sav','work/private.sav','tests/fixture.sav','C:/private.sav',
                     'gui.py/../private.sav','licenses/private.exe','.git/config','tests/.runs/test_example.py'):
            with self.subTest(name=name),self.assertRaises(ValueError):release.public_path(name)

    def test_personal_path_duplicate_and_mismatched_versions_are_rejected(self):
        self.sources['README.md']=('Local path '+'C:'+ '/Users/'+'PrivateOwner/'+'Documents').encode()
        (self.root/'README.md').write_bytes(self.sources['README.md']);self.write_manifest()
        with self.assertRaisesRegex(ValueError,'personal home path'):release.verified_sources(self.root)
        self.sources['README.md']=b'Public document\n';(self.root/'README.md').write_bytes(self.sources['README.md'])
        self.write_manifest([{'path':'gui.py','bytes':0,'sha256':'0'*64}])
        with self.assertRaisesRegex(ValueError,'Duplicate'):release.verified_sources(self.root)
        self.write_manifest();(self.root/'build_windows.py').write_text("VERSION='2.0'\n",encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'versions do not match'):release.verified_sources(self.root)

    def test_embedded_metadata_and_compressed_modules_are_verified(self):
        self.sources['game_metadata.json']=b'{"public":true}'
        (self.root/'game_metadata.json').write_bytes(self.sources['game_metadata.json']);self.write_manifest()
        blobs={'game_metadata.json':self.sources['game_metadata.json'],'PYZ.pyz':b'compressed archive'}
        module=[b'public Python module']
        pyz=SimpleNamespace(toc={'editor':(0,0,0)},extract=lambda name,raw=False:module[0])
        archive=SimpleNamespace(toc={'game_metadata.json':(0,0,0,0,'x'),'PYZ.pyz':(0,0,0,0,'z')},
                                extract=lambda name:blobs[name],open_embedded_archive=lambda name:pyz)
        reader=lambda executable:archive
        self.assertEqual(release.verify_executable(self.root,reader),2)
        module[0]=('C:'+ '/Users/'+'PrivateOwner/'+'file.py').encode()
        with self.assertRaisesRegex(ValueError,'Personal home path'):release.verify_executable(self.root,reader)
        module[0]=b'public Python module';blobs['game_metadata.json']=b'wrong metadata'
        with self.assertRaisesRegex(ValueError,'differs from manifest'):release.verify_executable(self.root,reader)
        blobs['game_metadata.json']=self.sources['game_metadata.json']
        archive.toc['private.sav']=(0,0,0,0,'x')
        with self.assertRaisesRegex(ValueError,'Private or unsafe'):release.verify_executable(self.root,reader)


if __name__=='__main__':unittest.main()
