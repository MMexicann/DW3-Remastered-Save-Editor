# Renewed PC save research

Research date: 2026-10-09. All development remains local. This records actual
attempts and the evidence still required; it does not expand the verified editor
library through unverified cipher guesses. DW3 Remastered, DW8 XL Complete
Edition and Pirate Warriors 3 retain independent file evidence. The subsequent
user-authorized platform split adds both supplied DW4 editors as explicitly
labelled published-format implementations; their genuine-fixture checks remain pending. Their validation limits are recorded in [VALIDATION.md](VALIDATION.md).

## What the results mean

| Result | Meaning |
| --- | --- |
| Blocked download | A public PC save lead was located, but its host returned a network error before save bytes were obtained. No cipher was tested. |
| No fixture | No complete native PC save was acquired. A path, tutorial or memory trainer cannot substitute for one. |
| Candidate codec/map | Published arithmetic or serialized fields were independently implemented, but not validated against a complete genuine PC save. |
| Vector/procedural validation | A known byte sequence or constructed file passes a test. This does not establish native identity, full-file integrity, gameplay editing or in-game loading. |
| Failed cipher trial | A decoder was applied to actual identified save bytes and failed to establish a valid payload. None of the renewed candidates below reached this result. Origins' earlier unsuccessful trials are documented separately in [ORIGINS_FORMAT.md](ORIGINS_FORMAT.md). |

GitHub and some Steam searches returned HTTP 429. Google/Bing and several download
hosts returned proxy `Tunnel connection failed: 403 Forbidden`. These are bounded
search/download limitations, not proof that a decoder does not exist. Direct
Steam guides/discussions and GitHub source access supplied new evidence. No
downloaded executable, trainer or third-party script was executed.

## Dynasty Warriors candidates

**DW4 Hyper, native Windows:** the screenshot's
[PC editor](https://github.com/talkative-platano/dw4hyper-save-editor/tree/3638c8dc23d2607b862a1105bfc9806e69d9e871)
documents unencrypted `save.dat`, exactly 69,568 bytes (`0x10FC0`), with a
little-endian byte-sum checksum at `0x10FA8`. Its author reports lossless and
in-game tests. This project independently implements 331 candidate fields and
procedural validation, in the PC library as a published-format editor; no genuine PC sample
was acquired here. The map covers named officer stats/EXP/unlocks, weapon EXP,
32 items, equipped item references, four bodyguard teams and custom characters.
Hyper's weapon/item/difficulty rules differ from XL. The linked
[DW4 XL editor](https://github.com/talkative-platano/dw4xl-save-editor) targets
**PS2** and is excluded from the PC editor library. Shared inner layout is not PC
platform proof.

**DW6, original Windows:** newly located
[save reader and controlled reload research](https://github.com/cnopt/dynastywarriors6-reverse-engineering/tree/f2152f67b031091a0268154203d25fa9f65d2664)
reads plaintext `save.dat` directly: 41 officer records of 168 bytes, eight weapon
entries each, level/XP/kills, and playable flags. Author screenshots corroborate
the fields and report successful unlock edits. The reader consumes four bytes
after its named seek bases, so copying its base constants as field offsets would
be wrong. No complete save, native size/magic or checksum rule is provided. The
[second GUI reader](https://github.com/cnopt/dw6-imgui-save-parser/tree/d021b466d6c00aa9d0679ef8456d9292f3ad3b22)
has a placeholder Save button. Skills, weapon modifiers, horse stats and
officer identity dependencies were researched; identity changes can redirect
progression/inventories. This is a substantial disk-map lead, not failed decryption.

**DW7 XL Definitive Edition, Steam 968790:**
[PC save discussion](https://steamcommunity.com/app/968790/discussions/0/595160389826986033/)
provides a
[Google Drive save](https://drive.google.com/file/d/18kINc8mzT-gh3xOVrzoRdu3C7pULHPOP/view?usp=sharing)
and explicit Windows restore instructions. A normal download request was blocked
by proxy403. No bytes, native decoder or integrity rules were validated. PS3 DW7
and XL patch offsets are different-edition references, not PC Definitive mappings.

**DW8 Empires, Steam 322520:**
[PC discussion and import reports](https://steamcommunity.com/app/322520/discussions/0/1319961868335012150/?ctp=2)
link a
[Google Drive archive](https://drive.google.com/file/d/1-Tof-xv8uFr6_yE9nETWGuEa78ZSJFLg/view?usp=sharing);
its normal view request returned proxy403. Published
[candidate cipher snippets](https://github.com/bucanero/ps3-save-decrypters/tree/b2e98ed254e6afc57697bf19fddf84296863dad1/dw8xl-decrypter/samples)
describe a DWORD XOR envelope starting at `0x40C`, checksum/seed at `0x408/0x40A`,
and an additional SystemSave byte layer. The independent candidate preserves the
original header/seed and checks the arithmetic integrity layers; 19 procedural
tests pass. No complete Empires PC save, native identity, gameplay map or edited
output was validated. BattleSave behavior remains a hypothesis. The
[PC v1.004 runtime table](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/shinkansen_dynasty_warriors_8_empires_v1004_124.ct)
distinguishes gold/materials/troops, merit, equipment, virtue/friendship,
spendable/lifetime bonus points and custom-officer/scenario dependencies. Those
addresses are never treated as disk offsets. Original Tapatalk/Pastebin sources
also returned proxy403.

**DW9, Steam 730310:** a
[Steam PC save thread](https://steamcommunity.com/app/730310/discussions/0/691996723218915728/)
links [savegame.pro](https://savegame.pro/pc-dynasty-warriors-9-savegame/).
Users describe character/map unlocks without all officer stories completed. The
host request returned proxy403, so no archive was inspected. The
[PC gem guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1367429596)
maps runtime gem type and four bonus-type/value pairs, including duplicate
records and values wider than one byte; it warns of version changes. It provides
no disk decoder. Existing PS4 references remain unverified for PC.

**DW9 Empires, Steam 1341200:** no PC save or disk codec was acquired; discussion
searches returned 429. Retrieved
[game mechanics](https://steamcommunity.com/sharedfiles/filedetails/?id=2705195639),
[CAW hex/memory research](https://steamcommunity.com/sharedfiles/filedetails/?id=2732095060)
and [CAW import/export](https://steamcommunity.com/sharedfiles/filedetails/?id=3175407939).
The last tool explicitly targets Steam v1.0.1.1 (2024-03-07), exports process data
to `.caw`, then saves through the game. It is not a disk decryptor. Research
distinguishes six reputations, player titles versus NPC Way of Life, 35 artifact
rarity/element combinations, gem slots, four equipped Secret Plans, campaign
proficiency and child inheritance. Reported memory proficiency 0/500/1000 and
CAW screen resets are mapping leads, not validated save-writing rules. Base DW9
does not establish Empires support.

## Samurai, Orochi and other candidates

**Samurai Warriors 4-II, Steam 348470:**
[Steam save discussion](https://steamcommunity.com/app/348470/discussions/0/481115363862745012/)
links [Dropbox data](https://www.dropbox.com/s/hyi7x130xz7poov/SAVEDATA0000.dat?dl=0).
The ordinary download returned proxy403. Its uploaded name differs from the
documented native `save.dat`; contents/platform still need verification. The
[PC v1.003 runtime table](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/shinkansen_samurai_warriors_4-ii_v1003_583.ct)
separates weapon/mount rank and current/max level, eight attributes/ranks, five
strategy-tome resources, skills and battle versus stored stats. The
[rare-weapon guide](https://steamcommunity.com/sharedfiles/filedetails/?id=527072619)
documents difficulty/objective dependencies. Original SW4's PS3 checksum fixer
does not qualify 4-II PC. No PC disk decoder trial ran.

**Warriors Orochi 3 Ultimate Definitive Edition, Steam 1879330:** an annotated
[Steam PC save](https://steamcommunity.com/app/1879330/discussions/0/592904528464062941/)
links [WO3U.zip](https://www.mediafire.com/file/dmjmqlmszqc7njm/WO3U.zip/file).
MediaFire returned proxy403. Author notes on low bonds/Musou, weapon attributes
and costume colors would help verify decoded fields. The
[PC gameplay guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2851197510)
distinguishes promotions, level resets, upgrade stones/item slots, ranked versus
binary weapon attributes, crafting materials and bonds. Reported stat caps are
community gameplay evidence, not native serialization limits. Console Ultimate
samples and the PC refresh-rate fix supply no verified disk codec.

**Pirate Warriors 4, Steam 1089090:** a
[2024 PC save guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3154884222)
links [save_data.rar](https://www.mediafire.com/file/e04xcgg231p9oz0/save_data.rar/file).
Its corrected normal MediaFire request returned proxy403. No save bytes or PC
disk decoder were acquired. The author's completion/stat descriptions explicitly
depend on then-current DLC. The
[PC SDK](https://github.com/Glubus/oppw4-sdk/tree/ed00f9fa0dae4ac561106c9e0d93cd2bcc44be88)
and [data](https://github.com/Glubus/oppw4-data/tree/9b544c4c961db6985f5a5079c9b97aef24a1cb10)
separate Beli, medal IDs/counts/new flags, crew-point display/raw deltas and
unresolved soul commit data. These are runtime/asset references, not a save codec.

**Berserk and the Band of the Hawk, Steam 502280:** the
[PC save request](https://steamcommunity.com/app/502280/discussions/0/133257959065034708/)
has no download; no complete PC fixture or disk decoder was acquired. The
[PC trainer](https://github.com/iccugs/BERSERK_trainer/tree/afec9a6c7685b3b6c9bb7092762a686af9b99937)
edits a running process; its large write targets are not natural caps. The
[tutorial translation](https://github.com/ayozetr/berserk-band-of-the-hawk-es/tree/a10d3affa706dc9d4650f5f54e82bb90c251986c)
and [Eclipse guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1519761513)
distinguish character progression from accessory enhancement/skills/materials,
horse unlocks, per-character floors/desires and global rewards. No native cipher
trial ran, and Vita data does not establish PC support.

**Persona 5 Strikers, Steam 1382330:** the
[PC utility](https://github.com/zarroboogs/p5spc.saveutil/tree/2462a2043aba3bc551d2eb6b732a81d2374aa826)
declares account-seeded byte encryption, PC size `0x55DEA0` and ten slots. An
independent 32-byte known-answer test reproduces its public encrypted/decrypted
screenshot; procedural structural checks also pass. This validates a cipher
fragment, not a complete save or gameplay editing. Incoming checksum behavior
and trailer rewriting still require real-file validation. No gameplay writer
or verified money/Bond/Persona/equipment fields were implemented. The independent stream-class recovery does not require or return an account ID.
No account context is included in reports or packaged artifacts.

## Copied files and controlled pairs still needed

Paths are corroborated by the
[Ludusavi manifest](https://github.com/mtkennerly/ludusavi-manifest/blob/f956ad520f4bea18097ec21af6418bcc37a3bb9d/data/manifest.yaml)
at commit `f956ad520f4bea18097ec21af6418bcc37a3bb9d`. Paths prove location, not
decoding. Where a basename was not established, it is deliberately left unknown.

| PC edition | Copy needed | Useful one-change pairs |
| --- | --- | --- |
| DW4 Hyper | `Documents/KOEI/Dynasty Warriors 4 Hyper/Savedata/save.dat`, exactly 69,568 bytes | Officer stat/EXP; one item acquire/equip; weapon EXP; bodyguard points; custom character |
| DW6 | `Documents/KOEI/Dynasty Warriors 6/Savedata/save.dat` | Officer unlock/level/XP; weapon modifier; horse stat; unchanged control |
| DW7 Definitive | `Documents/KoeiTecmo/Dynasty Warriors 7 DX/Savedata/save.dat` | Money; skill purchase; officer stat; weapon/equipment; one story clear |
| DW8 Empires | `SystemSave*.dat` and native campaign `BattleSave*.dat` from `Documents/KoeiTecmo/Dynasty Warriors 8 Empires/Savedata`; preserve actual names | Gold/materials/troops; spendable/lifetime bonus points; merit; weapon; Way of Life unlock |
| DW9 | Gameplay files from `Documents/KoeiTecmo/Dynasty Warriors 9 for Steam`; basename unverified | Purchase; stat allocation; gem creation/equip; weapon upgrade; officer story clear |
| DW9 Empires | Global/system data plus a campaign slot from `Documents/KoeiTecmo/Dynasty Warriors 9 Empires`; basenames unverified | Monthly/resource change; reputation/title; card; artifact/gem; CAW; proficiency/inheritance |
| SW4-II | `Documents/KoeiTecmo/SAMURAI WARRIORS 4-II/Savedata/save.dat` | Level/XP; tome purchase; skill acquire/equip; weapon/mount; rare weapon objective |
| WO3 Definitive | `Documents/KoeiTecmo/WARRIORS OROCHI 3 Ultimate/SAVEDATA/SAVEDATA.BIN` | Growth points; promotion; item slots; weapon attributes; bond; crafting |
| PW4 | Complete Steam folder under `%LOCALAPPDATA%/BANDAI NAMCO Entertainment/One Piece Pirate Warriors 4/Saved/SaveGames/<account>`; basenames unverified | One stat-map node; skill; Beli; medal/coin; soul purchase |
| Berserk | Complete `Documents/KoeiTecmo/BERSERK and the Band of the Hawk/SAVEDATA` folder; basename unverified | Level; money; accessory enhancement/amalgamation; material; horse acquire/equip; Eclipse checkpoint/desire |
| P5S | `%APPDATA%/SEGA/Steam/P5S/<account>/SAVEDATA.BIN`; original account context kept local | Money; Bond point/skill; Persona acquire/equip; character level; equipment |

For each pair, record edition/build/language/DLC, slot/character, displayed before
and after values, and an unchanged control. Validate native identity, complete
integrity, byte-exact no-edit roundtrip, edited serialization and preservation of
unrelated data before qualification. Actual game load/re-save testing is a
separate result and must never be implied by arithmetic tests.
