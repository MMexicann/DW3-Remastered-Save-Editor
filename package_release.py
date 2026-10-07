"""Package only manifest-verified public sources and the built Windows editor."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT=Path(__file__).resolve().parent
ROOT_FILES={'.gitignore','LICENSE'}
SOURCE_SUFFIXES={'.py','.pyw','.json','.md','.txt'}
WINDOWS_DOCS=('README.md','CHANGELOG.md','LICENSE','THIRD_PARTY_NOTICES.md')
PERSONAL_PATH=re.compile(r'(?i)(?:[a-z]:[\\/]+Users[\\/]+(?!Player(?:[\\/]|\b))[^\\/\s"\']+|/(?:home|Users)/[^/\s"\']+)')


def version(root=ROOT):
    values=[]
    for name in ('gui.py','build_windows.py'):
        tree=ast.parse((root/name).read_text(encoding='utf-8'))
        assignments=[node for node in tree.body if isinstance(node,ast.Assign)
                     and any(isinstance(target,ast.Name) and target.id=='VERSION' for target in node.targets)]
        if len(assignments)!=1:raise ValueError(f'{name} must declare one VERSION.')
        value=ast.literal_eval(assignments[0].value)
        if not isinstance(value,str) or not re.fullmatch(r'\d+\.\d+(?:\.\d+)?',value):
            raise ValueError(f'{name} has an unsupported release version.')
        values.append(value)
    if values[0]!=values[1]:raise ValueError('GUI and build versions do not match.')
    return values[0]


def public_path(name):
    if not isinstance(name,str) or '\\' in name or ':' in name:
        raise ValueError('Manifest paths must be relative POSIX paths.')
    path=PurePosixPath(name)
    if path.is_absolute() or any(part in ('..','.') for part in name.split('/')) or str(path)!=name:
        raise ValueError('Manifest path escapes or aliases the source tree.')
    parts=path.parts
    if len(parts)==1:
        allowed=name in ROOT_FILES or path.suffix in SOURCE_SUFFIXES
    elif parts[0]=='tests':
        allowed=len(parts)==2 and parts[1].startswith('test_') and path.suffix=='.py'
    elif parts[0]=='licenses':
        allowed=len(parts)==2 and path.suffix in {'.txt','.terms'}
    elif parts[:2]==('.github','workflows'):
        allowed=len(parts)==3 and path.suffix in {'.yml','.yaml'}
    else:allowed=False
    if not allowed or name=='SOURCE_MANIFEST.json':
        raise ValueError(f'Not a public source file: {name}')
    return path


def verified_sources(root=ROOT):
    root=root.resolve()
    manifest_path=root/'SOURCE_MANIFEST.json'
    if manifest_path.is_symlink():raise ValueError('The source manifest cannot be a symlink.')
    manifest_bytes=manifest_path.read_bytes()
    manifest=json.loads(manifest_bytes)
    release_version=version(root)
    if manifest.get('version')!=release_version:raise ValueError('Manifest version does not match the editor.')
    entries=manifest.get('files')
    if not isinstance(entries,list) or not entries:raise ValueError('The source manifest is empty.')
    sources={}
    for entry in entries:
        if not isinstance(entry,dict) or set(entry)!={'path','bytes','sha256'}:
            raise ValueError('Unsupported source manifest entry.')
        relative=public_path(entry['path']);name=str(relative)
        if name.casefold() in {old.casefold() for old in sources}:raise ValueError('Duplicate manifest path.')
        path=root.joinpath(*relative.parts)
        if (any(root.joinpath(*relative.parts[:index]).is_symlink() for index in range(1,len(relative.parts)+1)) or
            not path.resolve().is_relative_to(root)):
            raise ValueError(f'Source path escapes the repository: {name}')
        data=path.read_bytes()
        if type(entry['bytes']) is not int or len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError(f'Source hash or length mismatch: {name}')
        text=data.decode('utf-8-sig')
        if '\0' in text or PERSONAL_PATH.search(text):
            raise ValueError(f'Binary content or personal home path in public source: {name}')
        sources[name]=data
    required=set(WINDOWS_DOCS)|{'gui.py','build_windows.py','build-requirements.txt','package_release.py',
                               'RELEASE_NOTES.md','.github/workflows/windows-release.yml'}
    missing=required-sources.keys()
    if missing:raise ValueError('Required public sources missing from manifest: '+', '.join(sorted(missing)))
    licenses={name for name in sources if name.startswith('licenses/')}
    if not licenses:raise ValueError('Bundled dependency licenses are missing.')
    sources['SOURCE_MANIFEST.json']=manifest_bytes
    return release_version,sources


def write_zip(path,entries):
    # Fixed ordering, timestamps and permissions make source archives stable.
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=0o100644<<16
            archive.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)


def scan_bundled_data(label,data):
    if data is None:return
    for text in (data.decode('latin-1'),data.decode('utf-16-le',errors='ignore'),
                 data[1:].decode('utf-16-le',errors='ignore')):
        if PERSONAL_PATH.search(text):raise ValueError(f'Personal home path in bundled content: {label}')


def verify_executable(root=ROOT,archive_reader=None):
    """Inspect the built archive in memory, without extracting runtime files."""
    release_version,sources=verified_sources(root)
    executable=root/'dist'/f'DW3RemasteredSaveEditor-v{release_version}.exe'
    if executable.is_symlink() or not executable.resolve().is_relative_to(root.resolve()):
        raise ValueError('The executable must be built inside this repository.')
    binary=executable.read_bytes()
    if not binary.startswith(b'MZ'):raise ValueError('The built executable is not a Windows executable.')
    scan_bundled_data('executable',binary)
    if archive_reader is None:
        from PyInstaller.archive.readers import CArchiveReader
        archive_reader=CArchiveReader
    archive=archive_reader(str(executable));bundled=set()
    for name,entry in archive.toc.items():
        normalized=name.replace('\\','/')
        path=PurePosixPath(normalized)
        if (path.is_absolute() or ':' in normalized or '..' in path.parts or
            any(part.lower() in {'work','tests','fixtures','source-fixtures'} for part in path.parts) or
            path.suffix.lower() in {'.sav','.pak','.key'}):
            raise ValueError(f'Private or unsafe file in executable archive: {name}')
        data=archive.extract(name)
        scan_bundled_data(name,data)
        if normalized in sources and path.suffix=='.json':
            if data!=sources[normalized]:raise ValueError(f'Bundled metadata differs from manifest: {name}')
            bundled.add(normalized)
        if entry[-1]=='z':
            pyz=archive.open_embedded_archive(name)
            for module in pyz.toc:scan_bundled_data(module,pyz.extract(module,raw=True))
        elif path.suffix=='.zip':
            with zipfile.ZipFile(io.BytesIO(data)) as library:
                for module in library.namelist():scan_bundled_data(module,library.read(module))
    expected={name for name in sources if '/' not in name and name.endswith('.json') and name!='SOURCE_MANIFEST.json'}
    if expected-bundled:raise ValueError('Verified metadata missing from executable: '+', '.join(sorted(expected-bundled)))
    return len(archive.toc)


def package(root=ROOT,output=None):
    root=root.resolve();release_version,sources=verified_sources(root)
    name=f'DW3RemasteredSaveEditor-v{release_version}'
    executable=root/'dist'/f'{name}.exe'
    if executable.is_symlink() or not executable.resolve().is_relative_to(root):
        raise ValueError('The executable must be built inside this repository.')
    binary=executable.read_bytes()
    if not binary.startswith(b'MZ'):raise ValueError('The built executable is not a Windows executable.')
    output=Path(output) if output is not None else root/'release'
    assets=[output/f'{name}-Windows.zip',output/f'{name}-Source.zip',output/'SHA256SUMS.txt']
    if any(path.exists() for path in assets):raise ValueError('Release outputs already exist; choose a new output directory.')
    windows={doc:sources[doc] for doc in WINDOWS_DOCS}
    windows.update({path:data for path,data in sources.items() if path.startswith('licenses/')})
    windows[f'{name}.exe']=binary
    prefix=f'{name}-Source/'
    output.mkdir(parents=True,exist_ok=True)
    write_zip(assets[0],windows)
    write_zip(assets[1],{prefix+path:data for path,data in sources.items()})
    with assets[2].open('x',encoding='ascii',newline='\n') as stream:
        for path in assets[:2]:stream.write(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n')
    return assets


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',action='store_true',help='Print the matching GUI/build release version.')
    parser.add_argument('--verify-only',action='store_true',help='Validate public source hashes without creating archives.')
    parser.add_argument('--verify-executable',action='store_true',help='Inspect the built runtime archive (requires PyInstaller).')
    parser.add_argument('--output',type=Path,help='New release output directory (default: release).')
    arguments=parser.parse_args()
    if arguments.version:print(version());return
    if arguments.verify_executable:
        count=verify_executable()
        print(f'Verified {count} bundled archive entries.');return
    if arguments.verify_only:
        release_version,sources=verified_sources()
        print(f'v{release_version}: verified {len(sources)-1} public source files.');return
    for path in package(output=arguments.output):print(path.name)


if __name__=='__main__':main()
