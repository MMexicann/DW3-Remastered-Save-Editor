"""Read-only research catalog. Catalog rows cannot create editing adapters."""
import json
from pathlib import Path
from game_registry import GAMES


def load_catalog():
    data = json.loads(Path(__file__).with_name('support_catalog.json').read_text(encoding='utf-8'))
    entries = data['games']
    if not isinstance(entries, list):
        raise ValueError('Invalid game research catalog.')
    ids = set()
    for entry in entries:
        if set(entry) != {'id', 'title', 'platform', 'status', 'evidence', 'needed', 'editing_verified'}:
            raise ValueError('Invalid game research entry.')
        if entry['id'] in ids or type(entry['editing_verified']) is not bool:
            raise ValueError('Duplicate or invalid research registration.')
        ids.add(entry['id'])
    verified = {entry['id'] for entry in entries if entry['editing_verified']}
    if verified != {game.id for game in GAMES if game.editing_verified}:
        raise ValueError('Research catalog and verified editor library disagree.')
    return entries
