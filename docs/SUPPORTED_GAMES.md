# Supported games and platforms

Generated from `koei_editor.game_registry.GAMES`. Run `python -m tools.update_supported_games` after changing an adapter.

| Game / edition | Platform | Implemented scope |
| --- | --- | --- |
| DYNASTY WARRIORS 3 — Complete Edition Remastered | Windows PC | Character progression, equipment, companions and unlocks. |
| DYNASTY WARRIORS 8 — Xtreme Legends Complete Edition · PC | Windows PC | Resources, officer stats, weapon compatibility, affinity and existing attribute ranks. |
| DYNASTY WARRIORS 7 — Xtreme Legends Definitive Edition · PC | Windows PC | Gold, officer stats, skill points and active weapons; equipment and skill inspection. |
| ONE PIECE: PIRATE WARRIORS 3 — Windows PC edition | Windows PC | Individual or bulk character stats, special bars and skill slots. |
| ONE PIECE: PIRATE WARRIORS 4 — Windows PC · WW/JP/EA revision 15 | Windows PC | Beli, existing obtained coin quantities and searchable resource history. |
| DYNASTY WARRIORS 4 HYPER — Native Windows PC edition | Windows PC | Character stats, weapon levels, items and bodyguard growth. |
| ATELIER SOPHIE 2 — The Alchemist of the Mysterious Dream · PC | Windows PC | Item quality, battle-item refills, inventory inspection and alchemy EXP. |
| DYNASTY WARRIORS 4 — Xtreme Legends · SLUS-20812 | PlayStation 2 | Character stats, weapon levels, items and bodyguard growth. |
| DYNASTY WARRIORS: ORIGINS — Steam PC · slot saves | Windows PC | Gold, Skill Points, bonds, provincial peace, weapon upgrades and battle history. |
| WARRIORS OROCHI 3 ULTIMATE — Definitive Edition · PC | Windows PC | Officer stats, growth points, gems, crafting and existing weapon attributes. |
| SAMURAI WARRIORS 4 DX — Windows PC edition | Windows PC | Gold, gems, officers, existing weapons and attached skills. |
| DYNASTY WARRIORS 6 — Native Windows PC edition | Windows PC | Named officer unlocks, existing horse combat stats and searchable officer, weapon and horse records. |
| DYNASTY WARRIORS 9 EMPIRES — Windows PC · SYSTEMDATA | Windows PC | Existing item quantities; searchable inventory and custom officer records. |
| WARRIORS OROCHI Z — Native Windows PC edition | Windows PC | Stock EXP, officer base attack, existing weapon attack bonuses, attribute capacity and owned attribute ranks. |
| WARRIORS ALL-STARS — Windows PC · revision F4 | Windows PC | Available gold and existing material quantities in campaign slots; separate lifetime-gold inspection. |
| HYRULE WARRIORS — Wii U · APP.BIN | Wii U | Rupees, existing materials and map cards, weapon stars and ordinary seal KO counters. |
| HYRULE WARRIORS — Definitive Edition · zmha.bin | Nintendo Switch | Rupees, existing named material quantities and searchable character, fairy-food and weapon records. |
| HYRULE WARRIORS: AGE OF CALAMITY — Switch · svdt | Nintendo Switch | Rupees, discovered materials, trophies and reports; existing weapon protection and inspection. |
| FIRE EMBLEM WARRIORS — Switch · scenario0/1/2 exports | Nintendo Switch | Gold, existing ordinary materials, generic weapon stars and ordinary seal KO counters; named inspection. |
| DYNASTY WARRIORS 7 — US/EU · decrypted APP.BIN | PlayStation 3 | Gold and 62 officers’ health, attack, defense, power, speed and skill points. |
| DYNASTY WARRIORS 7 EMPIRES — US · decrypted SYSTEM DATA.BIN | PlayStation 3 | Manual system bonus-point editing; campaign saves use a separate format. |
| SAMURAI WARRIORS 4 — US · decrypted DATA.BIN | PlayStation 3 | Gold, eight gems and searchable weapon proficiency/EXP inspection. |
| ROMANCE OF THE THREE KINGDOMS XIII — Original PC · revision 14 · TC | Windows PC | City gold, supplies, population, wounded troops, fealty, commerce, farming, culture and troop proficiencies. |

Scope is specific to each edition and supported save revision. File-level qualification and actual game loading are separate; see [coverage and blockers](EXPANSION_COVERAGE.md) and [validation](VALIDATION.md). Research-only codecs are excluded.
