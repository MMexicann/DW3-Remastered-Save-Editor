"""Shared copy-only path policy for every game and backup operation."""
import os
from pathlib import Path, PureWindowsPath
import re
from koei_editor.games.dw3.models import SaveError


def reserved_windows_path(path):
    windows = PureWindowsPath(str(path))
    devices = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'}
    devices.update(prefix + digit for prefix in ('COM', 'LPT') for digit in '123456789\u00b9\u00b2\u00b3')
    return any(part.endswith((' ', '.')) or any(ord(c) < 32 or c in ':<>"|?*' for c in part)
               or part.split('.', 1)[0].rstrip(' ').upper() in devices
               for part in windows.parts if part != windows.anchor)


def _check(path):
    text = str(path).replace('\\', '/').lower()
    if re.search(r'/koeitecmo/(?:dw3ce_re/saved|dynasty warriors origins/savedata)(?:/|$)', text):
        raise SaveError('Use a separate copy outside the live game save folder.')
    # These PC editions save in the game root, not only in a Savedata child.
    if re.search(r'/koeitecmo/(?:dynasty warriors 9 for steam|dynasty warriors 9 empires)(?:/|$)', text):
        raise SaveError('Use a separate copy outside the live Koei Tecmo save folder.')
    if re.search(r'/koeitecmo/(?:atelier sophie 2|nioh[123]?|wolong|wo long|'
                 r'stranger of paradise[^/]*)(?:/|$)', text):
        raise SaveError('Use a separate copy outside the live Koei Tecmo save folder.')
    if re.search(r'/(?:koeitecmo/)?(?:dynasty warriors[^/]*|dynastywarriors[^/]*|'
                 r'one piece pirate warriors[^/]*|oppw[^/]*|samurai warriors[^/]*|'
                 r'(?:warriors|musou) orochi[^/]*|warriors all-stars|berserk[^/]*)/(?:savedata|saved|save)(?:/|$)', text):
        raise SaveError('Use a separate copy outside the live Koei Tecmo save folder.')
    if re.search(r'/sega/steam/p5s(?:/|$)', text):
        raise SaveError('Use a separate copy outside the live Persona 5 Strikers save folder.')
    if re.search(r'/koei/shin sangokumusou 4 special/savedata(?:/|$)', text):
        raise SaveError('Use a separate copy outside the live Dynasty Warriors 5 Special save folder.')
    if re.search(r'/koei/sengoku musou 2 tw/savedata(?:/|$)', text):
        raise SaveError('Use a separate copy outside the live Samurai Warriors 2 save folder.')
    if re.search(r'/steam/userdata(?:/|$)', text) or re.search(r'/userdata/[^/]+/[^/]+/remote(?:/|$)', text):
        raise SaveError('Steam Cloud folders cannot be accessed. Use a separate save copy.')
    if text.rsplit('/', 1)[-1] in ('steam_autocloud.vdf', 'remotecache.vdf'):
        raise SaveError('Steam Cloud metadata cannot be opened or changed.')
    if os.name == 'nt' and reserved_windows_path(path):
        raise SaveError('Use an ordinary file name, without device names or alternate data streams.')


def safe_path(path):
    path = Path(path)
    _check(path)
    _check(path.absolute())
    resolved = path.resolve()
    _check(resolved)
    return resolved
