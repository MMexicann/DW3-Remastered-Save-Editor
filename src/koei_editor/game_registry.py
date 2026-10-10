"""Explicit game registration. Parsers never probe or fall back to another game."""
from dataclasses import dataclass
from importlib import import_module
from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.adapter_contract import BoundScalarAdapter, validate_session


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
         '', '.sav', '#92353b', 'koei_editor.games.dw3.gui', 'koei_editor.games.dw3.save_parser', True, 'III'),
    Game('dw8xl', 'DYNASTY WARRIORS 8', 'Xtreme Legends Complete Edition · PC',
         'Resources, officer stats, weapon compatibility, affinity and existing attribute ranks.',
         '', '.dat', '#475f8d', 'koei_editor.games.dw8xl.dw8xl_editor', 'koei_editor.games.dw8xl.dw8xl_editor', True, 'VIII', scalar_backend='koei_editor.shared.verified_editor'),
    Game('dw7xl', 'DYNASTY WARRIORS 7', 'Xtreme Legends Definitive Edition · PC',
         'Gold, officer stats, skill points and active weapons; equipment and skill inspection.',
         '', '.dat', '#526985', 'koei_editor.games.dw7xl.dw7xl_editor', 'koei_editor.games.dw7xl.dw7xl_parser', True, 'VII',
         scalar_backend='koei_editor.games.dw7xl.dw7xl_parser'),
    Game('pw3', 'ONE PIECE: PIRATE WARRIORS 3', 'Windows PC edition',
         'Individual or bulk character stats, special bars and skill slots.',
         '', '.dat', '#257a78', 'koei_editor.games.pw3.pw3_editor', 'koei_editor.games.pw3.pw3_editor', True, 'PW3', scalar_backend='koei_editor.shared.verified_editor'),
    Game('pw4', 'ONE PIECE: PIRATE WARRIORS 4', 'Windows PC · WW/JP/EA revision 15',
         'Beli, existing obtained coin quantities and searchable resource history.',
         '', '.dat', '#297b73', 'koei_editor.games.pw4.pw4_editor', 'koei_editor.games.pw4.pw4_parser', True, 'PW4',
         scalar_backend='koei_editor.games.pw4.pw4_parser'),
    Game('dw4hyper', 'DYNASTY WARRIORS 4 HYPER', 'Native Windows PC edition',
         'Character stats, weapon levels, items, owned harness/orb assignments and bodyguard growth.',
         '', '.dat', '#785d8a',
         'koei_editor.games.dw4hyper.dw4hyper_editor', 'koei_editor.games.dw4hyper.dw4hyper_parser', True, 'IV', True, scalar_backend='koei_editor.games.dw4hyper.dw4hyper_parser'),
    Game('atelier_sophie2', 'ATELIER SOPHIE 2', 'The Alchemist of the Mysterious Dream · PC',
         'Item quality, battle-item refills, inventory inspection and alchemy EXP.',
         '', '.dat', '#827050', 'koei_editor.games.sophie2.atelier_sophie2_editor', 'koei_editor.games.sophie2.atelier_sophie2_parser',
         False, 'SOPHIE 2', True, scalar_backend='koei_editor.games.sophie2.atelier_sophie2_parser'),
    Game('dw4xl_ps2', 'DYNASTY WARRIORS 4', 'Xtreme Legends · SLUS-20812',
         'Character stats, weapon levels, items, owned harness/orb assignments and bodyguard growth.',
         '', '.psu', '#785d8a',
         'koei_editor.games.dw4xl.dw4xl_editor', 'koei_editor.games.dw4xl.dw4xl_parser', True, 'IV XL', True, 'PlayStation 2', scalar_backend='koei_editor.games.dw4xl.dw4xl_parser'),
    Game('origins', 'DYNASTY WARRIORS: ORIGINS', 'Steam PC · slot saves',
         'Gold, Skill Points, bonds, provincial peace, weapon upgrades and battle history.',
         '', '.dat', '#806126', 'koei_editor.games.origins.origins_game_editor', 'koei_editor.games.origins.origins_parser', True,
         'ORIGINS', scalar_backend='koei_editor.games.origins.origins_parser'),
    Game('wo3u', 'WARRIORS OROCHI 3 ULTIMATE', 'Definitive Edition · PC',
         'Officer stats, growth points, gems, crafting, existing ranked attributes and reinforcement reductions.',
         '', '.bin', '#775c82', 'koei_editor.games.wo3u.wo3u_editor', 'koei_editor.games.wo3u.wo3u_parser', True, 'WO3',
         scalar_backend='koei_editor.games.wo3u.wo3u_parser'),
    Game('samurai4dx', 'SAMURAI WARRIORS 4 DX', 'Windows PC edition',
         'Gold, gems, officers, existing weapons and attached skills.',
         '', '.dat', '#91613d', 'koei_editor.games.sw4dx.samurai4dx_editor', 'koei_editor.games.sw4dx.samurai4dx_parser', True, 'SW4',
         scalar_backend='koei_editor.games.sw4dx.samurai4dx_parser'),
    Game('sw4ii', 'SAMURAI WARRIORS 4-II', 'Windows PC edition',
         'Gold, tomes, officer stats, existing weapons and mount stats.',
         '', '.dat', '#91613d', 'koei_editor.games.sw4ii.sw4ii_editor', 'koei_editor.games.sw4ii.sw4ii_parser', True, 'SW4-II',
         scalar_backend='koei_editor.games.sw4ii.sw4ii_parser'),
    Game('dw6', 'DYNASTY WARRIORS 6', 'Native Windows PC edition',
         'Named officer unlocks, existing horse combat stats, named weapon element choices and searchable records.',
         '', '.dat', '#526985', 'koei_editor.games.dw6.dw6_editor', 'koei_editor.games.dw6.dw6_parser',
         True, 'VI', True, scalar_backend='koei_editor.games.dw6.dw6_parser'),
    Game('dw9emp', 'DYNASTY WARRIORS 9 EMPIRES', 'Windows PC · SYSTEMDATA',
         'Existing item quantities; searchable inventory and custom officer records.',
         '', '.bin', '#806126', 'koei_editor.games.dw9emp.dw9emp_editor', 'koei_editor.games.dw9emp.dw9emp_parser',
         False, 'IX E', True, scalar_backend='koei_editor.games.dw9emp.dw9emp_parser'),
    Game('orochiz', 'WARRIORS OROCHI Z', 'Native Windows PC edition',
         'Stock EXP, officer base attack, existing weapon bonuses/attributes and own-pool equipment selection.',
         '', '.dat', '#775c82', 'koei_editor.games.orochiz.orochiz_editor', 'koei_editor.games.orochiz.orochiz_parser',
         True, 'OROCHI Z', True, scalar_backend='koei_editor.games.orochiz.orochiz_parser'),
    Game('stars', 'WARRIORS ALL-STARS', 'Windows PC · revision F4',
         'Available gold and existing material quantities in campaign slots; separate lifetime-gold inspection.',
         '', '.bin', '#827050', 'koei_editor.games.stars.stars_editor', 'koei_editor.games.stars.stars_parser',
         True, 'ALL-STARS', True, scalar_backend='koei_editor.games.stars.stars_parser'),
    Game('hyrule_warriors', 'HYRULE WARRIORS', 'Wii U · APP.BIN',
         'Rupees, existing materials and map cards, weapon stars and ordinary seal KO counters.',
         '', '.bin', '#548247', 'koei_editor.games.hyrule_warriors.editor', 'koei_editor.games.hyrule_warriors.parser',
         True, 'HYRULE', True, 'Wii U', scalar_backend='koei_editor.games.hyrule_warriors.parser'),
    Game('hyrule_definitive', 'HYRULE WARRIORS', 'Definitive Edition · zmha.bin',
         'Rupees, existing materials, weapon stars, ordinary seal KO counters and searchable records.',
         '', '.bin', '#548247', 'koei_editor.games.hyrule_definitive.editor', 'koei_editor.games.hyrule_definitive.parser',
         True, 'HYRULE DE', True, 'Nintendo Switch', scalar_backend='koei_editor.games.hyrule_definitive.parser'),
    Game('age_of_calamity', 'HYRULE WARRIORS: AGE OF CALAMITY', 'Switch · svdt',
         'Rupees, discovered materials, trophies and reports; existing weapon protection and inspection.',
         '', '', '#657b43', 'koei_editor.games.age_of_calamity.editor', 'koei_editor.games.age_of_calamity.parser',
         True, 'CALAMITY', True, 'Nintendo Switch', scalar_backend='koei_editor.games.age_of_calamity.parser'),
    Game('fire_emblem_warriors', 'FIRE EMBLEM WARRIORS', 'Switch · scenario0/1/2 exports',
         'Gold, existing ordinary materials, generic weapon stars and ordinary seal KO counters; named inspection.',
         '', '', '#657b43', 'koei_editor.games.fire_emblem_warriors.editor', 'koei_editor.games.fire_emblem_warriors.parser',
         True, 'FIRE EMBLEM', True, 'Nintendo Switch', scalar_backend='koei_editor.games.fire_emblem_warriors.parser'),
    Game('dw7_ps3', 'DYNASTY WARRIORS 7', 'US/EU · decrypted APP.BIN',
         'Gold and 62 officers’ health, attack, defense, power, speed and skill points.',
         '', '.bin', '#526985', 'koei_editor.games.dw7_ps3.editor', 'koei_editor.games.dw7_ps3.parser',
         True, 'VII PS3', True, 'PlayStation 3', scalar_backend='koei_editor.games.dw7_ps3.parser'),
    Game('dw7e_ps3', 'DYNASTY WARRIORS 7 EMPIRES', 'US · decrypted SYSTEM DATA.BIN',
         'Manual system bonus-point editing; campaign saves use a separate format.',
         '', '.bin', '#526985', 'koei_editor.games.dw7e_ps3.editor', 'koei_editor.games.dw7e_ps3.parser',
         True, 'VII E PS3', True, 'PlayStation 3', scalar_backend='koei_editor.games.dw7e_ps3.parser'),
    Game('sw4_ps3', 'SAMURAI WARRIORS 4', 'US · decrypted DATA.BIN',
         'Gold, eight gems and searchable weapon proficiency/EXP inspection.',
         '', '.bin', '#91613d', 'koei_editor.games.sw4_ps3.editor', 'koei_editor.games.sw4_ps3.parser',
         True, 'SW4 PS3', True, 'PlayStation 3', scalar_backend='koei_editor.games.sw4_ps3.parser'),

    Game('dw8e', 'DYNASTY WARRIORS 8 EMPIRES', 'Windows PC · SystemSave.dat',
         'Existing custom-horse body type; searchable appearance, stats and ability records.',
         '', '.dat', '#526985', 'koei_editor.games.dw8e.dw8e_editor', 'koei_editor.games.dw8e.dw8e_parser',
         True, 'VIII E', True, scalar_backend='koei_editor.games.dw8e.dw8e_parser'),
    Game('wolong', 'WO LONG: FALLEN DYNASTY', 'Windows PC · USERDATA',
         'Genuine Qi, copper, accolades, existing ordinary stack reductions and searchable equipment.',
         '', '.bin', '#806126', 'koei_editor.games.wolong.wolong_editor', 'koei_editor.games.wolong.wolong_parser',
         True, 'WO LONG', True, scalar_backend='koei_editor.games.wolong.wolong_parser'),
    Game('p5strikers_pc', 'PERSONA 5 STRIKERS', 'Windows PC · SAVEDATA.BIN',
         'Money, Persona points, unspent BOND points and existing named consumable/cooking quantities.',
         '', '.bin', '#92353b', 'koei_editor.games.p5strikers_pc.editor', 'koei_editor.games.p5strikers_pc.parser',
         True, 'P5S', True, scalar_backend='koei_editor.games.p5strikers_pc.parser'),
    Game('hyrule_legends', 'HYRULE WARRIORS LEGENDS', 'Nintendo 3DS · zmha.bin',
         'Rupees, materials, existing map cards, weapon stars, ordinary seal counters and My Fairy names.',
         '', '.bin', '#548247', 'koei_editor.games.hyrule_legends.editor', 'koei_editor.games.hyrule_legends.parser',
         True, 'LEGENDS', True, 'Nintendo 3DS', scalar_backend='koei_editor.games.hyrule_legends.parser'),

    Game('ayesha_ps3', 'ATELIER AYESHA', 'The Alchemist of Dusk · PS3 US/Japanese export',
         'Cole, existing stack reductions and searchable inventory quality, properties and effects.',
         '', '.bin', '#827050', 'koei_editor.games.ayesha_ps3.editor', 'koei_editor.games.ayesha_ps3.parser',
         True, 'AYESHA', True, 'PlayStation 3', scalar_backend='koei_editor.games.ayesha_ps3.parser'),

    Game('dw5special', 'DYNASTY WARRIORS 5 SPECIAL', 'Shin Sangokumusou 4 Special · Windows PC',
         'Existing ordinary item ranks, weapon attack/weight and attributes; named officer/bodyguard inspection.',
         '', '.dat', '#526985', 'koei_editor.games.dw5special.dw5special_editor', 'koei_editor.games.dw5special.dw5special_parser',
         True, 'V SPECIAL', True, scalar_backend='koei_editor.games.dw5special.dw5special_parser'),

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
