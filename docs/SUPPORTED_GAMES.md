# Supported games and platforms

Generated from `koei_editor.game_registry.GAMES`. Run `python -m tools.update_supported_games` after changing an adapter.

| Game / edition | Platform | Implemented scope |
| --- | --- | --- |
| DYNASTY WARRIORS 3 — Complete Edition Remastered | Windows PC | Character progression, equipment, companions and unlocks. |
| DYNASTY WARRIORS 8 — Xtreme Legends Complete Edition · PC | Windows PC | Resources, officer stats, weapon compatibility, affinity and existing attribute ranks. |
| DYNASTY WARRIORS 7 — Xtreme Legends Definitive Edition · PC | Windows PC | Gold, officer stats, skill points and active weapons; equipment and skill inspection. |
| ONE PIECE: PIRATE WARRIORS 3 — Windows PC edition | Windows PC | Individual or bulk character stats, special bars and skill slots. |
| ONE PIECE: PIRATE WARRIORS 4 — Windows PC · WW/JP/EA revision 15 | Windows PC | Beli, existing obtained coin quantities and searchable resource history. |
| DYNASTY WARRIORS 4 HYPER — Native Windows PC edition | Windows PC | Character stats, weapon levels, items, owned harness/orb assignments and bodyguard growth. |
| ATELIER SOPHIE 2 — The Alchemist of the Mysterious Dream · PC | Windows PC | Item quality, battle-item refills, inventory inspection and alchemy EXP. |
| ATELIER SOPHIE — Original Steam PC · GAMEDATA slots | Windows PC | Cole, Tess tickets and existing basket/container quality; searchable inventory and alchemy progression. |
| ATELIER RYZA 2 — Lost Legends & the Secret Fairy · original Steam PC | Windows PC | Existing ordinary item and equipment quality from 1–100; searchable inventory and equipment. |
| FATAL FRAME II — Crimson Butterfly REMAKE · Steam PC | Windows PC | Shared system Photo Point reductions; per-slot inventory, camera and collection inspection. |
| DYNASTY WARRIORS 4 — Xtreme Legends · SLUS-20812 | PlayStation 2 | Character stats, weapon levels, items, owned harness/orb assignments and bodyguard growth. |
| DYNASTY WARRIORS: ORIGINS — Steam PC · slot saves | Windows PC | Gold, Skill Points, bonds, provincial peace, weapon upgrades and battle history. |
| WARRIORS OROCHI 3 ULTIMATE — Definitive Edition · PC | Windows PC | Officer stats, growth points, gems, crafting, existing ranked attributes and reinforcement reductions. |
| SAMURAI WARRIORS 4 DX — Windows PC edition | Windows PC | Gold, gems, officers, existing weapons and attached skills. |
| SAMURAI WARRIORS 4-II — Windows PC edition | Windows PC | Gold, tomes, officer stats, existing weapons and mount stats. |
| DYNASTY WARRIORS 6 — Native Windows PC edition | Windows PC | Named officer unlocks, existing horse combat stats, named weapon element choices and searchable records. |
| DYNASTY WARRIORS 9 EMPIRES — Windows PC · SYSTEMDATA | Windows PC | Existing item quantities; searchable inventory and custom officer records. |
| WARRIORS OROCHI Z — Native Windows PC edition | Windows PC | Stock EXP, officer base attack, existing weapon bonuses/attributes and own-pool equipment selection. |
| WARRIORS ALL-STARS — Windows PC · revision F4 | Windows PC | Gold, existing materials, owned Hero Card selection and searchable card records; separate lifetime earnings. |
| HYRULE WARRIORS — Wii U · APP.BIN | Wii U | Rupees, existing materials and map cards, weapon stars and ordinary seal KO counters. |
| HYRULE WARRIORS — Definitive Edition · zmha.bin | Nintendo Switch | Rupees, existing materials, weapon stars, ordinary seal KO counters and searchable records. |
| HYRULE WARRIORS: AGE OF CALAMITY — Switch · svdt | Nintendo Switch | Rupees, discovered materials, trophies and reports; existing weapon protection and inspection. |
| FIRE EMBLEM WARRIORS — Switch · scenario0/1/2 exports | Nintendo Switch | Gold, existing ordinary materials, generic weapon stars and ordinary seal KO counters; named inspection. |
| DYNASTY WARRIORS 7 — US/EU · decrypted APP.BIN | PlayStation 3 | Gold and 62 officers’ health, attack, defense, power, speed and skill points. |
| DYNASTY WARRIORS 7 EMPIRES — US · decrypted SYSTEM DATA.BIN | PlayStation 3 | Manual system bonus-point editing; campaign saves use a separate format. |
| SAMURAI WARRIORS 4 — US · decrypted DATA.BIN | PlayStation 3 | Gold, eight gems and searchable weapon proficiency/EXP inspection. |
| DYNASTY WARRIORS 8 EMPIRES — Windows PC · SystemSave.dat | Windows PC | Existing custom-horse body type; searchable appearance, stats and ability records. |
| WO LONG: FALLEN DYNASTY — Windows PC · USERDATA | Windows PC | Genuine Qi, copper, accolades, existing ordinary stack reductions and searchable equipment. |
| PERSONA 5 STRIKERS — Windows PC · SAVEDATA.BIN | Windows PC | Money, Persona points, unspent BOND points and existing named consumable/cooking quantities. |
| HYRULE WARRIORS LEGENDS — Nintendo 3DS · zmha.bin | Nintendo 3DS | Rupees, materials, existing map cards, weapon stars, ordinary seal counters and My Fairy names. |
| ATELIER AYESHA — The Alchemist of Dusk · PS3 US/Japanese export | PlayStation 3 | Cole, existing stack reductions and searchable inventory quality, properties and effects. |
| DYNASTY WARRIORS 5 SPECIAL — Shin Sangokumusou 4 Special · Windows PC | Windows PC | Existing ordinary item ranks, weapon attack/weight and attributes; named officer/bodyguard inspection. |
| FIRE EMBLEM WARRIORS: THREE HOPES — Switch · extracted SlotData exports | Nintendo Switch | Gold reductions, owned Shez/Byleth name customization and searchable character/weapon records. |
| DYNASTY WARRIORS 8 EMPIRES — US · decrypted SYSTEM APP.BIN | PlayStation 3 | Existing custom-horse Body Type; searchable appearance, stats and ability records. |
| WARRIORS OROCHI 3 ULTIMATE — US · decrypted APP.BIN · NPUB31505 | PlayStation 3 | Manual unallocated growth points and gems; searchable officer, weapon and inventory inspection. |

Scope is specific to each edition and supported save revision. File-level qualification and actual game loading are separate; see [coverage and blockers](EXPANSION_COVERAGE.md) and [validation](VALIDATION.md). Research-only codecs are excluded.
