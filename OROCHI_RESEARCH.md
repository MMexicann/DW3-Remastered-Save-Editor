# Warriors Orochi native PC coverage

Reviewed against the attached executables, public source facts, mechanics
references and a privately held public Steam save. Executables were inspected
and their SteamStub code section decoded statically; they were never executed.
No executable, decoded game image, player save or account context belongs in
this repository or its packages. Implementations are independently written;
no upstream project was copied into the application.

## Warriors Orochi 3 Ultimate Definitive Edition

`wo3u_parser.py` / `wo3u_editor.py` implement the Steam Windows packed layout.
The inspected executable identifies Steam app 1879330 and product version
1.0.0.1. Accepted files have exactly `0x2119CA` bytes and begin with the
little-endian marker `0x140318F1`. The native root serializer visits 150 officer
records, 145 groups of 16 weapon records, additional stage/team sections and an
opaque `0xA0000` section. The final five officer records are internal records;
they are inspected but have no writable fields.

The reached native save path serializes little-endian values then passes that
buffer directly to `WriteFile`; loading reads the same bytes and runs the
packed-field serializers. No save-owner binding, external crypto DLL, save cipher
or aggregate payload-checksum operation appears in that path. The root marker
and complete officer/weapon layout markers are qualified before writing. This
is structural qualification, not a claim that arbitrary corruption of every
unknown gameplay byte can be detected. Unknown data and every marker are
preserved rather than repaired or normalized.

Officer marker low words are `0x6DA8`, weapon marker low words `0x6228` in this
qualified revision; upper words must agree but are preserved because ASLR changes
them. These are serialized low DWORDs of object/vtable addresses. They are **not
checksums**, and a particular player's entire marker value is not a universal
constant. Other executable revisions with changed table offsets are rejected.

Static evidence locations in the inspected image:

| Routine | Observed behavior |
| --- | --- |
| `0x1402DFA9B`, `0x1402DFAC4` | Native allocation and save length `0x2119CA` |
| `0x1402487A0`, `0x1402488F0` | Clear output buffer, serialize packed native sections |
| `0x1402465B0` | Serialize/check title and revision marker `0x140318F1` |
| `0x140274F90`, `0x140275110` | Direct native `WriteFile` / `ReadFile` |
| `0x140258CA0` | Packed officer serializer, not a raw runtime memory copy |
| `0x14026C8C0` | Packed weapon serializer with eight ID bytes and eight ranks |
| `0x14026CC90` | Weapon descriptor lookup and special IDs 1250..1394 |

The independent public native sample was acquired from an annotated
[Steam save-sharing discussion](https://steamcommunity.com/app/1879330/discussions/0/592904528464062941/).
It has the exact length/title/layout and SHA-256
`e9a6ec40c7c1807dcb301d318d520aced64d920ac0a1452821ea42091f99c0a9`.
The author describes maximal stats except deliberately low Musou, low bonds,
minimal weapon attributes and plentiful crafting materials. All 145 playable
records show health/attack/defense 999, Musou 200 and speed 200, independently
corroborating the public field labels but not establishing natural caps.
The source deliberately contains cheat values, including speed 200; the editor
uses the guide's natural speed maximum 180 and Max preserves existing 200. The five extra internal records differ.
There are 1,109 occupied native weapon records and 445 instances of attribute
ID 31 at rank 1; the author's description of Verity on Samurai-type weapons
corroborates that ID. The 58 orb and 295 crafting-resource bytes match the
published spans, without adopting console container offsets or endianness by
assumption.

Additional sources:

- [Apollo NPEB02052 patches](https://github.com/bucanero/apollo-patches/blob/main/PS3/NPEB02052.savepatch):
  public labels/strides used as research leads, checked against the native
  packed serializers and sample. Patch titles and cheat values alone are not
  natural-cap evidence. Console files themselves are not accepted.
- [Steam PC mechanics guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2851197510):
  promotions reset level, expand item slots, award upgrade stones and have
  dependent bonuses; normal stats reach 999 except speed, whose natural maximum is 180. The guide also
  distinguishes orb fusion, bond consumption and story/Gauntlet unlock routes.
- [Hundun unlock guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2839992420):
  character unlock requires a specific Gauntlet completion and subsequent
  mode transition; unlocking a bit without those dependencies is not exposed.
- [PythWare/Warriors-Orochi-2-Editors](https://github.com/PythWare/Warriors-Orochi-2-Editors):
  stage/unit asset editors, not a compatible disk-save editor. No code reused.
- [ashimpure/WO3UDEXL](https://github.com/ashimpure/WO3UDEXL) and
  [WO3U Equipment Mods](https://github.com/ryuuseispt-ui/WO3U-Equipment-Mods):
  gameplay/modding leads; no native disk mapping or implementation was copied.

### Writable fields and limits

Offsets are native PC file offsets, little endian. Fields always come from the
immutable original snapshot; pending edits cannot manufacture records.

| Field | Native offset/stride | Behavior |
| --- | --- | --- |
| Unallocated growth points | `0x1378`, u32 | Individual edits through 9,999,999 |
| Precious stones / gems | `0x137C`, u32 | Individual edits through 999,999 |
| Health, Musou, attack, defense, speed | `0xECF2 + officer*0x2B0 + {0,2,4,6,8}`, u16, 145 records | Stat edits, bulk Max; 999 except speed 180 |
| Attribute orbs | `0xE944`, 58 u8 values | Individual balances through 99 |
| Crafting materials | Seven spans defined in parser, 295 u8 values | Individual balances through 99 |
| Existing weapon attribute slots | `0xC8012 + weapon*0x1C`, u8, 145*16 records | 0..8; decreasing cannot hide attributes; increasing cannot activate dormant IDs |
| Existing attribute ranks | `0xC801C + weapon*0x1C + attr_slot`, u8 | Proven standard IDs 5..11 use 1..10; Verity ID31 is binary rank1 |

Growth-point, gem, orb and material edit bounds come from public patch limits;
their natural caps have not yet been recovered from native gameplay clamps.
These fields are excluded from **all** bulk Max actions. Higher existing balances
can remain unchanged. Stat/rank/slot bulk actions also preserve higher existing
values. No ID is assigned to an empty weapon or empty attribute slot; zero-rank
and unknown attributes, unknown weapons and unsupported slot-count layouts
remain inspection-only. Normal descriptor IDs end before special range
1250..1394; IDs outside the qualified descriptor range are preserved read only.

The shared GUI provides search, grouped field controls, existing-weapon inspection,
separate progression and resource tables, staged batch Undo, Review Changes,
automatic backups and atomic Save As to a new `.bin` destination. Restore qualifies
the exact bounded bytes written, including the backup manifest/hash. Common
path protections and source-change detection remain in force.

### Coverage checklist

| Important system | Implemented or precise remaining blocker |
| --- | --- |
| Currency and stock EXP/growth points | Individual balance editing; native natural clamps still needed for resource Max |
| 145 playable officers' five stored stats | Writable, tested; higher values preserved; five internal slots protected |
| Character identity/names | Record indices and progression inspected; native roster-ID/name association not proved, so names are not guessed |
| Level and EXP | Read-only stored level/EXP; controlled level-up and promotion pairs needed to prove recalculation, rewards and level reset |
| Promotions and upgrade stones | Read-only promotion count; promotion rewards, allocated stones, remaining stones and item-slot dependencies need controlled before/after saves |
| Proficiency and abilities | Public source separates multiple bytes/ranks; natural progression/skill prerequisites and packed semantics need controlled pairs |
| Weapon ownership/types | Existing IDs inspected; no cloning, empty-record manufacture or guessed weapon names |
| Weapon attribute slots | Safe existing-record expansion/reduction; reduction cannot hide owned attributes; expansion cannot activate dormant IDs |
| Weapon attributes, elements and fusion | Existing proven ranks writable; unknown IDs and zero ranks preserved. Attribute acquisition/swap and full 58-name catalogue need native ID tables and fusion dependency pairs |
| Weapon compatibility and reinforcement | Raw records preserved; compatibility is packed into a u32 and is not the unaligned console patch's apparent u16. Per-grade caps/derived attack need independent mapping |
| Attribute-orb inventory | 58 balances editable; ID-to-name catalogue and natural clamps pending |
| Crafting inventory/recipes | 295 balances editable; materials' names, receipt/new flags, recipe unlocks and natural clamps pending |
| Equipped items and item enhancement | Preserved; normal enhancement, special ownership and equipped references must be distinguished with controlled equip/upgrade pairs |
| Bonds and companions | Low-bond genuine fixture available; pair symmetry, support thresholds, consumption and maximum semantics not yet mapped |
| Mounts | Existing item/mount relationship and ownership IDs not proved; require equip/acquisition pairs |
| Costumes and color customization | Annotated changed colors present; exact character/color-channel association and costume prerequisites not proved |
| Story, stages and campaigns | Preserved and separate from resources/stats; chapter endings, Redux/side-story unlocks and rewards need controlled completion pairs |
| Gauntlet/exploration, keystones and allies | Public patches indicate regions; four keystone types, summon ownership, progression/rewards and ally consumption need native mappings and controlled pairs |
| Duel cards/collections | Preserved; card ownership/new flags and gallery rewards/dependencies not proved |
| Gallery, music and movies | No independent PC packed-field map or controlled unlock pairs acquired |
| Revision variations | Exact 1.0.0.1-compatible packed layout qualifies; differently sized/marked/modded layouts rejected |
| Edited game loading | Not performed: no Windows game installation/load/re-save available in cloud |

### Validation

With `WO3U_SAVE_COPY` pointing to a reviewed copied native save outside the
checkout:

```text
python -m unittest tests.test_wo3u_format tests.test_wo3u_review tests.test_orochiz_candidate_codec -v
python -m unittest tests.test_wo3u_gui -v
```

The first command passed 27 tests with the private fixture present, including the
native no-op roundtrip and surgical native stat edit. Without the private fixture,
one native test skips honestly. The second passed two GUI tests under Xvfb:
search, grouped controls, edit validation, review, Undo, backup, Save As, inspector
and theme switching. Fixtures generated by `procedural_raw()` are explicitly
synthetic. A native complete bulk action preserved all five internal records;
1,399 changed bytes belonged only to declared Musou or existing weapon-slot
fields. This is file-level validation, not an edited game-load claim.

## Musou / Warriors Orochi Z

The inspected PC executable identifies product version 1.0.0.0. Its native save
path is `save.dat`; the native load routine requires exactly `0x25F48` bytes and
revision u16 at `0x4` equals 2. The writer copies two plaintext sections directly
then writes the resulting buffer. No encryption or external key is present in
that reached path.

The checksum is the u32 byte sum of bytes before `0x25F24`. Its 20-byte native
integrity record is that u32 followed by 16 zero bytes. Native checksum calculation
zeros that whole record and requests `file_length - 20 = 0x25F34` bytes; because
the integrity record starts earlier, this is equivalent to summing bytes strictly
before `0x25F24`. The final 16 bytes are opaque and excluded from the checksum;
they must not be zeroed, silently repaired or called part of the checksum.

| Routine | Static evidence |
| --- | --- |
| `0x5AC2E0`, `0x5ABE10` | Serialize/load raw sections `0x5EE8` and `0x20028` |
| `0x5AC214`, `0x5AC854` | Native read/write length `0x25F48` |
| `0x5AB6B0` | Revision u16 equals 2 before checksum validation |
| `0x5AB630`, `0x5AB510`, `0x5E8990` | Zero integrity record, compute byte sum, compare all 20 bytes |
| `0x474670`, `0x474750` onward | `0xDC` record stride and five u16 getter/setter fields |
| `0x474FD0` | Separate u16 progression-like field divided by 1000 |
| `0x474680`, `0x474840` | Existing weapon records with `0x18` stride |

`orochiz_candidate_codec.py` validates these native envelope rules and exposes
only an unchanged roundtrip. It is source-only and unregistered: revision, size
and a generic byte sum alone do not prove a player's title identity. No genuine
native Z save was acquired. GitHub searches found a gamepad fix and asset editors
rather than a disk editor or usable native fixture. Public save-site searches
remained blocked or did not provide a verifiable file; those access failures
are not decryption failures.

| System | Precise blocker |
| --- | --- |
| Container/plaintext/integrity | Native static mapping implemented; independently copied PC save still required for qualification |
| Roster/unlocks, five stats, level/EXP/proficiency | Candidate record strides/setters visible; title qualification, name association, exact progression semantics and natural caps need labelled PC fixtures |
| Abilities/skills | Packed bytes/flags not semantically proved; acquisition/upgrade pairs required |
| Weapons/fusion/elements | Native record stride visible; weapon IDs, rank/cap limits, empty records, fusion costs and dependencies not proved |
| Items/mounts | Ownership/equipment identities and normal caps not proved |
| Story/Dream/Survival stages, clear records | Raw second section includes saved state; progress/unlock/reward relationships not mapped |
| Costumes/gallery/music/movies | No independently qualified PC IDs/flags or controlled unlock pairs |
| Edited game loading | No gameplay writer or native edited-load claim; four procedural envelope tests passed |

A native copied Z file plus an unchanged control and one-action before/after
samples can extend this candidate. No matching DLL or owner secret is currently
indicated by the reached native save routines.
