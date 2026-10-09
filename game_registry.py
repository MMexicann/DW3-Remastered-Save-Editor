"""Explicit game registration. Parsers never probe or fall back to another game."""
from dataclasses import dataclass
from importlib import import_module
from models import SaveError


@dataclass(frozen=True)
class Game:
    id: str
    title: str
    subtitle: str
    description: str
    status: str
    extension: str
    accent: str
    editor_module: str
    parser_module: str
    editing_verified: bool = False
    emblem: str = ''
    published_format: bool = False
    platform: str = 'Windows PC'

    def create_editor(self, root, parent, theme='Light', on_theme=None):
        if self not in ALL_ADAPTERS:
            raise SaveError('Unregistered game.')
        Editor = import_module(self.editor_module).Editor
        return Editor(root, parent=parent, theme=theme, on_theme=on_theme)

    def read_save(self, path):
        # Extension check happens before invoking a game's decryption code.
        from pathlib import Path
        if Path(path).suffix.lower() != self.extension:
            raise SaveError(f'{self.title} requires an explicit {self.extension} copy.')
        if self not in ALL_ADAPTERS:
            raise SaveError('Unregistered game.')
        read_save = import_module(self.parser_module).read_save
        return read_save(path)


GAMES = (
    Game('dw3', 'DYNASTY WARRIORS 3', 'Complete Edition Remastered',
         'Character progression, equipment, companions and unlocks.',
         '', '.sav', '#92353b', 'gui', 'save_parser', True, 'III'),
    Game('dw8xl', 'DYNASTY WARRIORS 8', 'Xtreme Legends Complete Edition · PC',
         'Gold, gems, materials, officer stats and existing weapon attribute ranks.',
         '', '.dat', '#475f8d', 'dw8xl_editor', 'dw8xl_editor', True, 'VIII'),
    Game('pw3', 'ONE PIECE: PIRATE WARRIORS 3', 'Windows PC edition',
         'Individual or bulk character stats, special bars and skill slots.',
         '', '.dat', '#257a78', 'pw3_editor', 'pw3_editor', True, 'PW3'),
    Game('dw4hyper', 'DYNASTY WARRIORS 4 HYPER', 'Native Windows PC edition',
         'Character stats, weapon levels, items and bodyguard growth.',
         '', '.dat', '#785d8a',
         'dw4hyper_editor', 'dw4hyper_parser', False, 'IV', True),
    Game('dw4xl_ps2', 'DYNASTY WARRIORS 4', 'Xtreme Legends · SLUS-20812',
         'Character stats, weapon levels, items and bodyguard growth.',
         '', '.psu', '#785d8a',
         'dw4xl_editor', 'dw4xl_parser', False, 'IV XL', True, 'PlayStation 2'),
)

# Opaque research tools stay outside the gameplay library.
RESEARCH_TOOLS = (
    Game('origins', 'DYNASTY WARRIORS: ORIGINS', 'A new legend begins',
         'Inspect save copies, keep verified backups and compare snapshots.',
         'Research only · gameplay editing unavailable', '.dat', '#806126', 'origins_gui', 'origins_editor', False, 'ORIGINS'),
)
ALL_ADAPTERS = GAMES + RESEARCH_TOOLS

if any(not (game.editing_verified or game.published_format) for game in GAMES):
    raise RuntimeError('The editor library requires native file validation or an implemented published format.')


def get_game(game_id):
    try:
        return next(game for game in ALL_ADAPTERS if game.id == game_id)
    except StopIteration as error:
        raise SaveError('Choose an explicitly registered editor or research tool.') from error
