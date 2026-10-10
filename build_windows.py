"""Build one standalone Windows application with all registered game interfaces."""
import argparse
import json
import os
from pathlib import Path
from game_registry import ALL_ADAPTERS

ROOT = Path(__file__).resolve().parent
VERSION = '1.4'
DATA = ['officer_names.json', 'game_metadata.json', 'unique_weapons.json',
        'verified_limits.json', 'item_limits.json', 'native_enums.json',
        'bodyguard_growth.json', 'bodyguard_items.json', 'bodyguard_weapons.json',
        'weapon_bonus_rules.json', 'progression_routes.json', 'collection_unlocks.json',
        'origins_evidence.json', 'support_catalog.json', 'LICENSE',
        'THIRD_PARTY_NOTICES.md', 'licenses/atelier-sophie2-save-editor-MIT.txt']


def build_args(root=ROOT):
    args = ['--noconfirm', '--onefile', '--windowed', '--name',
            f'UniversalKoeiTecmoSaveEditor-v{VERSION}', '--paths', str(root),
            '--distpath', str(root / 'dist'), '--workpath', str(root / 'build'),
            '--specpath', str(root / 'build')]
    for name in DATA:
        args.extend(['--add-data', str(root / name) + os.pathsep + Path(name).parent.as_posix()])
    for game in ALL_ADAPTERS:
        for module in dict.fromkeys((game.editor_module, game.parser_module, game.scalar_backend)):
            if module is not None:
                args.extend(['--hidden-import', module])
    args.append(str(root / 'application.py'))
    return args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--print-config', action='store_true', help='Inspect build inputs without compiling.')
    arguments = parser.parse_args()
    if arguments.print_config:
        print(json.dumps(build_args(), indent=2))
        return
    if os.name != 'nt':
        raise SystemExit('Build the Windows EXE on 64-bit Windows for the native CNG/Tk runtime.')
    from package_release import verified_sources
    verified_sources(ROOT)
    from PyInstaller.__main__ import run
    run(build_args())


if __name__ == '__main__':
    main()
