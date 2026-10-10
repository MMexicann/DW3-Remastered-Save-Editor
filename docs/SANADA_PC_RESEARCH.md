# Samurai Warriors: Spirit of Sanada — Windows PC

## Result and qualified boundary

The Windows Steam edition is app **595740**, separate from Samurai Warriors
4-II, 4 DX, the original 4, and console Spirit of Sanada. Two freely shared
complete gameplay files and their system companion were downloaded and examined
without executing game/editor binaries. Complete outer decryption, checksum
verification and byte-exact unchanged re-encryption pass for all three.

There is **no registered gameplay adapter**. Title/build identification, inner
native integrity and field/record ownership are not sufficiently established to
write resources or progression safely. The tested outer checksum is a weak
16-bit word sum; matching it does not establish a playable, authentic or
uncorrupted gameplay file. The research code intentionally rejects modified
envelopes and exposes no gameplay writer or Save As API.

## Genuine-file evidence and framing

The [Manga Council PC/Steam save post](https://mangacouncil.blogspot.com/2018/12/samurai-warriors-spirit-of-sanada-save.html)
freely shares a player-contributed archive and describes level 99 officers,
maximum friendships, all characters, gallery completion and multi-stage battle
objective completion. The archive contains `SAVEDATA0000.dat`,
`SAVEDATA0001.dat`, `SYSDATA.dat` and a credit image. Player files, image,
archive, original seeds and private inspection reports stay outside Git.
The description is provenance, not an independently observed gameplay state or
a controlled before/after action pair. Exact executable build, language, region
and DLC configuration were not supplied.

| Observed class | Complete native bytes | Decoded bytes | Observations |
| --- | --- | --- | --- |
| Gameplay (`SAVEDATA0000.dat`, `SAVEDATA0001.dat`) | `0x28A104` | `0x28A100` | Both have decoded DWORDs `0x10`, `0x65` at 0 and 4; DWORD `0x846` at `0x100`. |
| System (`SYSDATA.dat`) | `0x1004` | `0x1000` | Same first two decoded DWORDs; DWORD `0x10` at `0x100`. |

For these independently tested copies only, raw bytes 0–1 contain a
little-endian unsigned 16-bit sum of **all** decrypted 16-bit words, modulo
65536. Raw bytes 2–3 contain the retained 16-bit seed. Bytes 4 through EOF are
XORed as little-endian DWORDs. Advance the 32-bit state three times for each
DWORD with `state = state * 0x5B1A7851 + 0xCE4E (mod 2^32)`, then XOR that
state with the word. This reproduces all three stored checksums and original
files; the one-step variant fails. The independently implemented shared
primitive is reused after this direct genuine-file comparison, without importing
another game's headers, offsets, internal checksums or maxima.

The first two DWORDs are **observed shared-copy framing**, not unique title IDs.
`0x846` is an observed gameplay marker, not a proven native revision or build
number. No semantic names are assigned to date-like header integers or any
other decoded values. Gameplay and system classes require explicit selection;
there is no parser fallback. Autosave/manual/interim slot roles still need
native reader/writer or controlled save-mode evidence.

The [Ludusavi manifest](https://github.com/mtkennerly/ludusavi-manifest/blob/master/data/manifest.yaml)
corroborates `Documents/KoeiTecmo/SW Spirit of Sanada/SAVEDATA` and app 595740.
Location evidence does not qualify contents. Always investigate isolated copies,
outside the live folder and Steam Cloud synchronization.

## Mechanics investigated before choosing fields

The official [Steam English PC manual](https://store.steampowered.com/manual/595740)
is the primary mechanic source. Page numbers below are printed manual pages,
not viewer indices. Manuals establish systems and dependencies; they do not
establish disk offsets or a natural cap for every stored value.

| System | Source-backed behavior | Exact additional evidence required |
| --- | --- | --- |
| Gold and Sanada Clan EXP | Dojo training spends Clan EXP to raise an officer's level; gold purchases moves, Musou and Rage training (p.17). These are separate resources, and shared Clan EXP is distinct from officer EXP and lifetime totals. | One purchase and one Clan EXP training pair, displayed before/after balances, unchanged control, complete integrity and offsets/widths. |
| Officer growth, attacks and exploration training | Training options depend on officer level. Musou training increases gauge units; Rage training increases maximum intensity; special training raises the officer's level ceiling; exploration training adds exploration time (p.17). | Same officer identity across a level-up, each training purchase and special-training pair; growth tables and saved-level/EXP/derived-stat distinction. No automatic story or training prerequisite writes. |
| Weapon proficiency, slots and skills | Proficiency from defeating enemies raises rank and unlocks up to eight skill slots. Blacksmith upgrades/adds/removes skills using materials. The manual states skill effect values can reach 99 (p.15). | Existing record identities, owner/weapon dictionaries, rank/proficiency thresholds, occupied and unlocked slot maps, one skill add/remove/upgrade and rank-up pair. A mechanic cap alone does not establish serialized width. |
| Fixed and upgradable weapons | [PC weapon discussion](https://steamcommunity.com/app/595740/discussions/0/1743357605582256406/) distinguishes default weapons from fixed DLC weapons; runtime DLC edits reportedly disappear after save/load. It describes a runtime record pattern, not disk offsets. [PC progression discussion](https://steamcommunity.com/app/595740/discussions/0/1290691308582358622/) also distinguishes fixed ultimate weapons. | Native lookup/write evidence and owned default/DLC/ultimate records; acquisition must remain distinct from equipment. Do not treat runtime targets as disk addresses or natural stat maxima. |
| Materials, medicines, fishing, farm and Jizō | Materials are acquired, purchased, given as gifts and combined into medicine; farm and Jizō exchanges take time (pp.14,18–19,25). | Qualified item catalogs, count/new/owned flags, one recipe/purchase/gather and timed-exchange pair; preserve timers, pending harvests and delayed rewards. |
| Mounts and companions | Stables sell mounts (p.14). Friendship may allow officers to join exploration (p.16); exploration companionship is separate from mounts and playable character ownership. | Buy/equip mount pair and companion-select pair, existing mount/character IDs, equipped references, catalogs and rank/stats rules. |
| Friendship and known favorites | Gifts raise friendship. Favorite gifts can increase it more, reveal known favorite categories and grant return gifts at high friendship (p.16). | A normal gift, favorite discovery and reward-bearing pair plus actor identities. Friendship, known favorites, reward flags and gift consumption must stay separate. |
| Playable unlocks | Conch shells at Raifukuji unlock officers for past battles or grant Clan EXP (p.14). | One conch unlock and one conch-to-EXP pair; shell consumption, existing character IDs, scope and reward dependencies. No invented universal unlock mask. |
| Exploration, objectives, Six Coins and stratagems | Exploration has goals and gathering. Stratagems consume Six Coins and must first be unlocked by prior battle objectives/feats (pp.21–26,51–52). | One exploration goal, objective/feat, coin award/spend and stratagem pair. These transition/reward records must be separate from resource edits. |
| Collections and customization | Vault shows event scenes, music and battle objectives; Shop changes costumes (p.14). | Gallery/event/music dictionaries, one collection/costume acquisition/equip pair, exact DLC/build and dependency map. No assumption of a custom officer editor from related SW titles. |

The manual explicitly distinguishes town/manual saves, autosaves and interim
battle saves; interim saving is unavailable during exploration (p.7). A
[Steam achievement save request](https://steamcommunity.com/app/595740/discussions/0/572642335441032442/)
reports that loading completed saves did not trigger the Vault achievement.
This reinforces the need for transition/reward testing; it does not prove a
particular disk flag.

## Public-source search and licences

GitHub repository and indexed code/source searches found no save-specific
Spirit of Sanada PC editor or complete native format mapping. The
[Steam save-editor discussion](https://steamcommunity.com/app/595740/discussions/0/1743356517527588873/)
only suggests runtime trainers. Steam save searches, official manual and PC
mechanic discussions were read. Nexus requests returned HTTP 403. SaveGame.Pro
and GamesKeys descriptions repeat the same completed-player provenance;
GamesKeys' CDN download returned HTTP 403. The independent usable archive was
obtained from the public Manga Council link using its normal download form.
The public Hackinformer result concerns **PS4 CUSA07931**, so it cannot establish
PC offsets, cryptography or integrity. Related console cheat catalogues and
runtime trainers do not supply disk mappings.

Additional Chinese-language source searches separated genuine leads from
mislabelled categories. Older VanEditor guides under today's Sanada forum
category describe the **2015 SW4-II** roster; they are not Sanada native
research. The [Gamersky completed PC save page](https://down.gamersky.com/pc/201706/913609.shtml)
explicitly describes **modified** weapon ranks/proficiency and also lists
uncompleted collections despite its broad title. Its ordinary download link
returned 404, another mirror was blocked, and the remaining mirror presented a
file-host landing page; no additional bytes were qualified. This description
must not be reported as untouched game-generated progression evidence.

No third-party editor implementation or game/catalog asset is copied into the
project. Public prose is summarized; the shared cipher implementation is already
independent project code. Source availability is not a licence to distribute
player files, game binaries or entire external projects.

## Validation and remaining inputs

`tests/test_sanada_pc_framing.py` distinguishes procedural envelope tests from
optional genuine-file tests. Procedural checks cover retained seeds/unknown
bytes, malformed sizes, wrong explicit classes, single-byte corruption,
checksum-valid foreign prefixes and rejection of modified payloads/seeds. The
genuine test checks all three complete original files, full outer checksums and
byte-exact unchanged re-encryption. Select a private folder with
`SANADA_PC_SAVE_COPIES`; absent input skips only the genuine test.

No gameplay edit, actual GUI save/backup/restore, native inner-checksum coverage,
or game load/re-save is claimed for this research lane. There is no registered
adapter to exercise these operations yet. Procedural copies are not genuine
saves and the outer word sum cannot detect every compensating corruption.

To implement a native adapter, obtain the exact matching **`SWSanada.exe`** for
static inspection (never execution), its build/language/region/DLC labels and
required gameplay parameter tables, or trustworthy public native parser/writer
research together with controlled gameplay pairs. Resolve inner checksum
locations/coverage, migrating revisions, title discrimination and complete
record identities before any writes. Keep these inputs private. The genuine
copies already acquired remove the missing-fixture blocker; they do not remove
these schema/integrity/ownership blockers.
