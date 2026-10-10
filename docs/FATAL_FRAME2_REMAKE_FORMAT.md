# Fatal Frame II: Crimson Butterfly REMAKE — Steam PC

The observed native PC revision `0x24121300` supports **shared system Photo
Point reductions** and read-only gameplay inventory/equipment/Camera Obscura
inspection. The adapter is separate from Wo Long despite inherited container
magic and serializer names. It does not register older Fatal Frame games,
console exports, demo saves or other revisions as supported.

## Independent native qualification

[casualspeedrun's freely shared Steam starting/practice saves](https://www.speedrun.com/FF2R/resources/lsb69)
provide original encrypted system files and gameplay files. The starting states
include intentionally modified zero-point/Nightmare and upgraded NG+ variants;
these are genuine native files, not proof of natural caps or ordinary ownership.
No player files, account context, binary patch modules or detailed private
analysis are included in this repository. No downloaded executable was run.

The title class in MIT-licensed
[KatanaSaveDataResigner, snapshot `4c90a2b`](https://github.com/mi5hmash/KatanaSaveDataResigner/blob/4c90a2b388438cb27a9752e6eab7333257de215f/KatanaSaveDataResignerCore/GameTitlesFactory/Titles/Ff2CbrFile.cs)
is a factual cipher/checksum lead. Its `ff2cbr-dummy` examples are explicitly
excluded from genuine-file evidence. Existing attributed Katana AES/checksum
primitives are reused; the title codec, parser and editor are independently
written. See [third-party notices](THIRD_PARTY_NOTICES.md).

| Native component | Qualified layout |
| --- | --- |
| Header | `0x100` bytes, unchanged except required checksums |
| Revision | `0x24121300` and matching inner pattern |
| System | `WLNSYS`, 61,851,984 bytes |
| Gameplay slot | `WLNUSR`, 9,318,960 bytes |
| Header/body lengths | Little-endian header fields at `0x14` / `0x18` |
| Encryption | Native AES-128-CBC body, original account/header preserved |
| Body checksum | 32 bytes at `0x50`, validates the entire body |
| Header checksum | 32 bytes at `0x70`, checksum range zeroed during computation |
| JSON | UTF-8 object at `0x110`, terminated by NUL |
| Post-JSON data | Opaque binary photograph data and padding, fully preserved |

Both native checksums match independently downloaded system and gameplay copies.
Wo Long magic alone grants no access: system parsing requires the distinctive
twin-doll/charm/spirit-stone/ghost collections and photo-array capacities;
gameplay requires Mio/Mayu, Camera Obscura flags, four charm slots, 650 possession
records and 550 storage records. Duplicate JSON members, invalid types, damaged
checksums, wrong revision/sizes and demo system data are rejected before fields.

## Resource editing and preservation

The system's `SystemPlayerRecordData.shop_point_` is a shared Photo Point balance.
The [official combat manual](https://www.gamecity.ne.jp/manual/zero/crimson-re/eng/5200.html)
explains the shared resource; [Koei Tecmo's support clarification](https://support.koeitecmo.info/hc/en-us/articles/56588368652953--FATAL-FRAME-II-CB-REMAKE-Lost-items-exchanged-for-Photo-points)
separates system points from per-slot purchases. Purchases deduct points in the
system; acquired items require saving the individual gameplay slot.

An opened nonnegative ordinary balance may be manually reduced to any whole
number from zero through its opened value. **Max and increases are disabled**:
no natural maximum or increase behavior has been independently qualified.
Negative or unusually high balances remain unchanged and inspection only.

Only the selected integer token changes. A shorter decimal value occupies the
original width using JSON whitespace, so all other JSON lexemes, unknown
members, formatting, binary photo bytes, NUL position and file lengths retain
their exact positions. No-op returns the original encrypted bytes. An edit
updates the two native checksum ranges, encrypts, reparses and compares the full
body and every other header byte. This avoids upstream JSON-import behavior
that clears/rebuilds the body and would destroy native post-JSON photographs.

The standard GUI supplies themes, staged Undo, Review Changes, source-change
checks, automatic backups and atomic Save As to a new destination. Live native
save folders, Steam Cloud paths and resolved aliases are blocked by shared
storage protections.

## Important mechanics and exact remaining inputs

| Mechanic | Implemented/tested or blocker |
| --- | --- |
| Shared Photo Points | Native system value, conservative reductions, both checksums and precise token preservation implemented/tested. Need unchanged and earned/spent controlled pairs plus displayed values to qualify increases/natural bounds. |
| Possession/storage counts and equipment references | Read-only numeric inspection. Unknown `key`/`key_num` values are not named or treated as ordinary resources. Need title-specific item catalog or controlled use/pickup/purchase pairs before quantity writes. |
| Film quantities/capacities | Blocked. The [consumable guide](https://gamefaqs.gamespot.com/ps5/559199-fatal-frame-ii-crimson-butterfly-remake/faqs/82421/consumables) reports different capacities by upgrade tier and different film types. Need native film identities and capacity dependencies; a large count in a modified save does not establish a legitimate maximum. |
| Healing, Prayer/Transcendence/Reversion Beads | Blocked. The [official upgrade manual](https://www.gamecity.ne.jp/manual/zero/crimson-re/eng/5300.html) describes spend/refund dependencies and item-based upgrade limits. Need verified bead IDs/counts, upgrade-tier encoding and controlled purchase/spend/reset pairs. |
| Charms/bags and camera equipment | Raw slot and camera flag inspection only. Need ownership, equip links, charm levels and bag-capacity rules; never manufacture them from numeric keys. |
| Twin Dolls, documents, ghosts, spirit stones and collections | System record counts inspected; unlock/reward flags unchanged. Need controlled collection/reward pairs and prerequisite rules. |
| New Game+, Nightmare, story/world/event flags | Separate from resource edits. Starting-save author documents Nightmare/NG+ exchange dependencies; no completion/difficulty/calendar action is provided. |
| `senki`, `bukun`, `xing`, skill fields in inherited serializer | Not interpreted as FF2 game mechanics. Shared engine names alone are insufficient evidence. |
| Native images/photo modes | Opaque image bytes preserved and checksummed, never rewritten as JSON padding. Photo records remain read only. |
| Other editions/builds and older Fatal Frame | Blocked on separately title/build-labelled original native files and corresponding integrity/schema proof. |

## Reproducible validation

```text
python -m unittest discover -s tests -p 'test_fatal_frame2_remake.py' -v
python -m koei_editor --game fatal_frame2_remake --self-test INPUT_COPY NEW_OUTPUT_DIRECTORY
```

The public suite constructs its own full-size envelopes with distinctive unknown
JSON/header/photo bytes. Tests cover checksum equivalence, complete no-op,
surgical scalar changes, lower balances, Max exclusion, unusual originals,
foreign/malformed inputs, duplicate members, dependency write rejection,
source changes, backups/restore and new destinations. Constructed states are
procedural tests, not player-save proof.

Optional `FF2_REMAKE_SYSTEM_COPY` and `FF2_REMAKE_GAMEPLAY_COPY` select genuine
native copies kept outside the checkout. Genuine-file roundtrip/checksum,
conservative edit read-back and GUI backup/restore evidence is reported
separately from procedural checks. **Actual edited in-game loading/re-saving has
not been performed**, and no fixture or cipher match establishes that claim.

The integration run passed all 11 format/shared-contract cases with both
optional genuine copies supplied. Independent review added exact-path escaped
JSON keys, opaque lexical preservation and malformed staged-state checks. Its
public Tk workflow uses a procedural envelope; a separate private execution of
that same workflow used the genuine positive-balance NG+ system copy and
confirmed a reduction plus exact source/backup/restore bytes. A zero-balance
native copy correctly produced no staged reduction. None of these checks ran
the game or transferred account identity.
