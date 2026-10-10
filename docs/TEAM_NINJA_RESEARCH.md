# Team Ninja native PC save expansion

This document separates implemented editing, verified format inspection and
missing native proof. The current changes are unreleased. No game executable,
third-party binary or attached binary was executed, and no player save or owner
identifier is included in the source tree.

## Wo Long: Fallen Dynasty

The new [adapter](../src/koei_editor/games/wolong/wolong_parser.py) qualifies the
acquired Windows PC USER profile: exactly 5,120,272 bytes, `WLNUSR` identity,
revision `0x23121200`, a 256-byte header, matching inner revision, block-aligned
AES-CBC body and zero-padded UTF-8 JSON. It rejects SYSTEM files, unknown revisions,
wrong lengths, duplicate JSON keys, nonfinite numbers, damaged integrity and
unqualified inventory structures. The native USER and BACKUP files and a SYSTEM
file were independently acquired from a freely shared
[SaveGameWorld save](https://www.savegameworld.com/pc-wo-long-fallen-dynasty-savegame-100/).
All three pass the existing codec's native header and body checksums. The shared
save's description explicitly reports trainer-modified items; its unusual values
are evidence of existing data, not evidence of natural limits.

The cryptographic implementation already present in this project is derived
with attribution from MIT-licensed
[KatanaSaveDataResigner](https://github.com/mi5hmash/KatanaSaveDataResigner/tree/4c90a2b388438cb27a9752e6eab7333257de215f).
The new gameplay layer is independently written around the native JSON schema.
Both checksum ranges cover their full native header/body spans. Editing does not
disable integrity or rebind the save owner. An unchanged file is returned byte
for byte. Changed integer tokens retain the spelling and ordering of every other
JSON token, original header context, overall file size and zero padding. Both
checksums are rebuilt, the original input representation is retained, and the
output is reparsed and verified before saving a new copy.

### Current controls and limits

- `PlayerData.senki`, `sen` and `bukun`: manual Genuine Qi, Copper and Accolades
  balance controls. The range 0..2,147,483,647 is a conservative editor input
  limit, **not a recovered natural gameplay cap**. All Max actions leave these
  fields unchanged. Higher opened values remain unchanged on no-op and can be
  restored by Undo. `senki_storage` and `new_senki_storage` are shown separately
  and never rewritten as if they were the current available balance.
- Existing ordinary carried/storage stacks: quantity may be reduced to
  1..the opened quantity. The adapter requires a nonzero existing item key and
  instance, quantity greater than one, ordinary observed flag 8, no equipment
  slot, equipment part 0, stored item level 1 and weapon-skill level 0. Item
  creation/deletion and quantity increases remain unavailable because per-item
  capacities and reward/ownership dependencies are not yet qualified. Max is
  disabled. The acquired USER has 59 such carried and 18 stored stacks; these
  counts are fixture observations, not a required occupancy count.
- Searchable inspection: every populated record in the 600 carried and 2,000
  stored physical slots, including numeric item key, instance, quantity, rarity,
  stored item-level and weapon-skill fields, equipment part/slot and flags;
  companion IDs, bond levels/points/flags; character level, stored skill maximum,
  the five-Virtue array and both stored-Qi fields. Display names are not guessed
  from hashes or an alphabetical guide. The physical array counts are save
  structure, not a claim about an in-game carry capacity.

The GUI retains shared backups, Undo, Review Changes, themes and copy-only safe
saving. Tests distinguish procedural data, genuine-file qualification and actual
game loading. [Format tests](../tests/test_wolong_format.py) cover native integrity,
malformed/foreign input, exact no-op, lexical preservation, targeted edits,
unusual values, no-Max, stack reductions, snapshot forgery, backups/restore and
source protection. [GUI tests](../tests/test_wolong_gui.py) cover search, manual
edits, Review/Undo, inspection, themes and saving. `WOLONG_SAVE_COPY` enables the
private genuine USER test. Edited game-load/re-save validation has not been
performed by this project.

### Mechanics coverage and remaining proof

The [official update history](https://www.teamninja-studio.com/wolong/us/update/)
confirms important dependencies: Store Genuine Qi unlocks at the maximum level;
Apex Bonus unlocks at level 500; later updates raise stored-Qi and selected item
capacities; hidden Wizardry requires acquired Hidden Tomes; Martial Arts
replacement/improvement and Stratagems have separate unlock prerequisites.
Updates also explicitly add native tamper checks for Dragon's Cure Pot upgrades.
These mechanics must not be reduced to unconditional bit toggles or storage
ceilings.

| System | Current result / exact missing proof |
| --- | --- |
| Available currencies | Tested manual balances; natural caps and current-build grant/spend clamps need native routines or controlled boundary/action pairs. |
| Stored Qi, Apex Bonus and level-cap expansion | Read-only native fields. Need Store/Withdraw/Apex before/after pairs and native level/EXP/extra-level dependencies; do not confuse stored Qi with available or lifetime Qi. |
| Five Virtues, level, skill points and Wizardry | Read-only level/Virtue inspection. Need level-up/reset, learned-tome and spell-unlock pairs; level, distributed Virtues, extra levels and skill-point arrays are linked. |
| Ordinary inventories | Tested existing quantity reductions; increases require per-item carry/storage limits and catalog/type qualification. Numeric keys remain explicit. |
| Equipment reinforcement and rarity | Read-only inspection. In the genuine file, stored `item_level` 17 accompanies the author's reported +16 equipment: the stored field is not a direct displayed upgrade value. Need native conversion and material/reward/cap prerequisites before writes. |
| Martial Arts and replacement | Stored `weapon_skill_level`, inscriptions and DLC inscription arrays are separate systems. Need replacement/unlock/upgrade pairs and native derived-value/cache consumers. |
| Embedment, special effects, graces, Jewelry Essence | Native nested orb/inscription schemas exist; names, categories, allowed combinations, per-category magnitudes, costs and locked/premium distinctions need a licensed independently qualified catalog plus native consumers or controlled pairs. No affix/code injection is offered. |
| Equipment references, battle sets, appearance | Existing references, entry/instance numbers and appearance are preserved. Need equip/swap/remodel pairs that identify every cross-reference and any cache updates. |
| Companions and bonds | Read-only IDs, bond levels, points and flags. Need named ID mapping, bond thresholds and gear/reward flags before any bond/unlock writer. |
| Divine Beasts, Dragon's Cure Pot, customization | Native save fields exist but acquisition/upgrade dependencies and tamper checks require native routines or controlled pairs. |
| Mission progress, flags, DLC, NG+ and Thousand-Mile Journey | Native mission structures are preserved. Need mission/flag/reward and DLC ownership pairs; story completion remains separate from resources. |
| Titles, records, collections, gestures and unlocks | Native arrays exist; need stable catalogs, prerequisites and paired reward/history behavior. No blind all-unlock action. |

For further qualification, supply separate native current-build USER/BACKUP
copies plus pairs surrounding one ordinary action (displayed balances, Store Qi,
level-up/reset, equipment upgrade, Martial Arts change, consumable use/transfer,
bond increase or mission reward). Matching executable/module files can support
static validation of natural bounds and callbacks. No account transfer is
required for this adapter; original owner/header context is preserved.

## Nioh and Nioh 2

The existing Katana codec remains format inspection only for these titles.
Two independently downloaded genuine Nioh PC USER files are 2,043,288 bytes,
their SYSTEM companions are 9,824 bytes, and their decoded headers match
`NIOHUSR`/`NIOHSYS`, revision `0x17091200` and the native 328-byte header/body
length fields. Sources:
[PC save with screenshots](https://www.savegameworld.com/pc-nioh-savegame/)
and [second PC save](https://www.savegameworld.com/pc-nioh-savegame-2/).
Outer format/decryption evidence does not establish the gameplay integrity
algorithms.

The MIT [pawREP cipher tool](https://github.com/pawREP/Nioh-Savedata-Decryption-Tool/tree/1127f936ccc35b0f93f16b6d94e0e860f329942f)
explicitly implements `-cs` by clearing seven runtime integrity flags. This
project does not use that bypass. The Apache-licensed alfizari Nioh 2 editor also
clears integrity flags instead of rebuilding verified gameplay integrity.
The newer [sourcier Electron editor](https://github.com/sourcier/nioh-save-editor/tree/653412187484358f8a4796a89023cccd1e67a282)
is actually a Nioh 2/3 editor despite its repository name; its Nioh 2 write path
does not implement native gameplay integrity. No explicit source licence was
found there, and its source was not copied into this project. PS4 Apollo patches
are console-specific and include untested/patch-1.27-only claims; they cannot
establish native PC offsets, legitimate caps or write readiness.

| Important mechanic | Exact blocker before gameplay writes |
| --- | --- |
| Gold, Amrita, stored resources | Matching native integrity-enabled before/after pairs and native integrity/update routines; current/lifetime/storage distinctions must be proved. |
| Level, attributes, weapon/Ninjutsu/Onmyo proficiency, skills | Native PC width/revision and level/EXP/skill/reward dependencies; a cheat target is not a natural cap. |
| Weapons, armor, accessories, reinforcement, familiarity | Current PC inventory boundaries, named/type catalog and native reinforcement/familiarity/integrity consumers; do not mirror pre-forge and current levels by assumption. |
| Affixes, graces, Soul Cores, Scrolls, forge/remodel/refashion | Category-specific values, inheritance/locked/star effects, ownership/reference and integrity dependencies. |
| Guardian Spirits, clans, companions, blacksmith patronage, prestige | Named native records, point/threshold/reward and native integrity routines. |
| Missions, difficulties, Kodama, collections and story | Separate progression/reward controls and integrity-qualified native PC layout; no unconditional completion action. |

Nioh-specific investigation includes Guardian Spirit growth, weapon familiarity,
blacksmith patronage, prestige, Kodama and Abyss progression. Nioh 2 additionally
has Soul Cores/Anima/Yokai Shift, Scrolls, expanded weapon categories and
Underworld/Depths progression. These are distinct mechanics: console cheat
targets for Spirit level, proficiency, effect magnitudes and equipment upgrades
do not establish natural PC caps or reward dependencies. Their unknown integrity
prevents even otherwise plausible resource offsets from becoming safe writers.

The exact essential input is a matching native PC game executable and any
save-loader modules, or a trustworthy independently licensed implementation of
the runtime integrity algorithms, plus intact USER/BACKUP samples before and
after controlled actions. More saves alone do not close the unknown checksum
algorithms. Intentionally cleared integrity flags do not qualify an editor.

## Nioh 3

See the detailed [native Nioh 3 research](NIOH3_RESEARCH.md): genuine encrypted and
decrypted USER files already establish title/revision, whole-body checksum and
unchanged reconstruction. Native gameplay arrays are still unqualified.
The newly investigated sourcier implementation publishes equipment/resources
at offsets different from alfizari's. **Neither published set qualifies the two
acquired native revisions**: fixed offsets yield unrelated/unusual records and
attribute values rather than validated inventories/resources. A relocated
heuristic record scan is not proof of pool ownership, boundary or dependencies.

Current required inputs remain a matching native executable/serializer or
controlled pairs with displayed currency/attributes and known existing
equipment, usable/storage and owned-scroll actions. Preserve the distinction
between current level and pre-forge level, equipment and scroll effect starts,
displayed versus internal scroll level, and local effects versus network
canonicalization. Source-contained game parameter tables from GPL/PolyForm
projects are not bundled or relabelled as independent metadata.

## Stranger of Paradise Final Fantasy Origin

The existing explicit PC Katana profile implements AES-CBC and unchanged-only
inspection. The upstream cipher source does not qualify native gameplay
integrity, serialized job/EXP/point dependencies or equipment layouts. A freely
shared [SaveGamePro page](https://savegame.pro/pc-stranger-of-paradise-final-fantasy-origin-savega/)
links a MediaFire archive, but that archive currently returns HTTP 404. No native
player file was acquired from that link. Existing PS4 Apollo job-EXP patches
cannot qualify PC fields or legitimate job limits.

Steam discussion of
[save transfers](https://steamcommunity.com/app/1358700/discussions/0/3826411948442952727/)
also reports account/platform context mismatches, and
[preorder equipment](https://steamcommunity.com/app/1358700/discussions/0/3826411948444568185/)
has game-load ownership/sanity restrictions. Such reports identify dependencies
to investigate; they are not native code proof or approval to disable checks.

Required: a freely shared separate native PC `SAVEDATA.BIN`/SYSTEM pair with
matching build/loader modules, or controlled native plaintext/action pairs;
then native body integrity, job unlock/limit-break/EXP, Anima shards/crystals,
rat tails, Dragon Treasure, gear/affinity/Chaos effects/upgrade and synthesis,
companions, DLC/rift/labyrinth/monster progression and mission rewards must each
be qualified. Cipher vectors and console patches alone do not authorize writes.

## Additional Team Ninja leads

| Game / source | Discovery and exact qualification boundary |
| --- | --- |
| Ninja Gaiden II, original Xbox 360/Xenia | [ike9000e's GPL-3 checksum utility](https://github.com/ike9000e/ngii-save-update-util) supplies source for a big-endian 32-bit word sum over the 30,848-byte gameplay block, followed by the stored sum. Its documentation describes 128 four-byte item records and Dragon Sword level codes. A separate [browser editor](https://github.com/rnrmfdlapdlf/ninja-gaiden2-save-editor) lists essence, Karma, health/Ninpo and named consumables. Neither establishes a genuine raw fixture here or natural caps. No code is copied. Needed: a genuine original-game raw save with identity/header or correctly extracted STFS entry plus matching mid-chapter action pairs. Generic checksum-shaped Xenia bytes alone are insufficient identity. Xbox CON container integrity must also be rebuilt before container writes. |
| Ninja Gaiden 2 Black, Windows PC | [real-guilty's purported save-editor repository](https://github.com/real-guilty/NG2B-Save-Editor/tree/fd7b25934e9cda24d47d9a59c7b7a3398ef22a0f) contains compiled PyInstaller artifacts, not reviewable application source, and has no explicit licence. Its README describes brute-force SYSTEM unlocks and mutually exclusive Tag Mission weapons. No artifact is executed, copied or represented as open-source field proof. Needed: genuine Steam SYSTEM/player files, title/revision/integrity qualification and safe unlock/reference dependencies. |
| Ninja Gaiden Sigma / Sigma 2 / Razor's Edge | Freely shared PC and PS3 saves exist, but they are separate editions from original Xbox 360 Ninja Gaiden II and Ninja Gaiden 2 Black. A PC page titled “Ninja Gaiden 2” actually links a Sigma 2 archive and describes Sigma-only Tag Missions; it cannot qualify the original game's fields. Needed: edition-specific serializers/integrity and field/action evidence. |
| Rise of the Ronin, Windows PC | The MIT Katana source documents unencrypted binary `RNNUSR`/`RNNSYS` data with a 256-byte header. Its fixture is explicitly a dummy. No native player fixture, internal integrity or gameplay map was qualified; matching native USER/SYSTEM files and serializer/action evidence are still needed. |

The original Ninja Gaiden II fixture search also checked the public Xenia
[compatibility discussion](https://github.com/xenia-canary/game-compatibility/issues/492).
It links a [public Master Ninja save discussion](https://www.reddit.com/r/ninjagaiden/comments/170nejv/ninja_gaiden_ii_xenia_master_ninja_save_file/),
but the Reddit page/API returns HTTP 403 here, so the linked player archive was
not acquired or qualified. GameFAQs' original Xbox 360 save page returns HTTP
400. The Tech Game's former download index now serves its sunset notice, not a
save archive. Xenia issue attachments inspected as references are identified as
logs; an emulator configuration folder is not treated as a player-save source.
These unavailable leads do not justify substituting Sigma 2 or manufacturing a
checksum-shaped test file as evidence of native original-game identity.

The optional [native corpus tests](../tests/test_teamninja_native.py) use
`TEAM_NINJA_NATIVE_DIR` for the separately held four Nioh files and three Wo Long
files. They preserve active Nioh integrity flags and confirm that decryption does
not authorize Nioh gameplay edits, while Wo Long requires both real checksums.
This corpus is private and excluded from source/bundles.
