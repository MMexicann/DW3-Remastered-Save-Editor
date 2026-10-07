# Weapon rare bonuses and elements — v0.3.3

Thanks to **austinkun** for reporting the missing rare bonus and element
controls in the Weapons tab.

Select an owned officer weapon. Its nine bonus dropdowns now offer normal
bonuses and 24 verified transferable rare bonuses. Add a rare bonus in an
empty slot or replace its type, then select **Apply Weapon Bonuses**. At most
one rare bonus is allowed. Its numeric control shows a dash because its saved
value is zero. Existing rare bonuses can be replaced but not removed.

Choose Fire, Lightning, Steel or Wind and select **Apply Element**. A weapon
without an element can acquire one; existing elements can be replaced.
Clearing an element is disabled because no native removal path was proven.
The target weapon does not need six hits: that condition concerns the source
weapon used in actual fusion.

Applied entries remain pending until saved. Undo, Discard Changes, Review
Changes and backups cover these edits. Max Selected/All Owned Bonus Rolls
raises normal numeric bonuses only. Grind presets retain existing rare
bonuses and elements rather than choosing them for the player.

## Format and evidence

| Field | Representation / rule | Confidence |
|---|---|---|
| `Skill` | Nine tagged `EquipItemSaveData` records | High: schema and supplied saves |
| Transferable rare IDs | 13–24 and 28–39, Type 1 with positive weapon-add probability | High: shipped table and generator |
| Rare `Value` | Int32 zero, including Hex Mark Saddle | High: native generator |
| Rare count | At most one; fusion uses final slot index 8 | High: native destination layout |
| Fire / Lightning / Steel / Wind | `Attr` Int64 bits 4 / 8 / 16 / 32; mask `0x3c` | High: reflected enum and native transfer |
| Other `Attr` bits | Preserved in full, including unknown high bits | High: only element mask is patched |

IDs 40–42 (Six Secret Teachings, Guardian Secrets and Red Hare Saddle Retro)
have zero weapon-add probability. They remain inventory items but cannot be
newly assigned as weapon bonuses. Existing unsupported identities remain
protected. Existing known rare values outside zero can only be preserved
unchanged; new rare rolls always use zero.

Rare additions/replacements/moves retain normal bonuses' relative order and
put the rare bonus in final slot 8, matching native fusion. Numeric-only edits
preserve earlier rare positions exactly. Normal count limits and
weapon-specific stock exceptions remain unchanged.

The generator selects one element bit and fusion replaces the whole element
mask rather than accumulating bits. New combined masks are refused. Existing
combined masks can be retained or replaced with a single element. All hit,
unique and unknown attribute flags remain unchanged.

These RVAs refer to the executable hash in `weapon_bonus_rules.json`; they
are research identifiers, not save offsets:

- Rare selection: `0x1535DE0..0x1535E28`, filters type and positive weight.
- Rare value: `0x151586F..0x151588C`, writes selected ID and zero value.
- Rare layout: `0x1697AC0..0x1697B13`, one final Type 1 slot.
- Element generation: `0x15158BC..0x1515955`, selects one of 4, 8, 16, 32.
- Element transfer: `0x16988C8..0x16988E7`, replaces mask `0x3c`.
- Source filter: `0x169ACA0` and `0x1699CA9..0x1699CF0`, excludes donors
  without an element.

## Integrity and boundaries

Disk boundaries come from parsed Unreal tags. Enum edits regenerate enclosing
sizes, total payload length and AES padding. Relocations can leave total
length unchanged; the integrity check now compares every plaintext byte to
validate that encrypted block set. The audit distinguishes `fields_relocated`
from total-size `resized`.

Combined unique acquisition and custom edits build the final inventory record
once. Missing collection snapshots use stock properties; existing snapshots
remain intact. Identity, DataID, acquisition time, equipment, other copies,
bodyguards, story and achievements are preserved. The editor writes the
result directly without consuming fusion materials.

No game executable, extracted assets or private save is distributed.
See [VALIDATION.md](VALIDATION.md) for automated results. This update awaits
in-game feedback. Keep an untouched backup and edit a separate copy.

## v1.0 unique element coverage

All 84 native unique weapon templates support Fire, Lightning, Steel or Wind,
including weapons acquired in the same pending batch. Element eligibility is
checked independently from bonus eligibility: an owned copy with a supported
identity, matching inventory reference and parsed Int64 `Attr` field can change
its element while its unusual or unsupported saved bonuses remain untouched.
The bonus controls remain protected on those copies. An unknown weapon identity,
inconsistent reference or unsupported attribute field still blocks element edits.

`element_changes` validates a whole selection before returning pending edits.
`owned_unique_element_changes` applies the chosen element to all supported owned
unique copies, including pending acquisitions, and omits copies already using it.
Neither action chooses an element automatically. New combined masks, invented
bits and clearing an existing element remain unsupported. Regression checks
serialize all 84 unique copies with each of the four elements and verify that
bonus tags, acquisition fields, collection snapshots, other inventory and all
non-element flags remain unchanged.
