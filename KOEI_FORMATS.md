# Verified Windows PC layouts and research scope

The application edits **native Windows PC saves only**. Console saves are not
accepted by these PC backends. The separate DW4 XL PS2 adapter has its own
container and platform checks. Console references can help
identify a field, but a console offset is never sufficient to enable a PC edit.
The read-only `support_catalog.json` covers PC editions in the Dynasty Warriors,
Pirate Warriors, Berserk, Samurai Warriors, Warriors Orochi and related series.
Console-only releases, including Pirate Warriors 1 and 2, are excluded.

## What "file editing verified" means

New games enter `game_registry.GAMES` only after an explicit adapter can identify
and validate an actual PC save, decode it, change evidenced gameplay fields,
regenerate native integrity data and reparse the result. Unchanged saves must
round-trip byte for byte and changed plaintext must be limited to declared
fields. Procedural regressions cover rejection and preservation behavior.

**This is not an in-game load test.** The cloud cannot run these Windows games.
DW8 XL and Pirate Warriors 3 explicitly display that in-game checks are pending.
Their editors support the layouts described here, not every platform, patch,
mod, region or DLC combination. Origins remains research copy tools, accessed
in contributor documentation rather than the editor library.

## Dynasty Warriors 8: Xtreme Legends Complete Edition

PC filename: `save.dat`. Exact accepted size: `0xB7F49` (753,481) bytes.
The first four bytes contain a little-endian 16-bit checksum and 16-bit seed.
The following `0xB7F44` bytes use a DWORD XOR stream: advance the state three
times per word with multiplier `0x5B1A7851`, increment `0xCE4E`, modulo `2^32`.
The decrypted intermediate bytes must sum as little-endian words to the header
checksum modulo `2^16`. A byte XOR layer starts with state `0x13100200`, uses
multiplier `0x41C64E6D`, increment `0x3039`, and takes bits 16–23 per byte.
The final file byte, XOR the low byte of the first mixed outer state, must equal
the sum of plaintext bytes modulo 256.

Accepted five-byte plaintext signatures are `F0 02 10 13 09` (the published
converter's canonical format) and `F0 27 02 19 09` (its included PC sample).
No header repair or guessed signature is performed. The original outer seed and
every unedited plaintext byte are preserved.

All offsets below refer to plaintext after removing the four-byte outer header.
Integers are little endian.

| Field | Offset | Width | Published editing limit |
| --- | --- | --- | --- |
| Gold | `0x105` | 4 | 9,999,999 |
| Gems | `0x1D43` | 2 | 9,999 |
| Facility materials | `0x1F6D1` | 2 | 9,999 |
| Weapon materials | `0x1F6D3` | 2 | 9,999 |
| Officer attack | `0x7FD5 + slot * 0x48` | 2 | 1,500 |
| Officer defense | `0x7FD7 + slot * 0x48` | 2 | 1,500 |
| Officer health | `0x7FD9 + slot * 0x48` | 2 | 1,000 |

There are 82 numbered officer records. Names and availability flags have not
been independently mapped, so slots are not assigned guessed names. These are
published save-patch limits, not promises of naturally attainable values.
The gem limit is now 9,999, independently corroborated by two Steam guides.
The former 65,535 patch value was a cheat bound. Higher existing values remain
untouched unless the user explicitly edits that field.

Level/XP, leadership and equipped weapon references are inspected read only.
Existing supported weapon attribute ranks can be edited. Mounts, story and unlock editing remain unavailable. The published experience patch has ambiguous semantics, so it
is not exposed merely because an offset exists.

Sources:

- [koko-tsuu/dw8xl_save_converter](https://github.com/koko-tsuu/dw8xl_save_converter),
  inspected commit `8ca795108a4f4f0bee91c55d3efce0c6da78515f`: PC fixture,
  independently checked cipher and explicit PC/PS3/PS4/Vita layout conversion.
- Public PC fixture `test_files/pc.dat`, SHA-256
  `f0221e67e7d59a496a9045a4c0d6b3a5a5eaf784b65b093b1d2c6c427d3ac5f0`.
  Gold 5,273,829; gems 7,061; materials 367/801; officer stats fit the published
  record structure. Both native checksums pass. Independent decoding of original
  and edited saves matches the reference converter's plaintext.
- [Apollo patches: NPUB31449](https://github.com/bucanero/apollo-patches/blob/main/PS3/NPUB31449.savepatch),
  inspected repository commit `99f4e10e415e1a1590c301b105667530710854fa`.
  Console field maps are applicable here because the converter establishes the
  shared payload and those fields were checked on the PC fixture.
- [DW8 XL save decrypter](https://github.com/bucanero/ps3-save-decrypters/tree/master/dw8xl-decrypter)
  independently corroborates the inner cipher and checksum.

## One Piece: Pirate Warriors 3

**The primary sample is a Windows PC save**, not a console export.
[Ceraph1216/pirateWarriors3Save](https://github.com/Ceraph1216/pirateWarriors3Save),
commit `a4addb6b4483c9e51afa8aabb3fa5cea86d60483`, supplies `OP3WIN0000.dat`.
Its README places it in `Documents\One Piece Pirate Warriors 3\SAVEDATA`.
The file is 1,268,996 (`0x135D04`) bytes, SHA-256
`1905c7e95c46d3fa6c2a593d849626c6e6a88b81db2450eed238c5e63ef06913`.

The first four bytes have the same word checksum/seed structure and outer
DWORD stream described above. The full remaining payload is encrypted; there
is no DW8 byte layer or single-byte trailer. The checksum validates on the
genuine PC sample. Decoding reveals `ONE PIECE: PIRATE WARRIORS 3` at payload
offset zero, plus readable Windows save-slot metadata. The editor also checks
the observed native layout markers at `0x500` and `0x518`, and rejects unknown
sizes, titles and layouts instead of adapting offsets heuristically.

The published PS3 mapping uses big-endian values. The observed PC fields are
little endian and lie `0x560` later. This translation was checked against all
47 PC character records and surrounding currency/medal regions, not assumed from
the title. A separate public PS3 save from
[Apollo saves](https://github.com/bucanero/apollo-saves/tree/main/PS3/NPEB02211),
commit `c6fa97f2f4ef1b3469f0421c727997108821e188`, was decrypted locally through
its native container to corroborate the published field structure. That console
container decoder and save are not part of this application.

PC payload offsets:

| Field | Offset | Width | Published editing limit |
| --- | --- | --- | --- |
| Character health | `0x654 + slot * 0x1F0` | 2 | 10,000 |
| Character attack | `0x656 + slot * 0x1F0` | 2 | 1,000 |
| Character defense | `0x658 + slot * 0x1F0` | 2 | 1,000 |
| Special bars | `0x65A + slot * 0x1F0` | 1 | 4 |
| Skill slots | `0x65C + slot * 0x1F0` | 1 | 6 |

The PC sample's observed Beli value is 999,999,999 at `0xC5D4`, with 1,000,000,000
at the adjacent `0xC5D8`. The published money patch changes **both** fields and
their relationship is unresolved. Currency editing is therefore disabled;
changing `0xC5D4` alone cannot yet be claimed to produce usable in-game money.
Controlled PC before/after Beli samples or an independently verified game-load
test are needed to establish the correct update. Currency inspection is read only.

Its first character has health 5,780, attack
571, defense 578, four special bars and six skill slots. Other characters have
plausible progression values at the same stride. The editor labels numbered
slots and preserves experience and level bytes. Stats can reset on level-up,
as documented by the published patches. The adjacent Beli-related value at
`0xC5D8` has not been assigned an unverified meaning and is not changed.

Reference field map:
[Apollo NPEB02211 patches](https://github.com/bucanero/apollo-patches/blob/main/PS3/NPEB02211.savepatch),
same inspected patches commit as above. Medal inventory semantics, experience
and level coupling, unlocks and story flags require further controlled PC
samples before editing can be offered.

A second low-progression native PC sample from
[gamesaves/OPPW3](https://github.com/gamesaves/OPPW3/tree/39a79e77483b2683656abca0ee981f060ee01a7f)
passes the same size, title, revision and native integrity checks, SHA-256
`6a16ac7557980adb1db138c2c96966349e9a5d7b4ba1a26b09388e6b23c58832`.
Read-only level/XP inspection uses the separately evidenced fields described in
[GAME_MECHANICS.md](GAME_MECHANICS.md). The observed health curve is an inference
and is not used to rewrite progression or define a claimed natural maximum.

## Games that remain unavailable

Origins: see [ORIGINS_FORMAT.md](ORIGINS_FORMAT.md). The one genuine Steam sample
does not establish save encryption or a gameplay schema. Earlier asset-cipher
and word-cipher trials did not produce a verified Origins payload.

Berserk and the Band of the Hawk: a public Vita save was inspected, but no native
PC sample, PC field mapping or integrity algorithm was established. Pirate
Warriors 4 and DW9 have public PS4 samples, but those do not establish PC editing
support. DW8 Empires has published PC cipher notes but needs a corresponding
native PC sample. Samurai Warriors 4 has a public console checksum tool; it does
not establish the Windows DX layout. These titles remain outside `GAMES`.

For any candidate, needed samples are explicit copies of the **native PC file**,
labelled with game version, edition, language/region and DLC. Provide an unchanged
control pair and before/after pairs changing one in-game value: currency, skill
points, a stat, one equipment slot or one unlock. Include the displayed values.
Preserve originals privately. Encrypted formats may additionally need a verified
decoder; before/after ciphertext alone does not supply field offsets.

## DW4 Hyper candidate, native PC only

The supplied [DW4 Hyper editor](https://github.com/talkative-platano/dw4hyper-save-editor/tree/3638c8dc23d2607b862a1105bfc9806e69d9e871)
publishes raw `save.dat`, size `0x10FC0` (69,568), with no encryption. The
checksum is the sum of bytes before `0x10FA8`, stored there as a little-endian
32-bit value; the last 20 bytes are zero. Its author reports successful game
tests. **No genuine PC fixture was acquired or independently validated here.**
The supplied DW4 XL repository handles PS2 memory-card data. It has a dedicated
PS2 library entry and parser; see [platform boundaries](DW4_PLATFORM_FORMATS.md).

`dw4hyper_parser.py` independently implements these facts as a candidate:

| Published PC location | Interpretation | Candidate capability |
| --- | --- | --- |
| `0xB8 + officer * 24`, 42 records | Playable byte; four stat bytes; native roster index; equipped item IDs; character EXP u16 | Playable/stats/EXP writes; identity/equipment read only |
| `0x798 + officer * 2` | Weapon EXP u16; special Lv.10 value 36,001 | Individual writes and special-weapon Max |
| `0x7F6 + item`, 32 bytes | 255 locked; otherwise stored level plus one | Normal levels 1–20, orbs 1–4, rare ownership 0/1; UI 0 means locked |
| `0x508 + team * 96 + 94`, four teams | Bodyguard points u16 | Individual points; names read only |
| `0x9A` | 0 Easy, 1 Normal, 2 Hard | Individual difficulty; excluded from Max |

The parser rejects other sizes, checksum failures, nonzero trailers, unknown
difficulties and mismatched standard roster indices. Writes change only declared
field bytes and the checksum, retaining all custom, equipped-item, ranking and
suspended-battle data. No-op serialization preserves the original whole file.
Stat/EXP/point storage bounds do not prove natural caps and are excluded from
bulk Max. Hyper has no level-11 weapon.

The explicitly labelled published-format library entry and `--game dw4hyper --self-test`
exercise copies, backups, review, Undo and new-destination writes. They retain
`format_sample_verified: false`; availability does not claim independent fixture verification.
Provide an unchanged native PC copy and displayed values for real-file checks,
followed by controlled edited load/re-save testing before claiming support.

## Source-only codec candidates

`dw8e_candidate_codec.py` independently implements the published Empires word
envelope and additional SystemSave byte layer, preserving the original header
and seed. The caller explicitly classifies SystemSave/BattleSave; checksums do
not identify the title or platform. Native sizes, identity and gameplay fields
remain unverified. It has no file I/O or application adapter.

`p5s_codec.py` reproduces an attributed 32-byte PC encryption screenshot vector.
It can recover the equivalent stream class from known version bytes without
requiring an account ID. Read-only candidate inspection checks the published
size, ten slot/name spans and marker, while always reporting unverified checksum
and complete-save integrity. It has no gameplay writer or application adapter.
See [renewed research](PC_RESEARCH_RETRY.md) for evidence and copied-file needs.

## Privacy and licensing

Downloaded saves and external repositories remain outside the application source
tree and source manifest. No third-party implementation is copied or linked into
the executable. `koei_codec.py` and the adapters are independently written from
the factual format observations above. All saves, console keys, account metadata,
screenshots and copyrighted game assets are excluded from source/runtime packages.
