# Legacy Xbox 360 expansion: native evidence and blockers

None of the Xbox 360 profiles investigated here is registered as an editable
adapter. Existing PC and PS3 adapters do not qualify their Xbox 360 counterparts.
The separate titles below remain blocked on native gameplay evidence rather than
on a missing generic container writer. A bounded, unregistered Samurai Warriors 2
diagnostic records independently verified observations from a genuine public
save; it does not expose gameplay fields, repair checksums or save files.

## Samurai Warriors 2: genuine base-game export

The owner of the save in the public
[Game name change discussion](https://www.xpgamesaves.com/threads/game-name-change.77900/)
freely shared a [MediaFire download](https://www.mediafire.com/?97l9963k8bcilsp).
The discussion distinguishes a base Samurai Warriors 2 save from the XL save,
and describes a title-update-related display-name mismatch. This establishes a
public provenance lead, not a proven regional or native-format revision.

The downloaded package is a `CON ` STFS container of 790,528 bytes, with native
title ID `4B4F07D5` and directory entry `Samurai2.dat`. The entry's declared
file size is **716,800 bytes (`0xAF000`)**; both allocated-block counters also
happen to be 175. Extraction used the directory file size rather than treating
block allocation as a serialized-length rule. All 175 extracted data-block SHA1
hashes were checked against the active STFS hash tables. The directory data
block, both active level-zero tables, parent table and package header SHA1
relationships were independently checked as well. The package RSA signature
was not verified. Neither account identifiers nor player files are published.
The general container structure is documented by
[Free60 STFS](https://free60.org/System-Software/Formats/STFS/); no third-party
extractor implementation or editor binary was executed or copied into the app.

The native extracted sample has these observed big-endian DWORD relationships:

| Stored DWORD | Observed arithmetic in this sample | Qualification limit |
| --- | --- | --- |
| `0x2E70` | Sum of bytes in `[0x4, 0x2E70)` | An observed section relationship, not complete native integrity. |
| `0x22F1C` | Sum of bytes in candidate range `[0x2E74, 0x22E9C)` | The exact endpoint is unresolved: preceding zero bytes and the trailer's initial zero allow multiple matching endpoints. |
| `0x22F20` | Sum of the two observed section sums | Does not establish coverage of other header, trailer or padding bytes. |

The sample's trailer at `0x22E9C` begins `00 01 02 03`. An exact export length,
matching arithmetic and this marker do **not** identify an arbitrary file as
this game's qualified profile. No independently qualified internal revision or
region discriminator was found. The English discussion is not region evidence.
Japanese PS3 Samurai Warriors 2 HD money/checksum offsets were not transplanted.

The unregistered
[inspection module](../src/koei_editor/research/sw2_xbox360/inspection.py) accepts
only immutable bytes of the observed length, returns measured comparisons and
always reports `qualified_game_profile=False`,
`complete_integrity_qualified=False` and `editable=False`. It neither extracts
STFS packages nor returns account data. Corruption outside the candidate ranges
can retain all arithmetic matches; the tests explicitly demonstrate why those
matches cannot authorize writes.

To qualify even a money-only adapter, obtain independently identified base-game
exports for the same revision and controlled before/after shop transactions;
prove the serialized balance's width, owner and dependencies; resolve all
native checksum ranges, including the ambiguous endpoint; and establish native
edition/region discrimination. A transaction's known cost and acquired item
must be accounted for separately. Officer growth, skill purchase, weapon/item
acquisition, equipment, guards, mounts, Survival progression and collections
need their own native identities and controlled pairs. Story completion stays
separate. The original
[Xbox 360 manual](https://manualzz.com/doc/70494033/games-microsoft-xbox-samurai-warriors-2-owner-s-manual)
describes shared officer growth across Story, Free and Survival modes, equipment
and guards, and separate interim and cleared-stage saves; these mechanics
prevent treating an arbitrary changing value as an isolated editable resource.

## Per-title evidence and next input

| Separate Xbox 360 title/edition | Public evidence checked | Exact remaining blocker / next useful input |
| --- | --- | --- |
| Dynasty Warriors 5 Empires | [Legacy editor listing](https://www.xpgamesaves.com/resources/dynasty-warriors-5-empires-editor.1835/) advertises checksum fixing, items, mounts/orbs and an infinite-turn modification; its author warns that Delegate can loop indefinitely. | No reusable public source, genuine extracted profile or native checksum/record map was recovered. Obtain an unmodified native save and controlled resource/item purchases; prove turn/Delegate dependencies before any turn feature. The infinite-turn hack is not a safe gameplay bound. |
| Dynasty Warriors 6 Empires | [Legacy editor listing](https://www.xpgamesaves.com/resources/release-dynasty-warriors-6-empires-editor.1065/) advertises funds/gems and container support. | No independently verified extracted balance/gem owner, order, serializer or checksum source. Obtain separate ruler/officer campaign exports and known-cost purchases/forging actions; establish campaign ownership and legitimate resource bounds. |
| Dynasty Warriors 7 | [Legacy editor listing](https://www.xpgamesaves.com/resources/dynasty-warriors-7-editor.1578/) advertises Conquest money, officer stats/skill points and unlocks. An old Tech Game download listing is now served by the site's sunset landing page. | No available genuine native bytes, checksum/revision proof or Xbox field map. Obtain a native Conquest save plus controlled money, skill purchase and weapon/seal acquisition pairs. PS3 APP.BIN and PC mappings remain separate. |
| Samurai Warriors 2, base | Genuine native package and extracted payload described above. | Region/revision identity, complete native integrity and resource ownership remain unresolved. Resolve these independently before registering a balance control. |
| Samurai Warriors 2 XL | [Legacy editor listing](https://www.xpgamesaves.com/resources/samurai-warriors-2-xl-editor.1938/) and [author discussion](https://www.xpgamesaves.com/threads/samurai-warriors-2-xl-editor-xbox-360-mod-tool.126270/) distinguish `SAMURAI2` and `SW2XL_US`, including recognition fixes after updates. | These are advertised container basenames, not qualified payload identities. Obtain a genuine XL native export and title-update/revision facts; independently establish XL layout, checksums and import/ownership dependencies. Do not relabel the base-game sample as XL. |
| Warriors Orochi | [Legacy editor listing](https://www.xpgamesaves.com/resources/warriors-orochi-editor.2215/) advertises Growth Points. The [Xbox 360 GameFAQs page](https://gamefaqs.gamespot.com/xbox360/939310-warriors-orochi/saves) actually aggregates PC/PS2/PSP save categories. | No genuine Xbox payload or independently reusable native checksum/field source. Obtain Xbox-native exports around a known Growth Points expenditure; prove shared-pool versus officer EXP and equipment ownership. Other-platform downloads are excluded. |
| Warriors Orochi 2 | [Legacy editor listing](https://www.xpgamesaves.com/resources/release-warriors-orochi-2-editor.1063/) describes `OROCHI_EX`, Growth Points, proficiency, skills and stage dependencies. The [public save description](https://www.xpgamesaves.com/resources/warriors-orochi-2-orochi_ex.1153/) requires login to download and describes modified skills displaying incorrectly. The [Xbox GameFAQs page](https://gamefaqs.gamespot.com/xbox360/946499-warriors-orochi-2/saves) lists PS2/PSP categories. | No freely accessible genuine Xbox payload was recovered. A [public author discussion](https://community.wemod.com/t/release-warriors-orochi-2-editor/250) offered source to another editor project but did not publish that source. Obtain an unmodified native save plus controlled Growth Points, proficiency and weapon-fusion actions; prove recipes, ownership, material costs and progression dependencies. Modified skill values or published cheat targets do not establish natural caps. |

Repository and code searches for these exact game/editor names and native
basenames did not locate reusable native save-editor source for the listed
profiles. Binary editor download descriptions are leads only: none was executed,
decompiled or redistributed. Public game-data modding tools and runtime offsets
are not serialized save maps. The diagnostic is an independent implementation
of arithmetic measured in the native bytes, with no imported third-party code,
catalogue or game asset. These are bounded search results, not a claim that no
other source or genuine file exists.

## Saving and verification boundaries

Any future qualified extracted-payload adapter must preserve unknown bytes,
unusual values and complete gameplay integrity, use the shared backup/Review
Changes/Undo/atomic-save workflow, and revalidate its edited result. Editing an
extracted `Samurai2.dat` or another raw gameplay file would still require an
external STFS tool to reimport it, rebuild package hashes and resign for the
console. This application does not rebuild STFS, sign packages or change
ownership. Container SHA1 verification alone does not prove gameplay integrity
or console acceptance.

Four focused
[research tests](../tests/test_sw2_xbox360_research.py) cover procedural candidate
arithmetic, bounded immutable input, corruption in each observed range, unchecked
bytes which still match, and the explicit absence of qualification or write
APIs. With `SW2_XBOX360_EXPORT_COPY` supplied externally, the fourth test checks
the genuine extracted sample's observed sums/trailer without modifying it;
otherwise that genuine-file test is skipped. All four passed with the genuine
copy. This is a read-only genuine-file observation, **not** a gameplay no-op
roundtrip, edited-save validation, GUI save/backup/restore qualification or an
actual game-load test. No Xbox editing or game-load test is claimed.
