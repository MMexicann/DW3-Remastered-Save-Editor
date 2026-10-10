# Other Koei PC native-save follow-up

These titles remain **research-only**, without registered editing cards. Public
native saves were obtained and inspected privately, but no semantic field offset
is guessed from repeated values, runtime pointers or a different platform.
Game binaries, trainers, shortcuts and downloaded editors were not executed.
No save, decrypted player data, account identifier or private path is distributed.

The follow-up [DQH I/II and Fate/Samurai Remnant Windows status](LICENSED_ACTION_RPG_STATUS.md)
records newly acquired DQH1 compression evidence, reacquired DQH2 evidence,
source/licence exclusions, distinct growth and workshop mechanics, and exact
enabling inputs. None of those three titles clears the native editing gates.

## Public files acquired and cryptographic qualification

| Game | Genuine public native sample | Qualification completed |
| --- | --- | --- |
| Dragon Quest Heroes: Slime Edition, PC | [3DM contribution](https://dl.3dmgame.com/patch/114595.html), complete 102,400-byte `SAVEDATA.BIN`. | Independently decoded `LZP2` stream: observed wrapper word `1`, 61,648 compressed bytes and 642,716 decoded bytes. This establishes compression framing, not game revision, integrity, native serialization roundtrip or gameplay semantics. |
| Dragon Quest Heroes II, PC | [SaveGame.Pro contribution](https://savegame.pro/pc-dragon-quest-heroes-ii-savegame/), archive contains complete `SAVEDATA.BIN`, 1,575,744 bytes (`0x180B40`), plus `inputmap.dat`. | Native plaintext-looking complete file with observed prefix `031028160800000003000000`; header semantics and integrity remain unqualified. Contributor describes distinct progressed Teresa/Lazarel slots, classes, skills, proficiency, items and multiplayer progress. These are uploader claims, not game-load validation or natural-cap proof. |
| Berserk and the Band of the Hawk, PC | [SaveGame.Pro contribution](https://savegame.pro/pc-berserk-and-the-band-of-the-hawk-savegame/), `BKSAVEDATA0000.dat`, 1,268,512 bytes (`0x135B20`). | Stored u16 checksum/seed and known Koei three-advance word cipher exactly qualify the actual ciphertext. Decrypted prefix explicitly names `BERSERK and the Band of the Hawk`; own body semantics/other integrity are unqualified. |
| Attack on Titan / A.O.T. Wings of Freedom, PC | [SaveGame.Pro contribution](https://savegame.pro/pc-attack-on-titan-savegame/), `atwin0000.dat`, 769,568 bytes (`0xBBE20`). | Three-advance Koei word cipher and decrypted u16 checksum match. Decimal-text metadata in the decrypted prefix is not used as an invented universal title identifier or region/build label. |
| Attack on Titan 2, PC PK profile | [SaveGame.Pro contribution](https://savegame.pro/pc-attack-on-titan-2-savegame/), uploaded archive leaf `Attack on Titan2_AOT2_PK_WIN0000.dat`, 3,687,964 bytes (`0x38461C`). | **One** advance per word, rather than borrowing the first game's three advances; stored u16 checksum matches. Exact original game build/PK revision/region and gameplay schema remain unqualified. |

For the three encrypted samples, first four bytes are little-endian u16 word sum
and seed. Starting from that seed, each complete plaintext u32 is XORed with the
state after the observed number of advances:

```text
state = (state * 0x5B1A7851 + 0xCE4E) modulo 2^32
checksum = sum(decrypted little-endian u16 words) modulo 65536
```

Each chosen family passes native outer integrity, byte-exact decrypt/encrypt
roundtrip and independent single-byte corruption detection. Other tested one-,
three- and four-advance families fail the native checksum. This is not a region
identifier, semantic save schema or proof that no additional gameplay integrity
exists. No deliberate edited save was imported, loaded or re-saved. Downloads
include boilerplate shortcut/link files; they remain private and were not run.

## Source distinction

- [iccugs/BERSERK_trainer](https://github.com/iccugs/BERSERK_trainer), commit
  `afec9a6c7685b3b6c9bb7092762a686af9b99937`, operates on live process memory.
  Its gold pointer/control is commented out and its health/gold constants are
  trainer targets, not evidence of natural save-backed caps. No licence for its
  project implementation was located, and none of its code is copied or run.
  Live health/frenzy/death-blow addresses do not prove persistent stored growth.
- [the-real-thunderlol/AOT2-WEAPON-DATA-EDITOR](https://github.com/the-real-thunderlol/AOT2-WEAPON-DATA-EDITOR),
  commit `05bef23d75c846663a5bfea051d2d97f914aa580`, edits **game assets** in
  `LINKDATA_PATCH_000.BIN` and regional text archives. Its 112-byte equipment
  definitions, costs and blade/scabbard/ODM/horse/gun tables are not player-save
  inventory records. Its 65,535 clamp is a storage bound, not a legitimate Max.
- ExcaliburZero's Dragon Quest Heroes: Rocket Slime editor targets a different
  Nintendo DS game; marcussacana/DQHEditor edits strings/assets. Neither supplies
  a Koei PC DQ Heroes II save layout. Khazan editors likewise target an unrelated
  game despite the word “Berserker”; they are not Berserk save-format evidence.
- Official Steam app metadata corroborates the PC titles: Berserk 502280,
  AoT1 449800, AoT2 601050 and DQH2 574050. It exposes no public demo app for these
  titles in the reviewed metadata, so a matching freely downloadable native
  serializer executable was not located through that route.

## Per-game mechanic coverage and exact prerequisites

| Game / mechanic | Required next proof before an editable feature |
| --- | --- |
| DQH2 gold / small medals / resource inventory | Current-versus-earned/spent counters, serialized slot boundaries, integrity and ordinary-versus-quest-item ownership/reward flags. Plaintext and uploader completion labels do not prove offsets. |
| DQH2 character/vocation levels / EXP / skill points / classes | Main-character vocation versus party-character growth, legitimate caps/curves, derived stats, training/skill/class prerequisites and first-time rewards; controlled native level/class/allocation pairs or matching serializer code. |
| DQH2 weapon proficiency / weapon-orb-accessory inventory / enhancement | Distinct character/weapon-type proficiency records, equipment references, item IDs and intrinsic stats, enhancement ingredients/costs and actual array/layout rules. No DS/PS4/runtime-offset transfer. |
| DQH2 monster coins / maps / quests / exploration / collections / costumes | Temporary battle coins versus persistent discoveries, clear rewards, gates, starter records and entitlement state. Completion, resource and content actions remain separate. |
| Berserk money / materials / accessories and reinforcement | A native profile/array map proving current persistent quantities and accessory identity/slot/skill/rank relationships, legitimate bounds and synthesis/upgrade costs. Runtime trainer limits are insufficient. |
| Berserk character levels / EXP / HP / attack / defense / techniques | Persistent growth versus live battle gauges; synchronized EXP/stats/level rewards, character ownership and equipment-derived terms. Need matching `BERSERK.exe` serializer/getters or controlled growth/equipment-save pairs. |
| Berserk frenzy / death blow / transformation / support | Determine which values persist and their legitimate prerequisites; live trainer addresses do not become save fields. No invented mount/fusion/companion inventory. |
| Berserk story / free mode / Endless Eclipse / behelit rewards / records | Per-character progress/ranks, reward-claim and unlock flags, with prerequisites; no blanket completion or reward reset. |
| AoT1 funds / materials / equipment / horses | Exact serialized resource and owned equipment IDs/quantity/upgrade records, blade/scabbard/ODM/horses and equipped references; natural reinforcement limits and spending/reward dependencies. |
| AoT1 character growth / skills / stages / collections | Level/EXP curve, derived stats and learned-skill gates; mission results/ranks/rewards and actual persistent gallery/record identities. No AoT2 camaraderie systems transplanted into the first game. |
| AoT2 funds / materials / equipment / reinforcement / development | PK revision layout, individual item identity/ownership and reinforcement/upgrade costs; asset equipment tables do not qualify save arrays. Matching original native code or controlled display-correlated save pairs required. |
| AoT2 custom character / skills / camaraderie / regiment systems | Character/name/appearance encoding, learned-skill/prerequisite and friendship reward transitions, persistent regiment resources versus temporary battle values. No guessed gender/character swap or progression flags. |
| AoT2 Final Battle equipment / Territory Recovery / collections | Expansion layout/ownership and separate reward/recruitment/progression transitions; installed data alone does not grant entitlement. Named assets are mechanical references, not entitlement proof. |

The immediate enabling inputs are the matching PC serializer/getter executable
(or a source-backed native save editor) and full original save folders with
controlled before/after resource, growth, inventory, equipment and reward
changes. Additional sample downloads alone do not justify arbitrary integer
search/replacement. The proved cipher can be reused once those record facts are
available; unsupported games remain unregistered in the meantime.
