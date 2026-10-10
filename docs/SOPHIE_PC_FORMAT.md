# Original Atelier Sophie Steam PC

The `atelier_sophie` adapter supports the observed original **Steam app527270**
extensionless `GAMEDATA` gameplay profile. It does not support Sophie DX
(app1502970), Sophie 2, system files or console exports.

## Evidence and native qualification

A player shared an archive in the [original Steam discussion](https://steamcommunity.com/app/527270/discussions/0/3160848559776680273/).
Its 31 gameplay snapshots are each 768,000 bytes, share the same original header
and root/record framing, and contain varying gameplay values. They represent
one player's archive, not 31 independent players. Copies remain outside the
checkout. All 31 decode and roundtrip unchanged exactly; selected resource and
occupied-quality edits in every snapshot preserve all bytes outside the selected
four-byte scalar. Procedural tests are separate from those genuine-file checks.

The native file uses a 32-byte header beginning `01 33 79 c9`, little-endian node
spans and big-endian scalar values. Every observed top-level node is qualified in
order, including `Info`; unknown children, record bytes and trailing padding are
preserved. Revision-2 item and party framing must contain the nine original character
identities. The item pools carry explicit byte extents and 56-byte records.

An [original-PC Steam format discussion](https://steamcommunity.com/app/527270/discussions/0/1743355067112284432/)
reports that these saves have no encryption or checksum. Player
[PC editing discussion](https://gamefaqs.gamespot.com/boards/170933-atelier-sophie-the-alchemist-of-the-mysterious-book/76118568)
and [quality/trait gameplay reports](https://gamefaqs.gamespot.com/boards/170933-atelier-sophie-the-alchemist-of-the-mysterious-book/76095218?page=1)
provide additional direct-edit evidence. No native checksum has been identified;
unchanged snapshots alone do not prove absence. The adapter relies on that
community format evidence. **An edited save loaded and re-saved by the actual
game, or a native save-loader integrity audit, has not been performed.** No game
or third-party editor binary was executed. The interface discloses this limit.

The format facts and implementation were independently derived. No third-party
editor implementation, game assets, save contents or item catalog is redistributed.

## Implemented fields and mechanics

| Mechanic | Implementation and bounds | Dependencies preserved |
| --- | --- | --- |
| Cole | Individual big-endian 32-bit scalar in qualified nested `money` node; edit range 0–999,999 | Rewards, quest history and all other bytes |
| Tess exchange tickets | Individual big-endian scalar in `numOfTickets`, explicit native width four; edit range 0–9,999 | Exchange/reward state and progression |
| Existing basket/container quality | Occupied instance/item identities, native big-endian float32 quality at record +4; eligible finite whole-number originals expose whole-number edits 1–999 | Item identity, quantity/use count, traits, effects, synthesis geometry, equipment and opaque bytes |
| Existing records | Searchable numeric item/instance IDs and quality across six observed pools | No invented names or new ownership |
| Alchemy progression | Read-only qualified `m_lv` and `m_exp` scalars | Level and unlock transitions |

[Players describe Tess tickets](https://www.reddit.com/r/Atelier/comments/uhk7lw)
as group-request rewards exchanged for materials/accessories; earning the first
ticket also opens her shop. Editing the scalar does not simulate earning that
reward or unlock the shop.

Currency limits are deliberately chosen editor limits, **not proven natural game
caps**. Max is disabled for every field. Higher original resources and integral
qualities are preserved and can be restored by assigning the opened value.
Fractional/nonfinite quality values are inspection only. Empty, important-item,
synthesis-work and temporary slots cannot be edited.

The [official original PC manual](https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/527270/manuals/AtelierSophie_manual.pdf?t=1695969954)
explains that material quality, alchemy level and synthesis choices affect item
quality; effects and inherited traits are separate choices. Recipes can depend
on exploration, synthesis and events. The community
[quality discussion](https://gamefaqs.gamespot.com/boards/170933-atelier-sophie-the-alchemist-of-the-mysterious-book/76024489)
notes that a recipe's attainable quality may be below 999. Consequently 999 is
an individual edit limit rather than a claimed attainable maximum for every
item. Quality edits do not recalculate forge/enhancement stats or change derived
equipment fields; equipped records are not exposed for editing.

## Blocked mechanics and required inputs

- Item creation, quantities/uses, synthesis geometry, traits/potentials/effects:
  controlled original native before/after action pairs, qualified item-specific
  applicability and lawful factual ID sources. Player reports warn that adding
  undiscovered traits can interact with encyclopedia discovery. Raw cheat IDs
  alone cannot qualify those dependencies.
- Equipment/enhancement: controlled forge/equip/enhance pairs identifying derived
  stats and equipped references. Ordinary container quality editing does not
  claim to update those dependent fields.
- Character/alchemy EXP, levels, skills and friendship: native threshold/action
  pairs covering reward/unlock transitions. Alchemy EXP is inspection only.
- Recipes, exploration and collections: controlled unlock/discovery pairs and
  prerequisites. Calendar, story and event completion remain blocked separately
  from resource editing.
- Actual game-load integrity: a willing player's controlled edited-load/re-save
  validation or native save-loader analysis. Public no-checksum reports are
  explicitly distinguished from this missing check.

## Sophie DX and Firis candidates

[Barrel Wisdom's independently shared PC saves](https://barrelwisdom.com/blog/atelier-pc-saves)
provide genuine Sophie DX and original/DX Firis gameplay files. Sophie DX is a
177,040-byte `.pcsave` with a plaintext summary and encoded body, unlike the
original profile. Firis original is a 1,228,800-byte tagged native save, with a
separate header/layout. Original Firis has revision-3 item/party nodes and 52-byte item records (100 basket,
4,000 ordinary container slots), unlike Sophie’s revision-2, 56-byte profile.
Its readable nodes alone do not establish absent checksums: Firis-specific
native integrity evidence or a native loader audit remains missing. All are
rejected by this adapter. DX body codec,
applicable native integrity, title/revision schema and controlled mechanic pairs
must each be qualified before support. Runtime structures and PS4 quickcodes
are research leads only; their offsets are not PC disk-save proof.

## Validation

`tests/test_sophie_format.py` covers procedural mixed-endian framing, malformed
and foreign input, dependency eligibility, bounds, unusual opened values,
surgical writes, exact no-op, disabled Max, source-change detection and new-copy
backup/restore. Optional `SOPHIE_SAVE_COPIES` supplies local original `GAMEDATA*`
copies for genuine-file roundtrips and selected surgical edits. No private saves
are stored in tests. GUI verification uses the actual shared safe-copy editor;
actual game loading remains pending as described above.
