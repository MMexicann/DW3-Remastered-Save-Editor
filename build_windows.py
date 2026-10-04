"""Build this project's standalone Windows GUI; no game/save inputs needed."""
from pathlib import Path
import os
from PyInstaller.__main__ import run

ROOT=Path(__file__).resolve().parent
if os.name!='nt':raise SystemExit('Build on Windows for the Windows CNG runtime.')
data=['officer_names.json','game_metadata.json','unique_weapons.json',
      'verified_limits.json','item_limits.json','native_enums.json',
      'bodyguard_growth.json','bodyguard_items.json','bodyguard_weapons.json','weapon_bonus_rules.json']
args=['--noconfirm','--onefile','--windowed','--name','DW3RemasteredSaveEditor-v0.3.3',
      '--paths',str(ROOT),'--distpath',str(ROOT/'dist'),
      '--workpath',str(ROOT/'build'),'--specpath',str(ROOT/'build')]
for name in data:args.extend(['--add-data',str(ROOT/name)+os.pathsep+'.'])
args.append(str(ROOT/'gui.py'))
run(args)
