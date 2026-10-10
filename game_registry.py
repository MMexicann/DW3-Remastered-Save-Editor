"""Explicit game registration. Parsers never probe or fall back to another game."""
from dataclasses import dataclass
from importlib import import_module
from models import SaveError
from adapter_contract import BoundScalarAdapter, validate_session


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
    scalar_backend: str | None = None

    def get_scalar_adapter(self):
        if self not in ALL_ADAPTERS:
            raise SaveError('Unregistered game.')
        if self.scalar_backend is None:
            raise SaveError('This editor uses its own document workflow.')
        return BoundScalarAdapter(self.id, self.extension, import_module(self.scalar_backend))

    def create_editor(self, root, parent, theme='Light', on_theme=None):
        if self not in ALL_ADAPTERS:
            raise SaveError('Unregistered game.')
        Editor = import_module(self.editor_module).Editor
        if getattr(Editor, 'game_id', self.id) != self.id:
            raise SaveError('The registered editor belongs to a different game/platform.')
        if self.scalar_backend is not None and hasattr(Editor, 'backend'):
            if Editor.backend is not import_module(self.scalar_backend):
                raise SaveError('The registered editor and scalar backend do not match.')
            if getattr(Editor, 'save_extension', None) != self.extension:
                raise SaveError('The registered editor and save extension do not match.')
        return validate_session(Editor(root, parent=parent, theme=theme, on_theme=on_theme), self.id)

    def read_save(self, path):
        # Extension check happens before invoking a game's decryption code.
        from pathlib import Path
        if Path(path).suffix.lower() != self.extension:
            raise SaveError(f'{self.title} requires an explicit {self.extension} copy.')
        if self not in ALL_ADAPTERS:
            raise SaveError('Unregistered game.')
        if self.scalar_backend is not None:
            return self.get_scalar_adapter().read_save(path)
        read_save = import_module(self.parser_module).read_save
        return read_save(path)


GAMES = (
    Game('dw3', 'DYNASTY WARRIORS 3', 'Complete Edition Remastered',
         'Character progression, equipment, companions and unlocks.',
         '', '.sav', '#92353b', 'gui', 'save_parser', True, 'III'),
    Game('dw8xl', 'DYNASTY WARRIORS 8', 'Xtreme Legends Complete Edition · PC',
         'Resources, officer stats, weapon compatibility, affinity and existing attribute ranks.',
         '', '.dat', '#475f8d', 'dw8xl_editor', 'dw8xl_editor', True, 'VIII', scalar_backend='verified_editor'),
    Game('dw7xl', 'DYNASTY WARRIORS 7', 'Xtreme Legends Definitive Edition · PC',
         'Gold, officer stats, skill points and active weapons; equipment and skill inspection.',
         '', '.dat', '#526985', 'dw7xl_editor', 'dw7xl_parser', True, 'VII',
         scalar_backend='dw7xl_parser'),
    Game('pw3', 'ONE PIECE: PIRATE WARRIORS 3', 'Windows PC edition',
         'Individual or bulk character stats, special bars and skill slots.',
         '', '.dat', '#257a78', 'pw3_editor', 'pw3_editor', True, 'PW3', scalar_backend='verified_editor'),
    Game('pw4', 'ONE PIECE: PIRATE WARRIORS 4', 'Windows PC · WW/JP/EA revision 15',
         'Beli, existing obtained coin quantities and searchable resource history.',
         '', '.dat', '#297b73', 'pw4_editor', 'pw4_parser', True, 'PW4',
         scalar_backend='pw4_parser'),
    Game('dw4hyper', 'DYNASTY WARRIORS 4 HYPER', 'Native Windows PC edition',
         'Character stats, weapon levels, items and bodyguard growth.',
         '', '.dat', '#785d8a',
         'dw4hyper_editor', 'dw4hyper_parser', False, 'IV', True, scalar_backend='dw4hyper_parser'),
    Game('atelier_sophie2', 'ATELIER SOPHIE 2', 'The Alchemist of the Mysterious Dream · PC',
         'Item quality, battle-item refills, inventory inspection and alchemy EXP.',
         '', '.dat', '#827050', 'atelier_sophie2_editor', 'atelier_sophie2_parser',
         False, 'SOPHIE 2', True, scalar_backend='atelier_sophie2_parser'),
    Game('dw4xl_ps2', 'DYNASTY WARRIORS 4', 'Xtreme Legends · SLUS-20812',
         'Character stats, weapon levels, items and bodyguard growth.',
         '', '.psu', '#785d8a',
         'dw4xl_editor', 'dw4xl_parser', False, 'IV XL', True, 'PlayStation 2', scalar_backend='dw4xl_parser'),
    Game('origins', 'DYNASTY WARRIORS: ORIGINS', 'Steam PC · slot saves',
         'Gold, Skill Points, bonds, provincial peace, weapon upgrades and battle history.',
         '', '.dat', '#806126', 'origins_game_editor', 'origins_parser', True,
         'ORIGINS', scalar_backend='origins_parser'),
    Game('wo3u', 'WARRIORS OROCHI 3 ULTIMATE', 'Definitive Edition · PC',
         'Officer stats, growth points, gems, crafting and existing weapon attributes.',
         '', '.bin', '#775c82', 'wo3u_editor', 'wo3u_parser', True, 'WO3',
         scalar_backend='wo3u_parser'),
    Game('samurai4dx', 'SAMURAI WARRIORS 4 DX', 'Windows PC edition',
         'Gold, gems, officers, existing weapons and attached skills.',
         '', '.dat', '#91613d', 'samurai4dx_editor', 'samurai4dx_parser', True, 'SW4',
         scalar_backend='samurai4dx_parser'),
)

# Opaque research tools stay outside the gameplay library.
RESEARCH_TOOLS = ()
ALL_ADAPTERS = GAMES + RESEARCH_TOOLS

if any(not (game.editing_verified or game.published_format) for game in GAMES):
    raise RuntimeError('The editor library requires native file validation or an implemented published format.')


def get_game(game_id):
    try:
        return next(game for game in ALL_ADAPTERS if game.id == game_id)
    except StopIteration as error:
        raise SaveError('Choose an explicitly registered editor or research tool.') from error
