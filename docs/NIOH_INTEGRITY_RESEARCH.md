# Nioh / Nioh 2 native integrity research

Nioh Complete Edition PC and Nioh 2 Complete Edition PC remain unregistered,
read-only research profiles. Native encryption is implemented, and unchanged
snapshots retain their original header keys, account binding, body bytes and
integrity flags. Gameplay writes require native integrity consumers and field
dependencies that the public decryptors do not implement.

## Native qualification

| Profile | Independently observed layout | Evidence boundary |
| --- | --- | --- |
| Nioh Complete Edition PC | `NIOHUSR\0`; revision `17091200`; `0x148`-byte header; `0x1F2C50`-byte body; full USER size `0x1F2D98`; matching body revision at `0x150` | Freely shared original PC USER copies retain all seven published integrity flags. Encrypted/decrypted/encrypted bytes match exactly. No edited game-load result. |
| Nioh 2 Complete Edition PC | `NIOHUSR\0`; revision `21030200`; `0x148`-byte header; full USER size `0x296F28`; matching body revision at `0x150` | Complete public upstream decrypted reference retains all four published integrity flags. This is an editor reference, separate from an independently captured gameplay action pair. |
| Nioh 1/2 PC SYSTEM | `NIOHSYS\0`; explicit title revisions; different USER/SYSTEM sizes | Katana upstream cipher vectors include SYSTEM files. SYSTEM vectors do not qualify gameplay USER integrity. |

The [Nioh PC inspector](../src/koei_editor/research/nioh/nioh_native.py)
requires the full USER size, exact title and both revision markers; rejects
SYSTEM, Nioh 2 and console input; freezes mutable input; and exposes no writable
fields. It preserves the opaque final 16 bytes. Those bytes are not labelled as
a checksum. The existing
[Nioh 2 inspector](../src/koei_editor/research/nioh2/nioh2_parser.py) now rejects
forged mutable snapshots and validates the exact bounded bytes passed to restore,
including a backup replaced together with its matching hash manifest.

## Public checksum leads checked

| Source | Findings |
| --- | --- |
| [pawREP Nioh decryptor](https://github.com/pawREP/Nioh-Savedata-Decryption-Tool/tree/1127f936ccc35b0f93f16b6d94e0e860f329942f), MIT | Implements native encryption; `SaveEditor.cpp` clears seven USER flags. Does not recover the native checks. Default decryption also clears header subkeys; our codec preserves original keys. |
| [alfizari Nioh 2 editor](https://github.com/alfizari/Nioh-2-Save-Editor/tree/7de1e3d5b20b7f94b055eb228a5e3b0746ea1452), Apache-2.0 | Supplies the complete retained-flag reference and published scalar/record offsets. Its editor clears four flags and invokes external cipher binaries. Neither operation qualifies integrity. No supplied binary was executed. |
| [sourcier editor](https://github.com/sourcier/nioh-save-editor/tree/653412187484358f8a4796a89023cccd1e67a282) | Its Nioh 2 constants still enumerate flag bytes to clear; the implemented checksum module is for Nioh 3. Nioh 2 currency writes use four bytes, unlike alfizari's eight-byte inspection widths, so width and high-word semantics need controlled proof. |
| [HTOS Nioh 2 implementation](https://github.com/hzhreal/HTOS/blob/a676bc22f3376852890b9c73995411f368459266/data/crypto/nioh2_crypt.py) | The README's version-01.27 "checksum fix" is flag clearing in `encrypt_file`, not checksum recovery. It is a PS4 source lead, not a PC schema. |
| [bucanero Nioh 2 decryptor](https://github.com/bucanero/save-decrypters/tree/b2e98ed254e6afc57697bf19fddf84296863dad1/nioh2-decrypter) | Explicit PS4 bypass flags; no native checksum routine. PS4 offsets are kept separate from PC envelope offsets. |
| [Katana resigner](https://github.com/mi5hmash/KatanaSaveDataResigner/tree/4c90a2b388438cb27a9752e6eab7333257de215f), MIT | `NiohFile` implements cipher/account operations and `Nioh2File` inherits them. Neither validates or recalculates gameplay integrity. |
| [Ambushfall save-transfer wrapper](https://github.com/Ambushfall/nioh-saver/tree/c4f779288e3329a9e90dca74b8365aeb9a3d6273) | Despite the README's "recalculates integrity" claim, both implementations invoke pawREP with `-cs` (Python explicitly calls it "no checksum"). No independent native integrity routine exists. |
| [John's public Nioh 2 editor](https://johnssaveeditors.com/games/nioh-2/) | Explicitly clears integrity flags on the first edit and states that edited in-game loading was not tested. It is not an independent integrity solution. |

The complete available histories of pawREP, alfizari and sourcier were also
examined. pawREP adds the seven-flag bypass in `1127f93`; alfizari's initial
editor already contains the four-flag bypass. sourcier's initial writer has no
native Nioh 2 checksum calculation. No earlier native integrity implementation
was recovered from these histories.

Independent Nioh PC files were obtained from a
[public Steam save-sharing discussion](https://steamcommunity.com/app/485510/discussions/0/1639792569834913906/).
Archives, native files, decrypted files, source copies and local analysis remain
outside the checkout. Private filenames, hashes and owner context are not
published or bundled.

## Analytical investigation

Both USER layouts contain two nontrivial dwords at `0x148` and `0x14C`, followed
by the body revision at `0x150`. This observation does not establish those
dwords as a seed/checksum pair. Native Nioh PC USER tails contain nonzero opaque
data; the public Nioh 2 reference has a zero tail. Their exact roles remain
unmapped.

Local candidate sweeps examined seeded CRC32/Adler32, direct MD5/SHA1/SHA256,
32/64-bit additive folds and the independently known Nioh 3 signed-qword block
fold. Block sizes `0x80` through `0x1000`, several native body-prefix starts,
candidate prefix/footer seed words and final-tail inclusion/exclusion were
tested. No matching integrity rule was established. The Nioh 3 algorithm is
therefore not transplanted into Nioh 1/2.

The seven Nioh and four Nioh 2 bypass flags occupy multiple separated spans.
This calls for tracing their native consumers and protected serialized fields;
it does not justify treating any single whole-body candidate as sufficient.
Local analysis around these spans found mixed booleans, scalars and opaque
words, but no proven serialized checksum boundaries or dependency transitions.

### Static runtime fragments

Public text tables from the
[Nioh 2 thread](https://fearlessrevolution.com/viewtopic.php?t=15040)
(attachments `58029`, dated 2024-03-17, and `49689`, dated 2023-04-06) and the
[Nioh thread](https://fearlessrevolution.com/viewtopic.php?t=5355)
(attachments `7592`, `35487`, `35529`) were downloaded and parsed as XML/text
only. The
[FRAMED Nioh 2 camera table](https://github.com/framedsc/Sitesource/blob/0264b26cd68db94a1f72d2889cbcea33643ae611/markdown/CheatTables/nioh2.ct)
and the public University of La Laguna
[process-analysis thesis](https://riull.ull.es/xmlui/handle/915/33676)
were also checked. None was executed or copied into the application.

The Nioh 2 tables contain useful static-analysis targets, with addresses tied
to the captured builds rather than portable save offsets:

| Captured native fragment | Proven observation and missing dependency |
| --- | --- |
| `A02ECE` / `DA5A29` | Reads Amrita as a qword at runtime structure `+7B778`, with Gold at `+7B780`. This supports an eight-byte runtime width, but does not prove every saved revision's representation or protected-field update rule. |
| `A02F00` / `A0987B` | Currency addition and proficiency update both call `A0F670`. Its body is absent; the call may be a shared utility and is not labelled a checksum routine. |
| `DA5A3A` | Currency-related reader calls `A1DD40`; the table does not include its full body or establish an integrity role. |
| `A207A0` | Level-cap logic reads runtime flags `+7B879`, `+7B7EB`, `+7B7EA`. These are distinct from the four published bypass flags and demonstrate progression-dependent checks, not a recovered checksum. |
| `C37DF6` / `C2AAFB` | Equipment-effect validation and familiarity updates have distinct processing; familiarity calls `C4CE70`, whose full body is absent. Derived effect values must not be treated as independently stored ownership or effect identity. |

The recent
[Nioh 2 item sanity-check mod](https://www.nexusmods.com/nioh2/mods/764)
credits the same table and deliberately skips validation; its public description
does not supply a native save checksum. The thesis covers runtime Gold/stat
mutation rather than native save integrity. These leads narrow where lawful
static analysis should continue, but do not expose the complete routines that
consume the seven/four bypass flags. A generic whole-file CRC cannot substitute
for those consumers or prove their field dependencies.

## Mechanic coverage and precise remaining inputs

The [official Nioh 2 PC manual](https://www.gamecity.ne.jp/manual/t2wNiSht/steam/usa/4000.html)
distinguishes carried Amrita from the Amrita gauge used for Yokai Shift, and
distinguishes Guardian Spirit acquisition, Soul Core purification and attunement.
Amrita carried at death can reside at the grave; a second death loses it together
with unpurified cores. A resource writer must therefore prove its current,
grave-held and lifetime fields independently. Spirit ownership must not imply
equipped spirit, attuned core, purified core or story completion. Main and sub
mission completion also have different story consequences.

[Nioh 2 proficiency guidance](https://www.powerpyx.com/nioh-2-how-to-get-onmyo-magic-ninja-proficiency-skill-points/)
records separate category proficiency, skill points, learned skills, prepared
jutsu and story-gated Dojo requirements. Acquiring a Locks item, consuming it,
earning proficiency and spending a point are distinct actions. Future action
pairs must include these distinctions rather than adjusting a proficiency scalar
and granting all associated rewards. Nioh 1's skill system requires its own
observations; Nioh 2 dependencies are not transferred into that edition.

[Nioh blacksmith guidance](https://twinfinite.net/guides/nioh-blacksmith-how-to-use/2/)
describes equipment sale for gold, forging access through smithing texts and
familiarity reset during Soul Matching. Nioh 2's
[equipment/Soul Matching guidance](https://gamefaqs.gamespot.com/ps4/241160-nioh-2/faqs/78230/blacksmith)
describes familiarity and effect inheritance requirements. These are gameplay
dependency leads, not binary-format evidence: item ownership, forge recipes,
material consumption, equipment level, familiarity and inherited effects need
separate record and transition proof. Refashioning appearance is also separate
from replacing an owned or equipped item's identity.

| Mechanic | Nioh Complete Edition PC | Nioh 2 Complete Edition PC |
| --- | --- | --- |
| Gold / Amrita, current versus lifetime | No qualified writable map | Published offsets inspected only; four/eight-byte disagreement and high-word semantics unresolved |
| Level / EXP / attributes | No qualified writable map | Published level/attribute offsets inspected; level mirror and sum-of-attributes dependencies require controlled pairs |
| Weapon / Onmyo / Ninjutsu proficiency and skill points | Unmapped | Published proficiency offsets inspected; threshold, earned/spent points and learned skills remain separate |
| Equipment / inventory / refashion | No qualified record identity or writer | Published weapon/item/scroll pool bases and strides are leads; identity, occupancy, equipped references and quantity rules unqualified |
| Forging / tempering / remodeling / familiarity | Unmapped | Public equipment fields are leads; costs, effect compatibility and derived tiers need proof |
| Guardian spirits / soul cores / companions | Unmapped | Ownership, attunement/equipped references and reward state unmapped |
| Appearance / customization | Unmapped | Unmapped |
| Missions / story / difficulties / Abyss or Underworld | Unmapped; separate from resources | Unmapped; separate from resources and rewards |

The next decisive input is each edition's native checksum/field-integrity
routine, obtained through lawful static analysis of the exact PC game build or
a public source-equivalent reconstruction. Tracing must identify every native
flag consumer, the covered bytes, stored result, seed/nonces and update order.
Retained-flag native files are already available; another unlabelled save alone
will not resolve these routines.

Controlled in-game before/after pairs with one action, displayed values and an
unchanged control are also required for currency high words, level mirrors,
proficiency/skill rewards, occupied equipment records, equipped references,
familiarity thresholds and forging costs. No password, account reassignment or
integrity bypass is needed. Existing unusual values must remain preserved.

## Tests and evidence

[Nioh inspection tests](../tests/test_nioh_native.py) cover size, title/revision,
immutable snapshots, flag preservation, malformed inputs, unsupported writes,
live/resolved-alias paths and an optional complete native cipher roundtrip via
`NIOH_SAVE_COPY`.
[Nioh 2 tests](../tests/test_nioh2_format.py) additionally exercise the exact-byte
restore race regression, source replacement during backup and existing
backup/source safety. With `NIOH2_SAVE_COPY`, the complete external retained-flag
reference also passes unchanged backup/copy/restore byte agreement. This remains
an upstream editor reference with unrecorded modification history, not an
independently captured controlled gameplay action.

Procedural tests are deliberately unqualified for body integrity. Complete
native no-edit cipher agreement is stronger than those generators but remains
separate from edited in-game loading and re-saving. Neither title claims native
gameplay editing or actual game-load validation.
