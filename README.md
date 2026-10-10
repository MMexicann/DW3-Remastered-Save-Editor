# Universal Koei Tecmo Save Editor

A lightweight Windows save editor by **Mexican**. Version **1.4** brings seven game
editors into one standalone application, with a game library, shared Light/Dark
appearance and switching between games without restarting.
Your Light/Dark choice is remembered when you reopen the application.

Contributing a fix or a new game? Start with [CONTRIBUTING.md](CONTRIBUTING.md).
AI coding agents should read [AGENTS.md](AGENTS.md). New games can use the
[adapter starter](adapter_template/INSTRUCTIONS.md) and shared contract tests.

## Games and platforms

**Windows PC** is selected by default. Choose **PlayStation 2** for supported
memory-card exports.

| Game | Platform | Editing features |
| --- | --- | --- |
| Dynasty Warriors 3: Complete Edition Remastered | Windows PC | Full editor: officers, weapons, items, bodyguards, unlocks, stories and collections |
| Dynasty Warriors: Origins | Windows PC, Steam slot revisions 16/17/29 | Gold, base-game/DLC Skill Points, existing bonds, provincial peace, eligible weapon reinforcement and manual battle-clear history |
| Dynasty Warriors 4 Hyper | Windows PC | Officer stats/EXP/playable flags, weapon EXP, items, bodyguard points and difficulty |
| Dynasty Warriors 8: Xtreme Legends Complete Edition | Windows PC | Gold, gems, materials, officer health/attack/defense and existing weapon attribute ranks |
| One Piece: Pirate Warriors 3 | Windows PC | Character health/attack/defense, special bars and skill slots; level/XP, currency and costume inspection |
| Dynasty Warriors 4: Xtreme Legends | PlayStation 2, USA SLUS-20812 | Officer stats/points, weapon EXP, items, bodyguard points and difficulty in `.psu` exports |
| Atelier Sophie 2: The Alchemist of the Mysterious Dream | Windows PC, Steam 1.08 layout | Existing item/equipment quality; Sophie and Plachta alchemy EXP |

Each game uses its own save format. The PS2 editor opens exported `.psu` saves;
export the save from your memory card before opening it.

## Getting started

Download `UniversalKoeiTecmoSaveEditor-v1.4.exe` from the GitHub release and run it.
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
