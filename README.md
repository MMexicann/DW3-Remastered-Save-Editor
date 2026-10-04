# Dynasty Warriors 3 Remastered Save Editor — v0.3.1 preview

A small Windows editor for **Dynasty Warriors 3: Complete Edition Remastered**
Steam saves. Edit a separate copy, remove repetitive farming, and keep story
completion separate from stat changes.

## Start here

1. Make a copy of `GameStatusData.sav` in a separate folder, such as Documents.
2. Double-click `DW3RemasteredSaveEditor-v0.3.1.exe`. Python is not required.
3. Choose **Open Save Copy**. An untouched backup and its hash manifest are
   created in `DW3EditorBackups` beside that copy.
4. Use individual controls or **Remove The Grind** on the Unlocks tab.
5. Choose **Review Changes**, then **Save Asâ€¦** to create an edited `.sav`.

**Apply** puts the selected entries into the editor's pending changes. **Undo**
reverses the last batch and **Discard Changes** clears pending edits. Nothing
is written until you save. A `.changes.json` report beside each saved copy
explains the changed plaintext bytes, enclosing sizes and encrypted blocks.

**Save Changes** asks before replacing the opened copy and creates another
backup first. **Restore Backupâ€¦** restores a backup to a new filename; it
never overwrites an existing destination. Keep a backup `.sav` and its
matching `.json` together.

The editor refuses live DW3 save paths, Steam Cloud directories, and Steam
Cloud metadata. It does not search for your saves or game installation,
launch the game, upload files, or install anything. Copying an output into
the game's save folder is a separate manual step outside this tool.

## Supported controls

| Area | Available in this version |
|---|---|
| Officers | 42 officers; Merit, permanent Life, Musou, Attack and Defense; individual/all maxima |
| Items | 16 normal items with verified Remaster roll limits; 27 rare items; individual ownership/value controls |
| Weapons | Edit normal bonuses on regular and unique copies; verified fusion values, custom types, Max Selected/All Owned; acquire 82 stock 4th/5th weapons |
| Bodyguards | Four teams: Merit, legal growth/respec and base-stat preview; 9 normal items plus Healing Scroll; 15 weapons with tier-specific bonuses; team equipment |
| Unlocks | Availability of 42 playable officers and 108 playable stages; story completion remains unchanged |

Permanent officer limits are **Life 250, Musou 250, Attack 150, Defense 150**,
and **Merit 99,999**. Normal-item limits were derived from this Remaster's
shipped tables and drop-generation code; some exceed older DW3 guides. The
full item names, IDs and limits appear in [SAVE_FORMAT.md](SAVE_FORMAT.md).

**Remove The Grind** sets those officer maxima, max normal-item rolls, rare
item ownership, supported unique weapons, bodyguard Merit and balanced
legal growth, max bodyguard items, and all 15 bodyguard weapon types with
legal maximum bonuses. It preserves Musou completion, story progress,
officer/stage availability and your teams' equipped item/weapon choices.
**Equip Best Weapons** is a separate action.

**Unlock Everything Supported** adds playable officer and stage availability
to that preset. It preserves completion flags and skips empty, debug and
promotional stage slots.

## Current limits

- Weapons now support normal bonus editing and maximum existing rolls,
  using values obtainable from compatible normal fusion materials. The
  editor writes the resulting bonuses directly; it does not consume materials
  or mark fusion achievements. Base power, elements, hits and rare weapon
  bonuses are preserved. Stock unique acquisition remains separate.
- Normal bonus counts are limited to 6 on ranks 1-3, 7 on fourth weapons,
  and 8 on fifth weapons. Unique weapons retain at least their stock normal
  bonus count; non-starter regular weapons retain at least one. Some high
  rolls have gaps, so the dropdowns offer the verified values only.
- Unique stock exceptions stay specific to their weapon: Volcano Staff's
  Attack +43 is supported there, rather than granted to every weapon.
- Ziluan's two unique weapons require array slots absent from the inspected
  save layout. They cannot be added in this version.
- Bodyguard growth uses a shared budget: **25 points at 99,999 Merit**.
  Life, Attack, Defense and Bow/Moveset spend those points; Count and AI
  advance through Merit gates. Balanced and three favored-stat presets stay
  within the budget. Merit decreases require a valid final allocation.
- Bodyguard HP/Musou/Attack/Defense are derived from growth, rather than
  independent permanent fields. The preview shows base stats before items,
  formation, orders, bodyguard type and battle modifiers. Edit growth to
  change those bases. Rank/model/type choices remain preserved.
- Bodyguard weapon bonuses support three distinct eligible attributes,
  with separate tier and weapon-family limits. The per-copy dropdowns only
  offer proven generated values. Acquisition uses free inventory slots;
  a full inventory is refused without replacing any existing weapon.
- Story rank/progression, Musou completion, officer equipment selections, options,
  records, DLC state and unknown regions are preserved.
- The parser accepts the verified UE 5.6.1 save layout with 84 unique-weapon
  records. Different versions/layouts are refused, rather than guessed.

See [BODYGUARDS.md](BODYGUARDS.md) for the growth rules, equipment controls,
item caps and weapon limits.

See [WEAPON_ROLLS.md](WEAPON_ROLLS.md) for bonus caps, fusion evidence and
the distinction between base power and an Attack bonus.

See [BUG_REVIEW.md](BUG_REVIEW.md) for the v0.3.1 review and fixes.

## Run the source

On Windows with Python 3.11 or newer:

```powershell
python gui.py
```

Or double-click `launch.pyw`. The application uses Tkinter and Windows CNG
through Python's standard library; it needs no runtime package downloads.

Parsing and writing are separate from the GUI:

- `save_codec.py`: AES, envelope and padding validation.
- `unreal.py` / `save_parser.py`: bounded tagged parsing, layout and path checks.
- `models.py`: documents, changes and patches.
- `save_writer.py`: supported edits, size regeneration, backup and atomic writes.
- `officer_weapon_editor.py`: per-copy normal bonus rules and edit planning.
- `bodyguard_growth.py`: verified shared budget, gates, presets and base stats.
- `bodyguard_editor.py`: final-state equipment validation and byte-edit planning.
- `gui.py`: interface, pending changes and confirmation dialogs.
- JSON metadata: documented IDs, names, caps and stock weapon templates.

## Tests and building

```powershell
python -m unittest discover -s tests -v
```

The AES known-answer, path-safety, growth and bodyguard bonus-rule tests run
without private data.
Integration tests use the original private research fixture and are skipped
when that fixture is absent; no player's save is included in this source
package. To run the hidden end-to-end GUI check against your explicit copy:

```powershell
python gui.py --self-test "D:\SaveCopies\GameStatusData.sav" "D:\SaveCopies\EditorTest"
```

The output directory must be new or empty. The test creates working copies,
exercises GUI callbacks with controlled dialogs, and writes
`self-test-report.json`. The input file is never edited. The executable
supports the same opt-in self-test.

See [VALIDATION.md](VALIDATION.md) for the actual verification results and
[BUILDING.md](BUILDING.md) for a reproducible executable build.

The original editor code is MIT licensed. This is an unofficial project,
not affiliated with Koei Tecmo. No game executable, asset package or private
save is distributed here.
