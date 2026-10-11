# Stranger of Paradise: Final Fantasy Origin PC native investigation

The new unregistered [native inspector](../src/koei_editor/research/sopffo/sopffo_native.py)
qualifies complete observed USER and SYSTEM framing and retains exact unchanged
cipher roundtrips. **Gameplay integrity is still unqualified; all writes remain
disabled.** This is implemented inspection, not a supported-game adapter. There
is no account reassignment, flag clearing, checksum repair or guessed PC field.

## Native evidence and edition boundaries

The corrected freely shared
[SaveGamePro page](https://savegame.pro/pc-stranger-of-paradise-final-fantasy-origin-savegame/)
has a working main download button. It redirects to a Dropbox archive containing
an Epic/EOS USER and SYSTEM pair. The separate MediaFire URL in its comments
still returns HTTP 404; that failed comment link is not the only available input.
The author describes a save before the final battle, without cheats. That
description establishes provenance, not controlled action or game-load evidence.
The archive and extracted saves remain outside the checkout and source bundle;
its shortcuts/configuration are not executed or imported into the application.

| Profile | Evidence | Observed complete size | Revision |
| --- | --- | --- | --- |
| Epic launch-era PC USER | Independently acquired freely shared native file | 6,216,976 bytes | `0x22020200` |
| Epic launch-era PC SYSTEM | Same independent archive, distinct file kind | 17,568 bytes | `0x22020200` |
| Later Steam PC USER, two distinct slots | Independently shared native repository files | 6,216,976 bytes each | `0x23013100` |
| Later Steam PC SYSTEM | Same independent repository, distinct file kind | 17,568 bytes | `0x23013100` |
| Later PC SYSTEM source pair | Katana upstream encrypted/decrypted source pair | 17,568 bytes | `0x23013100` |
| Other revisions/current-build assurance | Not acquired/qualified | Unknown | Unknown |
| PS4/PS5/Xbox | No PC schema or field proof follows from console patches | Unqualified | Unqualified |

The independently shared
[niemasd/Game-Saves PC directory](https://github.com/niemasd/Game-Saves/tree/08e8418187862dde9d70877c9fc367fa80304009/PC/Stranger%20of%20Paradise%20-%20Final%20Fantasy%20Origin)
contains two native USER files and a SYSTEM file. Its README identifies Steam
and reports last played on 2023-04-30. A Cheat Engine table coexists, so no clean
modification history, natural limits or controlled action pair is inferred. Only
the native saves were downloaded; no table or third-party executable was run.
These distinct complete USER files close the previous later-USER input gap. The
later Katana SYSTEM source pair remains separate source-reference evidence and
does not identify its own storefront. A stored revision word is reported exactly;
it is not relabelled as a particular retail patch without build evidence.

All four observed kind/revision profiles have these checked envelope facts:

- `RNNUSR` or `RNNSYS`, each followed by two zero bytes, at decoded offset zero;
  USER and SYSTEM selection is explicit and never falls back between parsers.
- Unsigned little-endian revision at `0x08`; the eight-byte revision/context
  span at `0x08..0x0F` repeats at `0x108..0x10F`.
- Unsigned little-endian header/body lengths at `0x14`/`0x18`, with an exact
  `0x100`-byte header and the full remaining file as body.
- AES-128-CBC, with no padding insertion/removal, over the **entire** file.
  All five encrypted independent files reconstruct byte for byte from their decoded
  snapshots. Original header, owner binding, unknown bytes and tail are retained.

The existing project's attributed MIT
[Katana primitives](../src/koei_editor/research/katana/katana_codec.py) provide the
cipher. Upstream commit
[`4c90a2b388438cb27a9752e6eab7333257de215f`](https://github.com/mi5hmash/KatanaSaveDataResigner/tree/4c90a2b388438cb27a9752e6eab7333257de215f)
does not implement a SOP gameplay checksum: its resign operation changes account
context and encrypts. Account reassignment is not part of this investigation.

## Integrity and record investigation

Both revisions' independent USER files have nontrivial opaque last blocks; the
later SYSTEM tail differs from the launch SYSTEM and matches the later source
fixture's pattern. The tail is not assigned a seed/checksum/padding meaning by
appearance. An independent second review tested direct MD5, SHA1, SHA256, SHA512
and BLAKE2 prefix/suffix digests at candidate full-file/body/framing boundaries
against all five independent trailers, without a match. MD5/SHA candidates on
raw ciphertext spans also did not qualify a tail rule. CRC32/Adler32 over the
USER body do not establish the header's opaque words as checksums. The first
decoded body qword is zero across both revisions, unlike the nontrivial Nioh
prefixes; related-game schemas are not imported. Negative candidate checks narrow
hypotheses; they do not prove integrity is absent. No flag or opaque byte has
been erased to make a file pass.

The MIT
[rcfox/SOPInventoryFilter](https://github.com/rcfox/SOPInventoryFilter/tree/043259f429d8752dfb66622fc80e7b09e3636506)
is a **live process-memory** inventory tool, not a native save parser. It
describes duplicated item IDs and `0x148`-byte records, two runtime inventory
arrays, effect slots, stored level/original level, item flags and equipped
references. The independently decoded launch USER does contain repeated
duplicate-ID records at that stride, including the documented potion signature.
However, current source effect interpretation produces incompatible affinity
metadata in the old native equipment. Later Steam equipment can fit the current
effect shape, but a duplicate-ID scan crosses candidate boundaries and admits
noninventory-looking records in both revisions. Its matching runs have different
apparent lengths; these are not qualified native array capacities. Neither runtime addresses
nor a longest matching run qualifies native carried/storage ownership, count or
revision-specific dependencies. No external catalog/source implementation was
copied; numeric lookalikes are not promoted into named fields.

The Apollo PS4
[CUSA29578 patch](https://github.com/bucanero/apollo-patches/blob/0ccc07ed39ea378db83e9901dbfa610b04637d7d/PS4/CUSA29578.savepatch)
contains job-EXP block writes. It has no native PC identity/build, integrity,
reward or job-cap proof. Those absolute console offsets are not used here.

To enable even an otherwise plausible balance field, the essential missing
input is matching PC save-loader/serializer code or an independently verified
native integrity implementation, plus intact USER/SYSTEM copies with displayed
values and one controlled action. Additional random finished saves alone cannot
establish the unknown integrity consumers. Never supply passwords or replace the
source user's account context for this work.

## Mechanic coverage and precise remaining proof

Official updates establish dependencies that prevent unconditional resource,
level, affix and unlock writes. The
[1.20 notes](https://www.jp.square-enix.com/sopffo/topics/2022/10/25/016316.html)
require the first expansion for the second expansion's missions/difficulty,
unlock synthesis through Rift progress, add accessory levels while explicitly
excluding them from average equipment level, raise storage from 4,000 to 4,400,
expand affinity upgrades to ten steps and distinguish NPC job-level-derived
stats from player mastery points. The
[1.30 notes](https://www.jp.square-enix.com/sopffo/topics/2023/01/26/016507.html)
require second-expansion completion for Lufenia and Different Future, gate gear
with new job affinities on the job unlock, gate stronger effects on class changes,
unlock replication through story progress, raise storage to 5,000 and add a sixth
Rift monster quest effect. The
[1.31 notes](https://www.jp.square-enix.com/sopffo/topics/2023/02/15/016565.html)
distinguish two-handed equipment affinity up to 270 and permit some Rift materials
to be received while already above their ordinary possession limit. The
[1.32 notes](https://www.jp.square-enix.com/sopffo/topics/2023/04/06/016640.html)
gate Warrior of Light equipment on both season-pass ownership and main-story
completion, and fix guns dropping without season-pass ownership. These are
mechanics evidence, not native PC offset/cap qualification.

| System | Current implemented result / exact blocker |
| --- | --- |
| Identity, revision, USER/SYSTEM framing, encryption | Complete observed profiles decoded; exact encrypted and decoded unchanged preservation; malformed/foreign framing rejected. Body integrity remains explicitly unknown. |
| Anima shards/crystals, rat tails, Dragon Treasure and crafting resources | No writer. Need native scalar record identity/width, current versus lifetime/reward balances, grant/spend action pairs, item-specific limits and integrity update code. Higher original values must survive; Rift over-cap grants mean a generic clamp is unsafe. |
| Job EXP, levels, limit breaks and job unlocks | No writer. Need per-character/job native records, EXP thresholds, owned limit-break items/caps, job-tree prerequisite and unlock/reward pairs. A PS4 EXP patch or guide's final DLC level target cannot prove a PC cap. |
| Job points, skills, mastery points and class changes | No writer. Need allocated/unspent/earned point relations, learned-node prerequisites, category limits and class unlocks. Ownership, effective skill availability and derived statistics remain separate. |
| Carried/storage inventories and equipment | Read-only private record research; no public inventory fields. Need version-specific native pool headers/bounds, item type/ID catalog, quantity/capacity, instance identity and equipped/preset references. Runtime strides alone do not qualify them. |
| Equipment level, rarity, affinities, Chaos effects and summon blessings | No writer. Need existing-record type qualification, stored versus pre-upgrade levels, allowed category/effect combinations, encoded magnitudes, per-item caps, unlocks and cache consumers. Accessories do not contribute to average equipment level; two-handed affinity has separate mechanics. |
| Smithy upgrades, dismantling, synthesis, replication and appearances | No writer. Need unlock and material consumption/reward pairs, source/destination instance/reference rules and version-specific parameter evidence. Item creation and cosmetic/equipment ownership remain separate. |
| Companions, battle sets and derived stats | No writer. Need named per-character jobs, equipment/preset cross-references, NPC-specific level/stat consumers and resonance state. Do not copy player mastery values into NPC progression. |
| Rift/Labyrinth floors, monsters, feeding, affinity and monster quest effects | No writer. Need current Rift save-slot ownership, monster records, threshold/reward effects, resets and displayed one-action pairs. Later sixth quest effects and over-cap materials are revision dependent. |
| Missions, difficulties, DLC, rewards, customization and story | No writer. Need owned DLC context and independent completion/first-clear reward/limit-break/mission-availability records. Season-pass gear and new weapon/job availability cannot be granted by changing one story flag. |

## Validation boundary

[Nine tests](../tests/test_sopffo_native.py) cover all observed framing profiles,
encrypted/decoded byte-exact no-op, preserved opaque bytes, rejection of every
gameplay/account/flag edit, immutable snapshots and snapshot restoration,
incorrect title/kind/revision/inner context/length/size, early rejection before
full body decryption, unknown body-corruption limitations and privacy of the
framing summary. Six procedural tests pass without private inputs. Optional
`SOPFFO_NATIVE_DIR` exercises the independently acquired Epic pair;
`SOPFFO_STEAM_NATIVE_DIR` exercises the two independent later Steam USER files and
SYSTEM; optional `KATANA_GOLDEN_DIR` separately exercises the later upstream
SYSTEM cipher pair. All nine pass with those external copies configured.

No save was loaded into the actual game by this project. No writable adapter,
GUI save/backup/restore qualification or current-build/game-load assurance is
claimed; these require native integrity and safely proved gameplay fields first.
