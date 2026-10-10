# Universal Koei Tecmo Save Editor

A free Windows save editor by **Mexican**, with a game library, shared Light/Dark
themes, searchable records, backups, Undo and Review Changes. Switch between
games while keeping each editing session open.

## Supported games

Select the game and platform that match your save. Windows PC is selected by
default. Console editors open extracted or decrypted save exports: `.psu` for
PlayStation 2, `APP.BIN` for Wii U and DW7 PS3, `DATA.BIN` for SW4 PS3, and `svdt`
for Age of Calamity. Export and reimport/resign PS3 saves with Apollo Save Tool.

<!-- BEGIN SUPPORTED GAMES -->
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
<!-- END SUPPORTED GAMES -->

## Download and use

Download the **Windows EXE** from the
[latest GitHub release](https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/releases/latest)
and run it. The **Windows ZIP** includes the same executable and documentation.
The standalone app needs no Python installation.

1. Make a separate copy of your save outside the game and Steam Cloud folders.
2. Select your game/platform and choose **Open Save Copy**.
3. Edit values or use the available bulk actions. **Find fields** and
   **Find records** help locate characters, equipment and inventory entries.
4. Check **Review Changes**; use **Undo** to reverse an edit batch.
5. Choose **Save As** to create an edited copy. Automatic backups and backup
   restore are available.

Return to **Game Library** to switch games. Your sessions and Light/Dark theme
are retained.

## Run from source

From the repository root with Python 3.10 or newer and Tkinter:

```powershell
python -m pip install -e .
python -m koei_editor
```

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md) for development and new adapters.
AI coding agents should read [AGENTS.md](AGENTS.md).
The [documentation index](docs/README.md) includes build instructions and formats.

## Contact

Discord: `mexicannn`.
[Mexican's Steam profile](https://steamcommunity.com/id/theonlyjuandeagingmexican/).
