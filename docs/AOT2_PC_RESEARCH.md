# Attack on Titan 2 Windows save research

Reviewed on 2026-10-11. Attack on Titan 2 / Final Battle remains unregistered:
the genuine public PK-profile copy qualifies its **outer envelope**, while no
Windows gameplay field, record layout or exact revision qualifies for writes.
See [the shared native-save findings](OTHER_KOEI_PC_RESEARCH.md) and the
[read-only envelope diagnostics](../src/koei_editor/research/berserk_aot/envelope.py).

## Genuine-file qualification and its limits

The [SaveGame.Pro contribution](https://savegame.pro/pc-attack-on-titan-2-savegame/)
contains a complete `Attack on Titan2_AOT2_PK_WIN0000.dat`, 3,687,964 bytes
(`0x38461C`). Its surrounding archive and page attribute it to PC Attack on
Titan 2. The contributor's “completed,” “maxed” and “everything bought” labels
are claims about that upload; they neither identify a build nor establish any
field's displayed value, legitimate maximum or reward state.

The archive was read privately with the environment's existing archive library.
Only the native `.dat` was extracted; shortcut and URL entries were skipped.
No downloaded editor, trainer, game binary or external source code was executed.
No save, decrypted player bytes, account identifier, private path or asset is
included in the checkout.

| Observation | Independently checked result | Qualification boundary |
| --- | --- | --- |
| File framing | First four bytes are little-endian u16 sum and u16 seed; the remaining `0x384618` bytes align to u32. | This describes the observed envelope, not a complete title/revision discriminator. |
| Cipher | One advance of `state = state * 0x5B1A7851 + 0xCE4E` modulo `2^32` before XORing each little-endian u32. | AoT1's three-advance cipher does not transfer to this PK copy. Three- and four-advance alternatives fail its stored checksum. |
| Outer integrity | Sum of all decrypted little-endian u16 words after the four-byte header, modulo 65,536, equals the stored sum. | An additive checksum has collisions. Other integrity layers are still unqualified. |
| Unchanged reconstruction | Independently decrypting and encrypting preserves every file byte and the original seed. | This proves no-edit file arithmetic, not an edited file's game acceptance. |
| Corruption rejection | Flipping one bit separately at file offsets `0`, `1`, `2`, `3`, `4`, `0x1C230E` and `0x38461B` fails the outer check. | These seven corruptions do not prove cryptographic authentication or exclude inner checksums. |
| Decrypted prefix | Decimal-text metadata followed by padding; no verified literal title/revision marker. | Its unknown tokens are not published or interpreted as a native revision, region, account or gameplay field. |

The native optional test
`tests.test_berserk_aot_envelopes.OptionalNativeEnvelopeTests.test_aot2_pk_native_unchanged_outer_envelope`
passed: **1 test, 0 failures, 0 skips**. It checks byte-exact unchanged
reconstruction and independent first/last body-byte corruption rejection.
The separate seven-corruption/three-family inspection above also passed and
confirmed that the original copy's hash remained unchanged. No staged gameplay
edit, backup/restore, Undo, Review Changes or GUI save workflow was exercised for
AoT2 because it has no qualified gameplay adapter. **No edited game-load or
in-game re-save validation was performed.**

## Public editor/source audit

| Reviewed source | Actual scope and licence | Save-editing conclusion |
| --- | --- | --- |
| [AOT2-WEAPON-DATA-EDITOR at `05bef23`](https://github.com/the-real-thunderlol/AOT2-WEAPON-DATA-EDITOR/tree/05bef23d75c846663a5bfea051d2d97f914aa580) | `linkdata.py` opens `LINKDATA_PATCH_000.BIN` and regional text archives; `weapon_table.py` edits asset definitions. No project licence was found in the reviewed tree. No code was copied or run. | Its 112-byte equipment definition records, costs and 65,535 clamp are neither owned-equipment save records nor natural gameplay limits. |
| [Katsuki Engine at `b838066`](https://github.com/PythWare/Katsuki-Engine/tree/b838066ecb8f834d4db509297f0c64c28da600e3) | README/guide describe asset BIN extraction, rebuilding and mod packages. `katsuki_profiles.py` enumerates AoT1/AoT2 LINKDATA archives. Licence restricts use to non-commercial personal purposes and prohibits redistribution of source/binaries except upstream contributions. No code was copied or run. | Support for both games refers to game assets. The reviewed source does not supply Windows saved-profile fields. |
| [GokonSoftworks at `049d7f9`](https://github.com/PythWare/GokonSoftworks/tree/049d7f98eadd6670eeb7a74723fd7aade4643b5c) | Successor to Katsuki Engine. README describes game-container extraction/rebuilding and mod management; `GokonSoftworks/C_source/schema.c` assigns AoT1/AoT2 to `SCHEMA_FAMILY_LINKDATA_V2`. Same non-commercial/no-redistribution licence. No code, filename catalog or assets were copied or run. | Asset-container encryption/schema is independent of native save serialization; it provides no gameplay map for the reviewed PK copy. |
| [Digital2buy AoT2 service](https://digital2buy.com/product/attack-on-titan-2-save-editor-aot2-save-modding) and [Final Battle service](https://digital2buy.com/product/attack-on-titan-2-final-battle-save-editor-aot2-save-modding) | Commercial service pages advertise resources and unlocks; the Final Battle listing explicitly mentions a Switch saved-game prerequisite. No public implementation, record schema or licence for reusable source is supplied. | Marketing promises and console prerequisites are not proof of Windows offsets, revision support, natural bounds or safe ownership/reward transitions. |

The public-source search found no independently reviewable native Windows AoT2
save editor among these leads. That is a result of this survey, not a claim that
no such implementation exists.

## Persistent mechanics and separate dependencies

The official [Town Life/system page](https://www.koeitecmoamerica.com/attackontitan2/system2.html)
describes custom-character creation, equipment development, training, friendship,
regiment administration and scout missions. Scout missions award EXP, regiment
funds and materials and also increase the selected companions' friendship.
The official [Final Battle feature page](https://www.koeitecmoamerica.com/attackontitan2/finalbattle/feature.html)
and [upgrade page](https://www.koeitecmoamerica.com/attackontitan2/finalbattle/upgrade.html)
separately establish Territory Recovery, recruitment, camaraderie, regiment
emblems and additional equipment as expansion systems. These document mechanics;
they contain no save offsets or complete native bounds.

| Mechanic | Records/actions to distinguish before editing | Smallest useful controlled native pair |
| --- | --- | --- |
| Regiment funds and materials | Current balances versus lifetime earnings/spending, material identity and quantity versus acquisition/ownership and mission rewards. | Unchanged control plus one sale/purchase or one material-consuming action, with displayed before/after balances and quantities. |
| Existing blades, scabbards and ODM gear | Individually owned instance/slot, equipment definition ID, reinforcement state, equipped reference, development/upgrade costs and unlock prerequisites. | Reinforce one existing item once; separately upgrade/develop once and equip an existing different item, preserving the original inventory identities. |
| Reinforcement | Ordinary reinforcement versus its higher tier and the material transition; do not assign a storage ceiling as Max. A [player report](https://steamcommunity.com/app/601050/discussions/0/1698294337788185814/) describes a `+99`/rainbow-material transition but is not native record or universal cap proof. | One action on each side of the tier transition, matching displayed item identity, level, material consumption and unchanged control. |
| Character growth and skills | Custom protagonist growth versus other character progression; stored EXP/level and training versus derived equipment/battle values; learned/equipped skills, prerequisites, point spending and first-time rewards. | One EXP/level transition and one independent skill acquisition/equip action with displayed values and reward context. |
| Customization | Name text/encoding and fixed width, appearance selectors and valid referenced options; appearance is separate from growth, character ownership and story state. | One name or one appearance-option change per pair, with exact UI choice and region/build context. |
| Story-mode friendship | Custom protagonist's relationship with a character, conversation/event gates, gifts and reward/skill claims. | One gift/relationship increase, then a separate threshold/reward event pair. Do not raise a counter while resetting a claimed reward. |
| Regiment administration | Persistent learned policies/base upgrades versus the active policy, which the official page says lasts until changed or the player returns from a mission. | One policy change, one mission return and one permanent R&D purchase captured separately. |
| Territory Recovery camaraderie/recruitment | Expansion-specific regiment members and camaraderie relationships, territory progress, acquired emblems and rewards. These are separate from Story Mode friendship and the first game's progression. | One recruitment, one camaraderie increase and one territory/reward claim captured independently in a known Final Battle build. |
| Final Battle equipment/content | Owned/equipped gun/AP-ODM equipment and other new combat systems versus installed assets, expansion entitlement and unlock rewards. | One existing item change from a verified entitled profile; do not infer ownership from an available LINKDATA catalog. |

Battle gas, blade condition, HP, ally cooldowns and online match scores appear in
the official [action](https://www.koeitecmoamerica.com/attackontitan2/system.html)
and [online](https://www.koeitecmoamerica.com/attackontitan2/system3.html) descriptions.
Those temporary mechanics are not promoted to persistent growth/resource fields.
AoT2 customization, Story Mode friendship and Final Battle camaraderie/Territory
Recovery must not be transplanted into AoT1.

## Exact enabling inputs

An editable adapter still needs the matching original Windows serializer/getter
implementation or permissively reviewable source for this PK layout, or original
full save folders containing controlled actions and an unchanged control.
Include game/store edition, executable build/revision, region, DLC/Final Battle
context and displayed values. The sample's filename and size do not establish
that context. A base-game original profile and known-build PK profile would also
help qualify migration boundaries; no automatic conversion is authorized by the
outer cipher alone.

Before exposing a single field, prove its record base/count/stride, width and
endianness, slot or item identity, bounds and relevant dependencies, then every
remaining integrity layer. Unknown bytes and unusual/higher values must survive
no-op and unrelated edits. After field qualification, integrate the shared safe
storage/GUI contracts and test surgical edits, malformed/foreign input,
backup/restore, source protection, Undo and Review Changes. Edited game-load and
re-save validation remain a separate final evidence step.
