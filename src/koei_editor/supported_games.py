"""Supported game/platform inventory, derived from the executable registry.

Add adapters to game_registry.GAMES, then run:
    python -m tools.update_supported_games
This updates the readable index below, docs/SUPPORTED_GAMES.md and README.
Research-only codecs never become supported entries through documentation.
"""
from dataclasses import dataclass

from .game_registry import GAMES


# BEGIN GENERATED SUPPORTED GAME INDEX
# dw3: DYNASTY WARRIORS 3 / Complete Edition Remastered [Windows PC]
# dw8xl: DYNASTY WARRIORS 8 / Xtreme Legends Complete Edition · PC [Windows PC]
# dw7xl: DYNASTY WARRIORS 7 / Xtreme Legends Definitive Edition · PC [Windows PC]
# pw3: ONE PIECE: PIRATE WARRIORS 3 / Windows PC edition [Windows PC]
# pw4: ONE PIECE: PIRATE WARRIORS 4 / Windows PC · WW/JP/EA revision 15 [Windows PC]
# dw4hyper: DYNASTY WARRIORS 4 HYPER / Native Windows PC edition [Windows PC]
# atelier_sophie2: ATELIER SOPHIE 2 / The Alchemist of the Mysterious Dream · PC [Windows PC]
# dw4xl_ps2: DYNASTY WARRIORS 4 / Xtreme Legends · SLUS-20812 [PlayStation 2]
# origins: DYNASTY WARRIORS: ORIGINS / Steam PC · slot saves [Windows PC]
# wo3u: WARRIORS OROCHI 3 ULTIMATE / Definitive Edition · PC [Windows PC]
# samurai4dx: SAMURAI WARRIORS 4 DX / Windows PC edition [Windows PC]
# dw6: DYNASTY WARRIORS 6 / Native Windows PC edition [Windows PC]
# dw9emp: DYNASTY WARRIORS 9 EMPIRES / Windows PC · SYSTEMDATA [Windows PC]
# orochiz: WARRIORS OROCHI Z / Native Windows PC edition [Windows PC]
# stars: WARRIORS ALL-STARS / Windows PC · revision F4 [Windows PC]
# hyrule_warriors: HYRULE WARRIORS / Wii U · APP.BIN [Wii U]
# hyrule_definitive: HYRULE WARRIORS / Definitive Edition · zmha.bin [Nintendo Switch]
# age_of_calamity: HYRULE WARRIORS: AGE OF CALAMITY / Switch · svdt [Nintendo Switch]
# fire_emblem_warriors: FIRE EMBLEM WARRIORS / Switch · scenario0/1/2 exports [Nintendo Switch]
# dw7_ps3: DYNASTY WARRIORS 7 / US/EU · decrypted APP.BIN [PlayStation 3]
# dw7e_ps3: DYNASTY WARRIORS 7 EMPIRES / US · decrypted SYSTEM DATA.BIN [PlayStation 3]
# sw4_ps3: SAMURAI WARRIORS 4 / US · decrypted DATA.BIN [PlayStation 3]
# rotk13_pc: ROMANCE OF THE THREE KINGDOMS XIII / Original PC · revision 14 · TC [Windows PC]
# END GENERATED SUPPORTED GAME INDEX


@dataclass(frozen=True)
class SupportedGame:
    id: str
    title: str
    edition: str
    platform: str
    features: str
    genuine_file_verified: bool


SUPPORTED_GAMES = tuple(
    SupportedGame(game.id, game.title, game.subtitle, game.platform,
                  game.description, game.editing_verified)
    for game in GAMES
)


def markdown_table() -> str:
    """Render the same supported inventory for contributors and the README."""
    lines = [
        '| Game / edition | Platform | Implemented scope |',
        '| --- | --- | --- |',
    ]
    for game in SUPPORTED_GAMES:
        title = f'{game.title} — {game.edition}' if game.edition else game.title
        values = (title, game.platform, game.features)
        lines.append('| ' + ' | '.join(value.replace('|', r'\|') for value in values) + ' |')
    return '\n'.join(lines) + '\n'
