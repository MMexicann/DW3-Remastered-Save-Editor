# Pirate Warriors 4 and Warriors: Abyss PC evidence

PW4 has a qualified native PC revision-15 editor for spendable Beli and quantities
of already obtained coins. Abyss remains an unregistered, read-only research
candidate. No attached executable was executed. No player save, binary, unpacked
code, account identifier or private fixture is included in the distribution.

## Pirate Warriors 4

### Supported envelope and native serialization

The attached x64 executable identifies `OP4WINUSER.dat` and `OP4WINSLOT%04d.dat`.
The mapped editor accepts only native `0x27161C` PC slots; the `0x2804` system
save is excluded. Little-endian `u16` checksum and seed precede the encrypted
payload. Complete `u32` words are XORed after advancing this 32-bit LCG:

```text
state = (state * 0x5B1A7851 + 0xCE4E) modulo 2^32
```

Region advances per word are WW/JP/EA=1, AS=4 and EU/NA=3. The editor explicitly
qualifies the one-step family; three-/four-step files are rejected. The checksum
is the decrypted `u16` word sum modulo 65536. Native functions are
`0x14159DBE0`, `0x14159DD00`, `0x14159DE10`; the step table is `0x14197C140`.

A genuine, freely shared PC slot was downloaded through the public Steam guide
“Pirate Warriors 100% save data for all dlc.(it's99.9%true)”. The completion label
is its uploader's claim. Its original download address remains private under
the contributor fixture policy. The native file has the expected size and its
unchanged roundtrip is byte exact. Three-/four-step decryptions fail checksum;
WW cannot be distinguished from the identical JP/EA arithmetic. No matching
system save, controlled before/after pair or edited game-load test is available.

The native stream starts at decoded payload `0x618` (raw `0x61C`). Serializer
functions `0x14131D750` and `0x14131D960` use `0x80` object headers with `u32`
checksum, total subtree length and revision at 0/4/8. All 144 top-level subtree
lengths and **145 own-body checksums** are validated. Battle subtree index 5 has
own body `0x1D730` and a nested `0x420` child. Parent integrity excludes that
child. Native checksum function `0x1415F1150` sums own-body bytes and clears bit
31; the bounded objects cannot reach its high-word overflow threshold.

Only the demonstrated revision-15 ordered layout is accepted. The attached
writer emits revision22 and has conversion hooks; changing headers to22 is
unsafe. Unknown header/body bytes and trailing capacity remain unchanged.
Damaged native checksums are rejected even when the outer checksum is repaired.
Only an edited object's checksum and the outer checksum are recomputed.

### Proven resource mappings and dependencies

RTTI identifies profile vtable `0x14196E5D0`. Getter `0x14023D9F0` gives body
length `0x1065C`; `0x14023DA00` returns object+`0x10`. Serialization therefore
maps profile object+`0x14` to payload `0x6BC0`. Native Beli reward/update routines
`0x14132A670` and `0x1412DCA80` read/update that current balance and cap it at
**999,999,999**. They separately update lifetime earnings at object+`0x7A0`
(payload`0x734C`), capped at4,000,000,000. Lifetime earnings remain read only:
achievement/reward dependencies are not fully mapped, and setting a resource
balance does not represent earning it through gameplay.

Slot-summary renderer `0x14159EB00` reads playtime (profile+`0x10`) and completion
getters `0x1415EE250`, `0x1415EE1C0`, `0x1415EE5B0`. It does not read current
Beli. Hours/minutes and completion percentages have mirrored numeric metadata
at payload`0x600`; the reader checks agreement and preserves them during edits.

`CDataSaveCoin` vtable `0x141953A70`, constructor `0x1412FC2E0` and body getter
`0x1400B70B0` identify root-list entry9, body`0x19400`, payloadbody`0xB8988`.
The equal-sized `CDataSaveExtraAttack` is entry7 and is never substituted.
The physical coin pool has`0x840` records of stride`0x30` plus`0x800` trailing
bytes. Native reward and consume operations admit IDs0..399 and catalog type≤3.
Each coin has distinct counters at body-relative offsets0 earned,4 spent,8
current quantity, and an obtained/notification flag byte at12.

Reward function`0x1412F5D60` **unconditionally caps current quantity999** for
admitted coin IDs, separately caps cumulative earned99,999, and sets obtained
bit0. Consume function`0x1412F5CD0` floors current quantity0 and separately updates
spent history. Collection percentage function`0x14119CC90` counts earned>0,
rather than current quantity; changing quantity alone preserves that criterion.

The editor qualifies only records with both earned>0 and obtained bit0, IDs0..399.
It permits current quantity0..999, including exhausted owned records. It never
creates coins or changes earned/spent history, obtained/notification flags, DLC
ownership, rarity, growth maps or reward claims. All physical entries beyond399,
unqualified rows, unknown bits and trailing bytes remain unchanged. Native coin
names and rarity tables reside in external fixed-data assets that were not
attached; the searchable GUI truthfully labels **native coin IDs**, without
guessing character names or assigning rarity from quantity. The reviewed native
slot contains280 qualified records. Max preserves existing quantities above999
and Beli balances above999,999,999; returning to an original unusual value unstages.

The GUI exposes Resources and Owned coins, searchable native IDs, visible-record
Max, Undo, Review Changes, a read-only earned/spent/flag inspector, backups and
safe Save As. Source copies are never overwritten and changed-source snapshots
are rejected. Restores validate the exact bounded bytes being restored.

### Coverage checklist

| System | Current implementation or exact blocker |
| --- | --- |
| Spendable Beli | Implemented0..999,999,999; existing higher values preserved by Max. |
| Lifetime Beli/rewards | Read-only native mapped counter; achievements/reward thresholds remain unqualified. |
| Coin inventory | Existing obtained records' quantity0..999; read-only earned/spent/flags. Coin acquisition, exact display names, rarity/catalog types and DLC IDs need external fixed-data assets or controlled display-correlated copies. |
| Character unlocks/DLC | Missing controlled unlock pair and DLC entitlement/save relationship; no unlock action. |
| Beginning/character Growth Maps | Node states, costs and dependent stat/skill rewards require fixed-data node catalogs and controlled node-purchase copies. |
| Stats/skills | Growth-map stats may be derived; writable base values and unlock/equipment dependency layout unqualified. |
| Equipped skills/specials | Extra-attack class identified; valid ability IDs, unlock state, capacity and equipped references unmapped. |
| Soul Maps/Soul ranks | Runtime state clues are distinct from ordinary Growth Maps; absent disk/display correlation and supported revision conversion. |
| Costumes | Asset model names do not prove save ownership, equipped state or entitlement. |
| Dramatic/Free/Treasure Log | Stage IDs, rank/reward flags and result dependencies lack displayed/native correlation. Story completion stays separate from resources. |
| DLC adventures/challenges | Matching DLC/revision native copies and controlled result/reward pairs missing. |
| Gallery/movies/music/records | Coin collection criterion mapped but individual unlock bits and record/reward dependencies unqualified. |
| Weapons/fusion/mounts | Not established as PW4 save mechanics; no invented controls. |

Public sources consulted: [Glubus/oppw4-sdk](https://github.com/Glubus/oppw4-sdk)
commit`ed00f9fa0dae4ac561106c9e0d93cd2bcc44be88` and
[Glubus/oppw4-data](https://github.com/Glubus/oppw4-data)
commit`9b544c4c961db6985f5a5079c9b97aef24a1cb10`. The SDK has no located license;
no source or asset data was copied. These are runtime/asset research rather than
a disk-save editor. Documented Beli/reward function identities were independently
checked against the attached executable; several older RVAs do not describe it.

## Warriors: Abyss

The attached x64 executable's code section is SteamStub-wrapped. It was inspected
using static header decoding and AES transforms on a private copy, never run.
The save service identifies `SYSTEMDATA.BIN`, `GAMEDATA%02d.BIN`, `SAVEDATA` and
the Warriors Abyss title folder. Steam application ID 3178350 is corroborated
by the wrapper metadata and public game pages.

At `0x14041AEB0`, system/game allocations are `0x2800`/`0x30000` bytes, both
aligned. The first 16 bytes are plaintext ASCII `470558d4d8015d9f`.
The remaining bytes use AES-256-CBC with IV
`e1c1c49f9a3019341ea820f99fd09a83`. Decrypted bytes first contain the second
16-byte marker `a1423bc7d48e148b`, followed by serialization beginning with
little-endian revision `0xA4`. The native AES tables match standard AES; they
are not evidence of a custom cipher. CBC decryption is at `0x14041A330`;
encryption/decryption primitives are at `0x140418010`/`0x1404191B0`.

Key setup at `0x14041A952` obtains an unsigned 64-bit platform save-owner value,
XORs `0xFABE9C015F6E379A`, formats unsigned decimal ASCII and pads with NULs to
32 bytes. The original owner's context is essential, not a universal hardcoded
title key. The candidate API requires it explicitly on every operation and
does not retain or return it. It does not guess accounts or reassign ownership.

No genuine freely shared Abyss save with its necessary original-owner context
was located. GitHub queries located mechanics/build planners, not a qualifying
PC save editor or native fixture. Public Steam guides were reviewed. Nexus
initially denied requests; the later follow-up accessed its public game/mod
listing successfully but located no qualifying native save or save codec.
The earlier Reddit access failure is not treated as evidence that saves do not exist.
Gameplay serialization subroutines and inner integrity coverage remain
unqualified. CBC and known markers do not authenticate arbitrary body changes;
the tests demonstrate that limitation and keep `integrity_verified` and
`writable` false. Native revision-conversion hooks were observed, but only
the statically emitted `0xA4` is admitted for candidate research.

### Coverage checklist

| System | Required distinction/dependency | Current status and precise blocker |
| --- | --- | --- |
| Karma Embers and hero recruitment | Persistent recruitment currency versus in-run resources | Genuine system/game copies with original-owner context and one recruitment/spend pair missing. |
| Permanent hero growth/transcendence | Permanent enhancement versus levels gained during a run | Hero records, growth thresholds and unlock dependencies not correlated with native bytes. |
| Unique weapons and limit breaks | Obtained rewards versus trait/stat effects | Mechanics established in public planners; native ownership/reward flags and requirements unmapped. |
| Emblems/traits | Player traits versus support traits; derived team totals | Planner data shows totals are computed from chosen heroes; no guessed editable aggregate fields. |
| Summon skills and Unique Tactics | Specific emblem counts/hero dependencies versus actual unlocks | Dependencies documented in planners; save-backed prerequisites and equipped hero IDs unmapped. |
| Party/companions and formations | Recruited persistent roster versus run-specific support selection | No native record boundaries, valid references or controlled party-change pair. |
| Treasure/equipment and consumables | Run pickups versus permanent collection/unlocks | Persistence and item ID/quantity layouts need native paired saves. |
| Traversal level and clear history | Difficulty unlocks, clear rewards and story separation | No corresponding native progression pair; no completion action added. |
| Stage/run progress and bosses | Temporary run state versus historical completion | Resume serialization and reward-claim dependencies unmapped. |
| DLC heroes/costumes | Installed content versus save ownership and hero revisions | Requires matching DLC/revision copies; no entitlement assumptions. |
| Collections, records and presentation unlocks | Discovered/unlocked entries versus derived counters | Presence and byte layout require native evidence; no invented gallery controls. |
| Weapon fusion/mount systems | Only implement mechanics actually present | Not established for this title; no transplanted controls. |

Mechanics sources: [YeanGO/musou-abyss-guideWeb](https://github.com/YeanGO/musou-abyss-guideWeb)
and [Wynathan/wynathan-abyss](https://github.com/Wynathan/wynathan-abyss), whose
README identifies Update 8/v1.8.0 and distinguishes Transcended heroes and Unique
Weapons. Steam guides reviewed include “Starter guide for beginners” (3444300118),
“Easy Clears Farming Build” (3432580338), “Warriors Abyss: Origins Ultimate F.A.Q”
(3665782940), “Beat Level 5 With Any Hero” (3449663060), and “Text Fixes for
Companion Traits in patch 1.8.0” (3784084267). No planner source/data was copied.
[Steamless](https://github.com/atom0s/Steamless) was consulted for private static
wrapper inspection; its restricted license is not treated as permission to
distribute a derivative unpacker, and none is included.

## Verification

`tests/test_pw4_format.py` has10 passing tests with the private genuine PW4 copy:
unchanged roundtrip; targeted Beli/coin edits in memory; all native object checks;
malformed size/region/revision/metadata rejection; qualified ownership; history,
unknown bytes and higher values preserved; staging, review, backups, source-change
protection and restores. Procedural fixtures test preservation with distinctive
unknown bytes; they are explicitly not game-load evidence. The native test uses
`PW4_SAVE_COPY` and distributes no fixture. No edited save was loaded in game.

`tests/test_pw4_review.py` adds independent adversarial coverage for exhausted
coins, unknown flags/history, higher quantities, surgical coin integrity, exact
integer snapshot seeds and backup replacement races. The focused five tests pass, including a separate GUI workflow.
`tests/test_pw4_gui.py` covers searching native coin IDs, Apply, Review, Undo,
visible Max, read-only inspection, themes, backup and Save As with procedural
data. The combined native-format, GUI and independent review run under Xvfb passes
**16/16 tests**. Both GUI workflows use procedural data; the native fixture
validates format roundtrips and targeted in-memory edits. GUI validation is
separate from game-load validation.

The candidate codec suite has13 tests. With the reviewed PW4 copy12 pass and1
skips (native Abyss copy/context absent); without private fixtures11 pass and2
skip. It exercises independent arithmetic vectors, both capacities, wrong
regions/owners, checksum/marker failures, immutable snapshots and forged/edited
snapshot rejection. Abyss body changes are deliberately not accepted as
integrity-verified. Optional `ABYSS_SAVE_COPY`/`ABYSS_SAVE_OWNER_CONTEXT` remain
local and are never published. Neither title has actual game-load validation.

## Unreleased follow-up research (2026-10-10)

The attached Abyss image was decoded again entirely as static analysis: adjacent
DWORD SteamStub header XOR, AES-ECB IV decoding, and CBC transformation of the
explicit code section into a private analysis image. No binary was executed and
no unpacked image or unpacker is distributed. Native save service confirms system
versus game capacities and chooses registered save objects through callbacks.
`0x1403F96E0` reads/writes the four-byte revision and rejects unsupported newer
low-byte revisions; `0x1403F9620` serializes selected registered objects using
their virtual `+0x10` handlers and category bytes. These functions are not a
field map or checksum proof: the category-selected object list, each object's
serialization, and gameplay integrity coverage still require qualification.
There is no justified scalar-writing fallback around the owner-dependent key.

Fresh GitHub title queries find mechanical planners, translations and purported
trainers rather than a source-backed disk-save editor. The additional
[Suyukn/warriors-abyss-tool](https://github.com/Suyukn/warriors-abyss-tool) describes
v1.8 data, 141 heroes, 54 emblems, transcendence costs and 18 Origins DLC heroes.
Its localStorage/exported JSON stores **planner teams**, not `SYSTEMDATA.BIN` or
`GAMEDATA##.BIN`. Steam save-crash/modding discussions and save-guide searches,
Nexus's game listing, and public save-site title searches did not supply a genuine
PC save plus its original unsigned owner context. No planner/translation/trainer
was executed or packaged.

The concrete prerequisite remains a complete genuine PC `SYSTEMDATA.BIN` and/or
`GAMEDATA00.BIN` (or another exact two-digit game slot) from the same original
export context, with that save's original unsigned platform owner value. The
owner value is supplied privately through the opt-in candidate interface, never
guessed from an unrelated profile. Controlled recruitment/spend/growth/run pairs
would then separate persistent progression, run resume data and reward claims.
Decryption alone cannot qualify body edits; until inner integrity and the chosen
object schema are proven the candidate stays read-only and unregistered.
