# Attack on Titan / Wings of Freedom Windows research

Status: **research only**. No gameplay field, native revision discriminator or
complete integrity inventory has been qualified. This title has no registered
editing card. The read-only [outer-envelope harness](../src/koei_editor/research/berserk_aot/envelope.py)
does not implement the scalar editor contract or save modified files.

## Copied-file evidence

The [SaveGame.Pro PC contribution](https://savegame.pro/pc-attack-on-titan-savegame/)
was acquired again privately. Only the complete `atwin0000.dat` was selected
from its archive: 769,568 bytes (`0xBBE20`). Archive shortcuts and links were not
executed. No player data, decrypted contents, account context, file hashes or
game assets are published.

The first four bytes encode a little-endian u16 sum and u16 seed. The existing
Koei word-cipher facts were independently recalculated on the complete copy:

- Advance the 32-bit state three times per complete little-endian u32 using
  `state = (state * 0x5B1A7851 + 0xCE4E) mod 2^32`, then XOR the word.
- The modulo-65,536 sum of every decrypted u16 after the four-byte header equals
  the stored checksum. One-advance and four-advance hypotheses fail this sum on
  the same input.
- An unchanged decrypt/encrypt reconstruction preserves every original byte,
  including the seed and checksum. This is a genuine copied-file roundtrip.
- Eleven independently selected one-bit mutations spanning the stored sum,
  seed, early/middle body and final bytes were all rejected by the harness.
  This does not mean an additive checksum detects every possible alteration.
- Truncated/appended files, the wrong AoT2 profile selection and a same-size
  zero-filled foreign buffer were rejected; the copied input remained unchanged.

The decrypted prefix contains separated decimal text. It has no explicit
`Attack`, `A.O.T` or `Wings` title literal in its first 64 bytes. Neither that
text, the filename, total length nor the successful word sum is promoted to a
native title/region/build identifier. The uploader's completion and equipment
claims are not correlated on-screen values or game-load evidence; the same page
contains a conflicting completion report from another user.

No deliberate gameplay edit, game load or game re-save was performed. Additional
checksums, profile boundaries, record counts/strides and ownership/reference
rules remain unqualified. AoT1-specific staging, Undo, Review Changes, backup,
safe-saving and GUI editor workflows were not tested because no writable AoT1
adapter exists; the read-only harness must not be reported as that editor.

## Public editor and source distinctions

| Source | Actual scope and licensing finding | Windows mapping consequence |
| --- | --- | --- |
| [Wakamu's AotSaveHack announcement](https://www.reddit.com/r/vitahacks/comments/530uo9/aotsavehack_a_simple_attack_on_titan_save_editor/) | Author describes a VB tool for an exported/decrypted Vita `app0000.dat`, with money and droppable-item patches. No source or licence located. No binary downloaded or executed. | A program running on a PC can still target Vita saves; this is not a native Windows parser. Cheat targets do not establish natural caps. |
| [Apollo PCSB00898 patches](https://github.com/bucanero/apollo-patches/blob/0ccc07ed39ea378db83e9901dbfa610b04637d7d/PSV/PCSB00898.savepatch) | GPL-3.0 repository; Vita EUR patch file credits Wakamu and lists a money write and 81 item writes. The page spells its title “Wings of Liberty”. | No patch table/code is copied. Console addresses are not Windows save offsets, and no cross-platform layout identity is proved. |
| [Kaplas80/AoTBinTool](https://github.com/Kaplas80/AoTBinTool/tree/0d30a3657a64f986b901717c2ff9089aa3654400) | MIT source, documented as an extractor/creator/updater for base-game and DLC BIN archives on PC/Vita/PS3. | Asset/archive records do not identify owned equipment, saved quantities or native save integrity. No implementation imported. |
| [Katsuki Engine AoT1 profile](https://github.com/PythWare/Katsuki-Engine/blob/b838066ecb8f834d4db509297f0c64c28da600e3/Katsuki_Logic/katsuki_profiles.py) and [GokonSoftworks AoT1 schema](https://github.com/PythWare/GokonSoftworks/blob/049d7f98eadd6670eeb7a74723fd7aade4643b5c/GokonSoftworks/C_source/schema.c) | Both licences restrict commercial use and redistribution. Reviewed AoT1 code selects regional `LINKDATA_*.BIN` containers and the `LINKDATA_V2` archive family. | Recent claims of full modding support concern unpacking/rebuilding assets and mod packages; no native `atwin0000.dat` gameplay schema found. No implementation copied into this project or run. |
| [Save Wizard's supported-cheat list](https://www.savewizard.net/wizardtest/index.php/downloads.php) | Commercial PS4 product lists funds, character EXP, equipment/item ownership and development unlock cheats separately. No native Windows save source/format supplied. | The feature labels illustrate distinct state categories but do not qualify offsets, dependencies or legitimate Max values. |

English/Japanese editor searches and GitHub repository/code searches did not
locate a source-backed native Windows gameplay writer for this profile. Runtime
trainer addresses and installed LINKDATA records remain excluded as save-offset
evidence. Broader family findings are in [OTHER_KOEI_PC_RESEARCH.md](OTHER_KOEI_PC_RESEARCH.md).

## Persistent mechanics and required next captures

The [Koei-authored Wings of Freedom manual](https://dlassets-ssl.xboxlive.com/public/content/3c60755a-2142-4051-8100-3e88110b0104/GameManual/72969523-d16d-4ad3-9b32-1a82d35c8e48/en-NZ/index.html)
is a mechanics reference, not Windows save-layout proof. It distinguishes
Regiment Skill, character Soldier Skill and learned skills. Battle rewards
increase experience; Regiment Skill gates equipment development. Owned gear,
materials and growth are shared between Attack and Expedition modes. The supply
station develops new gear, upgrades owned gear and fortifies it by combining
equipment. Materials and equipment can be exchanged for funds; horses have a
separate supply station. Survey progress can award funds, add information and
open battlefields. Gallery entries record encountered/obtained content.

AoT1 capture requirements therefore concern these systems; AoT2 custom avatars,
camaraderie and Final Battle Territory Recovery must not be transplanted here.
Keep resource balances separate from spend history, equipment ownership,
development availability, equipped references, first-time rewards and story
completion.

| Candidate | Precise enabling evidence still missing |
| --- | --- |
| Current funds | A same-build unchanged control and one purchase/sale pair with displayed before/after balance, excluding cumulative spending and earned/reward counters. |
| Materials | One displayed acquisition and one consumption pair for a known material, plus another ID/slot to prove encoding, ID/quantity relationship, count/stride and ordinary versus gated/reward inventory. |
| Existing blades, scabbards/canisters and ODM gear | Full copies around one equip, upgrade and fortify action. Identify individual owned records, equipment IDs, equipped references, fortification growth and consumed donor removal; preserve unknown records and values. |
| Horses | Purchase/equip pairs identifying ownership independently of the selected horse and gallery discovery. |
| Soldier/Regiment growth and learned skills | Display-correlated experience/growth pairs with a level/skill/development transition, proving whether levels/abilities are stored or derived and whether reward/prerequisite flags change. |
| Mission and gallery records | Separate stage completion/rank, Survey threshold/reward and newly encountered/obtained content pairs; no completion edit inferred from a resource quantity. |

All candidates first require the matching Windows build/region/DLC context and
serializer/getter evidence or controlled original-save pairs, a native title and
revision discriminator, complete profile/record bounds and every integrity
layer. Natural caps must be verified from that revision; numeric storage ceilings
and published cheat targets are insufficient. Higher/unusual original values
must survive unchanged operations. Additional unrelated progressed downloads
alone cannot resolve these blockers.
