# Romance of the Three Kingdoms XIII original PC

The `rotk13_pc` adapter implements **original Windows PC, save revision 14**,
qualified with seven complete publicly shared Traditional Chinese campaign saves.
Power Up Kit, console exports, scenario files, custom-officer files, system data
and other revisions are separate formats and are rejected. The source samples
do not identify an exact executable build or all installed DLC; support is scoped
to the demonstrated save revision and tagged layout, not every PC edition.

## Evidence and independent implementation

The [published Van editor description](https://dl.3dmgame.com/patch/96257.html)
explicitly covers save files as well as scenarios and custom officers. Its native
save reader/writer and city-field definitions were inspected statically; the
editor was never executed. The adapter was written independently from factual
encoding/record observations. No proprietary code, extracted names, resources or
binaries are redistributed. The [research review](STRATEGY_EXPANSION.md) records
other candidates and licence boundaries.

The original `San13Editor.exe` from published **1.00 Build20170220** was used
for this static inspection, separately from its PK executable. Its native city
loader/writer (0x4143D0/0x416540) establishes the serialized order and widths;
city getters (0x40EC60) establish the quantities' meanings. Native memory stride
0x16C is distinct from save stride 0xF2. These addresses identify the reviewed
editor build, not game-memory or save offsets for other editions.

The seven original PC saves independently corroborate the complete additive
encoding, native preview checksum, matching header/body revisions and tagged city
record layout. Source-backed field definitions distinguish money, military
supplies, **civilian population**, **military population** and wounded troops.
The two population fields are
separate components; no invented `military <= civilian` constraint is imposed.
The [official XIII manual](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/363150/manuals/SAN13Manual_en.pdf)
describes city resources and military systems. Derived total population and
deployed troops must not be confused with these stored components.

## Encoding and integrity

| Layer | Qualified behavior |
| --- | --- |
| Native file | Exactly 0x400000 bytes; `.s13` copied campaign input |
| Preview header | First 0x400 bytes; decoded title `SAN13 SAVEDATA` followed by NUL |
| Native encoding | Header and body independently restart an unsigned 32-bit generator at zero: `state = state * 0x41C64E6D + 0x3039` modulo 2^32; mask is bits 16–23. Decode subtracts the mask modulo 256; encode adds it. This is not XOR. |
| Preview integrity | Little-endian u16 at header +0x14 equals the unsigned byte sum of all 0x400 decoded header bytes except +0x14/+0x15, modulo 65536 |
| Save revision | Header little-endian u16 +0x16 and body little-endian u32 +0x00 both equal 14 |
| Body | Expected native section tags at revision-specific fixed offsets are checked before fields are exposed. Unknown padding and variable officer records are preserved, not interpreted. |

The published native city writer changes serialized city values without a body
checksum operation. The preview checksum covers the preview, not campaign city
data. City edits therefore preserve the entire preview and its original checksum.
The writer preserves the full decoded body outside declared fields, re-encodes
with the original native representation and reparses its output. Unchanged
serialization returns the original file byte for byte. Damaged preview integrity
is rejected rather than silently repaired.

## City quantities

The original PC `City` section starts at native file 0x3800 (decoded body 0x3400).
Its 0x20-byte tag precedes 60 records of 0xF2 bytes, followed by alignment and the
next native section. The scalar document's payload is the decoded **body only**;
field offsets exclude the 0x400-byte preview.

| Field | Record-relative offset | Storage | Meaning |
| --- | --- | --- | --- |
| Gold | +0x36 | little-endian u32 | Current city money |
| Supplies | +0x3A | little-endian u32 | Current military food/supplies |
| Civilian population | +0x3E | little-endian u32 | Non-military population component |
| Military population | +0x42 | little-endian u32 | Military population component, separate from deployed armies |
| Wounded troops | +0x46 | little-endian u32 | City's stored wounded population; does not change deployed armies |
| Fealty | +0xAE | little-endian u16 | Current city fealty |
| Commerce | +0xB1 | little-endian u16 | Current city commerce development |
| Farming | +0xB7 | little-endian u16 | Current city farming development |
| Culture | +0xBD | little-endian u16 | Current city culture development |
| Spear proficiency | +0xC7 | little-endian u16 | Current city spear training quantity |
| Horse proficiency | +0xC9 | little-endian u16 | Current city cavalry training quantity |
| Bow proficiency | +0xCB | little-endian u16 | Current city bow training quantity |

Stable field IDs identify the city record and quantity. Records are selected
from the validated existing native section. The read-only byte at record +0x00
is a **district reference**, not a force owner: valid district IDs are 0–119,
with 0xFF unset. Unknown references remain inspectable but their city fields
are not writable. City ownership and other references
are retained, and quantities do not acquire or transfer a city. Unknown IDs,
padding, unusual and higher quantities, other records, army data and scenario
outcomes remain byte-exact. City names are not imported from game assets or a
different edition's catalog.

All twelve quantities support deliberate whole-number edits within their unsigned
16- or 32-bit storage range. This is an encoding bound, **not a natural gameplay cap**.
All are `maxable=False`; Max does not invent a target or reduce an unusual value.
Assigning the opened original value removes the pending edit.

Development values are distinct from their separately serialized maximum-growth
values and forecasts. Training quantities are distinct from unlock levels and
derived combat effects. Those fields, prosperity flags and multipart durability
remain unchanged. Wounded editing does not heal armies, grant reinforcements or
apply a recovery event. This adapter changes stored current quantities only.

## Integration, tests and remaining work

The registered editor uses the shared searchable GUI, immutable staging, Undo,
Review Changes, automatic snapshots, guarded restore and atomic Save As to a new
destination. It rejects changed sources, existing destinations, resolved aliases,
live game/cloud paths, bad identity/revision/structure and unknown writable IDs.
The Windows build imports the backend/editor through the registry; the runtime
support catalog and generated inventories include this exact profile.

Run the format/contract/GUI tests with a display:

```text
python -m unittest tests.test_rotk13_format tests.test_rotk13_gui -v
python -m tools.update_supported_games --check
python -m koei_editor --smoke-test
```

Set `ROTK13_SAVE_COPIES` to a private directory of reviewed original PC revision-14
copies for native roundtrip and targeted-edit tests. The standard copied-save
self-test also uses this adapter:

```text
python -m koei_editor --game rotk13_pc --self-test INPUT.s13 EMPTY_OUTPUT_DIR
```

This generic self-test checks all 720 quantities, copies, integrity and restore;
it changes zero fields because no natural Max is established. Manual targeted
edits are tested separately. Its `checksum` report means the native preview
checksum; no campaign-body checksum exists for these city edits.

The shared path guard rejects the complete `KoeiTecmo/San13` live subtree,
including regional `EN_SAVEDATA`/`TC_SAVEDATA` folders and resolved aliases, as
qualified by the [published Steam Cloud configuration](https://steamdb.info/app/363150/ufs/).

Seven genuine saves established byte-exact unchanged encoding and preview
integrity. Targeted edits, malformed/foreign inputs, source/destination safety,
backup/restore and actual Tk workflows are covered separately from procedural
fixtures. **No edited save was loaded or re-saved in the game.** Exact executable
build provenance, additional regions and other revisions remain unqualified.
Officer attributes, relationships, equipment and deployed army systems require
separate native serialization and dependency mapping before they become writable.
