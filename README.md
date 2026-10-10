# Universal Koei Tecmo Save Editor

A lightweight Windows save editor by **Mexican**. Version **1.5** brings eleven game
editors into one standalone application, with a game library, shared Light/Dark
appearance and switching between games without restarting.
Your Light/Dark choice is remembered when you reopen the application.

Contributing a fix or a new game? Start with
[CONTRIBUTING.md](https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/blob/main/CONTRIBUTING.md).
AI coding agents should read
[AGENTS.md](https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/blob/main/AGENTS.md).
New games can use the
[adapter starter](https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/blob/main/adapter_template/INSTRUCTIONS.md)
and shared contract tests in the source download.

## Games and platforms

**Windows PC** is selected by default. Choose **PlayStation 2** for supported
memory-card exports.

| Game | Platform | Editing features |
| --- | --- | --- |
| Dynasty Warriors 3: Complete Edition Remastered | Windows PC | Full editor: officers, weapons, items, bodyguards, unlocks, stories and collections |
| Dynasty Warriors: Origins | Windows PC, Steam slot revisions 16/17/29 | Gold, base-game/DLC Skill Points, existing bonds, provincial peace, eligible weapon reinforcement and manual battle-clear history |
| Dynasty Warriors 4 Hyper | Windows PC | Officer stats/EXP/playable flags, weapon EXP, items, bodyguard points and difficulty |
| Dynasty Warriors 8: Xtreme Legends Complete Edition | Windows PC | Gold, gems, materials, officer stats, four weapon-action compatibility ratings, existing weapon affinity and attribute ranks |
| Dynasty Warriors 7: Xtreme Legends Definitive Edition | Windows PC | Gold; 65 officers' health, attack, defense, power, speed and skill points; switch between existing owned equipped weapons |
| Warriors Orochi 3 Ultimate Definitive Edition | Windows PC, qualified 1.0.0.1 layout | 145 officers' stats, growth points, gems, 58 orb and 295 crafting balances; existing weapon slots and eight qualified attributes |
| Samurai Warriors 4 DX | Windows PC, save revision `0x39EA` | Gold, eight gems, 55 officers' base stats and qualified playable unlocks, existing equipped weapons and attached skill ranks/activation |
| One Piece: Pirate Warriors 4 | Windows PC, WW/JP/EA save revision 15 | Spendable Beli and existing obtained coin quantities; searchable coin records and read-only history |
| One Piece: Pirate Warriors 3 | Windows PC | Character health/attack/defense, special bars and skill slots; level/XP, currency and costume inspection |
| Dynasty Warriors 4: Xtreme Legends | PlayStation 2, USA SLUS-20812 | Officer stats/points, weapon EXP, items, bodyguard points and difficulty in `.psu` exports |
| Atelier Sophie 2: The Alchemist of the Mysterious Dream | Windows PC, Steam 1.08 layout | Existing item/equipment quality, consumable refills within stored capacity, Sophie/Plachta alchemy EXP; inventory inspection |

Each game uses its own save format. The PS2 editor opens exported `.psu` saves;
export the save from your memory card before opening it.

## Getting started

Download `UniversalKoeiTecmoSaveEditor-v1.5.exe` from the
[latest GitHub release](https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/releases/latest)
and run it. The Windows ZIP contains the same executable and user documentation.
No installation or Python setup is needed for the standalone executable.

1. Make a separate copy of your save outside the live game and Steam Cloud folders.
2. Select the platform and game, then choose **Open Save Copy**.
3. Edit individual values or select multiple fields for bulk edits. Max options
   apply to the fields that support them. **Find fields** filters scalar editors
   by field name, group or record; **Max Visible Fields** follows that filter.
4. Use **Review Changes** to inspect pending edits. **Undo** reverses an edit batch.
5. Choose **Save As** to create an edited copy. Automatic backups and backup
   restore are available.
6. Return to **Game Library** to switch games. Each session retains its open copy
   and pending changes.

Equipment and inventory inspectors support **Find records**, including searches
across names, IDs and stored values. Some records use numeric IDs because names
have not been proved for that game's native layout. Unknown records stay intact.

## v1.5 coverage and limits

The four new PC adapters were checked against genuine publicly shared saves for
unchanged roundtrips, integrity and surgical edits. Edited saves have **not** been
loaded in the games. Independent genuine-file qualification remains pending for
the published-format DW4 Hyper, DW4 XL PS2 and Sophie 2 adapters.

WO3 stats use natural limits of 999 and Speed 180. Its resource counters support
individual edits but are excluded from Max where natural limits are unproved.
SW4 DX base stats are manual storage-range edits, also excluded from Max; weapon
skills use each existing slot's stored ceiling. PW4 never changes coin acquisition
flags or lifetime counters. Max preserves higher and unusual existing values.
Story completion, rewards and derived progression stay separate from resources,
stats and content unlocks.

See [the per-game coverage checklist](EXPANSION_COVERAGE.md) for implemented
mechanics, qualified revisions, evidence and exact blockers. Source-only research
for Orochi Z, SW5, Abyss, Stars, DW8 Empires and Nioh 3 does not create writable
library entries. WO4 needs its gameplay DLL; DW9 Empires could not be transferred
for inspection. These are not advertised as supported editors.

## Origins features

Open a separate copy of `SLOT0000.dat` through `SLOT0008.dat`. `USER.dat` contains
system data and is not a gameplay slot.

- Gold: 0–999,999. Base-game and revision 29 DLC Skill Points: 0–999 per pool.
- Existing bonds: level 1–5 and training count 0–999. Training counts are excluded
  from Max; conversations, requests, learned arts and reward claims stay intact.
- Provincial peace: 0–10,000 points, with 10,000 representing 100%. Reward claim
  flags stay intact. Full peace can stop the game's provincial skirmishes.
- Eligible existing weapon reinforcement: 0–99, including weapons starting at +0.
  Weapon IDs, traits, equipment references and empty or reserved inventory records
  stay intact. Special or unknown weapon IDs remain available for inspection.
- Battle-clear history: manually mark one of 35 supported battles as cleared.
  Completed history cannot be reset and is excluded from Max. This changes replay
  completion history; it does not finish the active campaign or grant rewards.

Bond levels alone do not complete every bond event or grant its rewards. Character
and weapon XP, learned skills, active story progression, endings and unlock flags
are preserved. Weapon proficiency editing is withheld because level gains also
affect skills and rewards.
The inspector shows occupied weapon records, including records whose reinforcement
is not qualified for editing. Higher or unusual existing values are kept.

## DW3 features

All existing DW3 functionality remains available:

- All 42 officers: Merit and permanent Life/Musou/Attack/Defense.
- 16 normal and 27 rare items, including supported normal-item maximum values.
- All 84 unique weapons, Ziluan 4th/5th weapons, normal/rare bonuses, individual
  and bulk elements, weapon collection and Tactics costumes.
- Bodyguard Merit, growth, items, weapons, equipment, Nanman models and special
  colors, including the Yellow uniform shortcut.
- All 42 officer unlocks, 108 playable stages, three side stories and 39 supported
  Musou story clears.
- 42 music tracks, 50 movies, between-stage Musou saves and Huanglong Elixirs.
- Backups, Undo, Review Changes, Save As, backup restore and value validation.

## Run or build from source

On Windows with Python and Tkinter:

```powershell
python application.py
```

Or double-click `launch.pyw`. No third-party runtime package is required on
Windows. See [BUILDING.md](BUILDING.md) for the standalone executable build,
[ARCHITECTURE.md](ARCHITECTURE.md) for contributor details and
[VALIDATION.md](VALIDATION.md) for test coverage and validation limits.

## Contact

Discord: `mexicannn`.
[Mexican's Steam profile](https://steamcommunity.com/id/theonlyjuandeagingmexican/).
The application also includes the existing Contact dialog.
