# Warriors All-Stars and Warriors Orochi 4 research

Reviewed 2026-10-10. Attached executables were read as byte buffers and
statically disassembled; neither executable was run. No game assets, binaries,
player saves, account data or private filesystem paths are included here.

## All-Stars: recovered PC envelope

`stars_candidate_codec.py` independently implements the native envelope
arithmetic recovered from the supplied `Star_US.exe`. It provides immutable
in-memory inspection and unchanged reconstruction only. This is a research
module, not an editor adapter or a supported game card.

The executable is AMD64, with an encrypted `.text` section and a SteamStub 3.1
`.bind` entry point. Its original code was decrypted privately for static
inspection using the documented header arithmetic; no instruction from the
executable was executed. The inspected code imports Windows CNG AES and embeds
`SAVEDATA.BIN` plus the standard `Documents/KoeiTecmo/WARRIORS ALL-STARS/Savedata`
path. This agrees with the [public backup manifest](https://github.com/mtkennerly/ludusavi-manifest/blob/master/data/manifest.yaml)
and the [PC save-location discussion](https://steamcommunity.com/app/610190/discussions/0/598539991659863325/).

Recovered instruction addresses below are RVAs in this supplied revision,
not save offsets and not supported revision identifiers:

| Routine RVA | Static finding |
| --- | --- |
| `0x71D4C0` | File span sizing: global plaintext `0x79B66`, slot plaintext `0x78E41`; each rounds to 16 bytes, adds 16 sentinel bytes and a 4-byte seed. |
| `0x71C450`, `0x71C360` | Global block uses key index 9; nine subsequent slot blocks use indices 0–8. |
| `0x71D560` | Initial double `(index+1)*0.5/10`, then ten ordered `x=(1-x)*(4*x)` operations. The low DWORD of the final IEEE754 double seeds key generation. |
| `0x71DF90` | AES-128 key: advance unsigned DWORD with `state*0x343FD+0x269EC3`, emit the high byte, repeat 16 times. |
| `0x71E440` | IV: advance unsigned DWORD with `state*0x15A4E35+1`, emit bits 16–23, repeat 16 times. |
| `0x71E560`, `0x71E8A0` | Explicit CNG `ChainingModeCBC`, key length 128, no CNG padding. |
| `0x71CB50`, `0x71BF10` | Encrypt and compare the final 16 bytes `FingerPrint01234`; store the initial IV seed as an unencrypted trailing DWORD. |
| `0x71C170` | Native encrypted slot offset `0x79B84 + slot*0x78E64`. |

The observed complete encrypted file size is `0x4B9D08` (4,955,400 bytes):

| Block | Key index | Plaintext bytes | Encrypted bytes | Seed bytes |
| --- | --- | --- | --- | --- |
| Global/system | 9 | `0x79B66` | `0x79B80`, including padding/sentinel | 4 |
| Each of nine slots | 0–8 | `0x78E41` | `0x78E60`, including padding/sentinel | 4 |

Original IV seeds and padding are preserved exactly. The native fingerprint
comparison is **not a checksum over the preceding payload**: the regression
suite demonstrates that changing a CBC block far from the trailer still passes
the sentinel. No complete gameplay integrity, internal title/revision marker,
semantic layout or account binding is claimed. Key arithmetic does not take an
account ID; that does not prove every internal record is account-independent.

The key seeds are stored explicitly after independently checking the executable's
ordered double arithmetic. This avoids floating-point differences in future
portable interpreters. Index 4 and global index 9 legitimately share a key;
key equality cannot establish block identity or a native revision.

`inspect_candidate(raw)` checks exact observed size and all ten decrypted
sentinels. `reencode_unchanged(document)` rejects any modified payload, padding,
seed or block order and verifies byte-exact reconstructed ciphertext. It has no
file writer and does not use a sentinel as authorization for gameplay writes.

### All-Stars coverage checklist

These are mechanically documented systems to map, not invented writable fields.
Every row is presently blocked by the absence of an independently acquired
complete native PC save and controlled one-action comparisons. The candidate
codec removes the outer encryption research obstacle; semantic qualification
remains necessary for every row.

| Mechanic | Research result and specific remaining proof |
| --- | --- |
| Gold/training purchases | Currency pays for training and cards/material sales; map current gold separately from request/lifetime earnings, and verify the purchase delta. |
| Character levels, EXP, actions, stats | Actions unlock with levels (guide reports all actions at level 20); map EXP versus derived level/stats and action flags. Bravery is battle-local and must not be presented as permanent character level. |
| Characters and route rosters | Initial factions and recruited roster differ; Opoona has ending dependencies. Distinguish permanent availability from current campaign recruitment; preserve selected protagonist and faction. |
| Hero cards/equipment | Cards replace a conventional weapon-growth editor here: map owner, rarity, attack, affinity/current and maximum, element, Friendship Gift, traits, occupied trait slots and equipped references. Do not label card affinity as regard. |
| Card customization and materials | Materials have origin and rarity, trait recipes and request dependencies. Map existing card and material records, counts, consumption and trait capacity; never create guessed empty records. |
| Elements | Five reported card elements: Fire, Ice, Lightning, Darkness, Love, plus no element. Frenzy is a combat effect, not a discovered sixth card element. IDs/ranks remain unmapped. |
| Regard/bonds and Hero Skills | Regard rewards and paired Hero Combo/Combo Skills require distinct character-pair records. Map asymmetric/symmetric structure, thresholds and prerequisites before bulk changes. |
| Requests/quests | Three request stages have fixed card/reward structure and reset with the main story/new game plus. Map active requests, progress, claimed rewards and reset behavior separately. |
| Stories, endings and map battles | Three faction routes, hero endings and true route unlocks have prerequisites. Require separate actions from currency/stat edits; no completion flags are enabled. |
| Gallery, songs and collections | Achievement and discussion evidence identify collectibles/unlocks; map ownership separately from viewing/new flags and DLC entitlements. |
| Mounts/bodyguards/weapon proficiency | Not established as independent permanent systems in this title. Do not import another Warriors game's features by analogy. |

Mechanics sources actually read:

- [Understanding Warriors All Stars](https://steamcommunity.com/sharedfiles/filedetails/?id=2911155500): Heroes, Hero Cards, Bravery and battle-local effects.
- [Materials List](https://steamcommunity.com/sharedfiles/filedetails/?id=1128232772): material names, origins, rarity and trait recipes.
- [Quest Compendium](https://steamcommunity.com/sharedfiles/filedetails/?id=1128263301): regard/card rewards, three-stage requests and story reset behavior.
- [Card elements](https://steamcommunity.com/sharedfiles/filedetails/?id=1132460396): five elements and Frenzy distinction.
- [Achievements guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1400955882): action/level progression and ending/Opoona dependencies.
- [Setsuna character unlock guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2801764723): faction recruitment and true-route prerequisites.

Guide observations are community mechanics evidence, not serialization offsets
or independently established gameplay bounds.

## Warriors Orochi 4 / Ultimate: launcher-only input

The supplied `WO4.exe` is a roughly 520 KB AMD64 launcher, with a 2021-08-02 PE
build timestamp. Its static strings name `WO4.dll`, `WO4U.dll` and a
`GaiaLauncher_JP` project; imports include `LoadLibraryW`, `GetProcAddress` and
Steam initialization. These findings identify the missing native gameplay code.
No save key, serializer or checksum implementation was recovered from this
launcher. The matching **`WO4.dll` for base WO4, or `WO4U.dll` for Ultimate**, from
the exact installed build is the next essential binary input. Supplying either
one alone does not replace the need for a complete native PC save.

The [public WO4U mod loader](https://github.com/Fragonite/zmod) is a process/asset
modification lead, not proof of a disk-save codec. PS4 cheat patches are also
platform-specific; no PS4 offsets were promoted to PC mappings.

### WO4/Ultimate coverage checklist

All writable rows require the matching gameplay DLL, an identified native PC
save and controlled mappings. The supplied launcher cannot establish any of them.

| Mechanic | Distinctions and exact remaining proof |
| --- | --- |
| Officers, level/EXP and skill points/tree | Verify stored EXP, allocated/spendable points, skills and derived stats per officer. |
| Ultimate promotions and stat stones | Promotion resets level and unlocks skills; community reports up to nine promotions. Map reset dependencies, allocated stones and reward grants separately; do not use a flat Max Level operation. |
| Gold, growth points and crystals | Verify separate balances and lifetime/spendable values, purchase/grant paths and legitimate caps. |
| Weapons/fusion/attributes | Verify existing inventory records, star/rarity, base attack versus compatibility bonus, attribute IDs/ranks/slots and fusion consumption. Ultimate camp upgrades reportedly raise some attributes to 20 and slots to ten; base WO4 constraints differ. |
| Unique and Infinity-crafted weapons | Story/objective unlocks and Infinity material crafting are separate acquisition routes. Require ownership and prerequisites, not merely a weapon ID swap. |
| Camp upgrades and unlocks | Camp affects bonuses, attribute capacity and character access; verify unlock/reward chains. |
| Bonds/support/party combinations | Verify per-pair progression, party references and team bonuses without treating temporary battle bonuses as stored stats. |
| Sacred treasures/deification | Verify eligible characters, ownership/equipped references and DLC distinctions before creating controls. |
| Mounts | Story/character unlocks provide regular horses, Red Hare and Matsukaze; DLC/early bonuses differ. No entitlement changes are implemented. |
| Story/side-story/ranks/objectives | Map chapter access, difficulty records, rank/S thresholds and challenge rewards separately; story completion remains an explicit independent operation. |
| Ultimate Infinity mode and fragments | Map towers/progression/materials and Perseus fragments independently of base story completion. |
| Gallery/music/costumes/collections | Verify stored unlock and viewing flags; preserve unavailable content and DLC requirements. |

Mechanics sources read:

- [WO4U characters and horses](https://steamcommunity.com/sharedfiles/filedetails/?id=1548552332): story, side-story, camp and mount dependencies.
- [Ultimate progression discussion](https://steamcommunity.com/app/831560/discussions/0/1742268227707773517/): promotion/stat stones/camp and attribute expansion distinctions.
- [Unique/crafted weapon guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2862301500): unique challenges and Infinity crafting.
- [S rank requirements](https://steamcommunity.com/sharedfiles/filedetails/?id=1552511935) and [team combinations](https://steamcommunity.com/sharedfiles/filedetails/?id=1577872429).

## Sample acquisition and validation limits

Public GitHub repository searches, Steam discussions and Steam guides were
retried after networking became available. No genuine All-Stars native save was
obtained from those inspected discussions; they supplied save-location and
load/corruption reports. Savegame.pro returned HTTP 403 and savegameworld.com's
requests were blocked before archive bytes arrived. WO4 discussions inspected
so far supplied save troubleshooting rather than an acquired native fixture.
Some later guide requests returned HTTP 429; those are rate limits, not evidence
that a feature or sample does not exist. No access control was bypassed.

The procedural test generator independently uses the documented double/key/IV
arithmetic and distinctive payload/nonzero padding. Seven focused checks pass;
one optional `STARS_SAVE_COPY` check skips without a privately supplied native
copy. Tests cover exact no-edit ciphertext, ten-block boundaries, altered
snapshot rejection, invalid parameters, truncation/foreign input, damaged
sentinels and the sentinel's inability to detect unrelated CBC corruption.

No genuine-save roundtrip, targeted gameplay edit, GUI workflow, backup/restore
or in-game load was performed for either game. Neither game is registered as an
editable library entry. Follow-up native fixtures remain private and should be
selected by environment variable; never add them to the source manifest.

Steamless's static wrapper documentation was inspected at
[commit cd770bf](https://github.com/atom0s/Steamless/tree/cd770bf9749d3e4f438d23ac643917ad1a804257).
Its CC BY-NC-ND 4.0 implementation remains outside this repository and release.
No third-party unpacker code was copied into the public candidate module, which
implements the game's independently observed save arithmetic using the
project's existing CNG AES provider.
