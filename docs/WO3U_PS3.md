# Warriors Orochi 3 Ultimate: US PS3 decrypted export

The separate `wo3u_ps3` adapter edits **unallocated growth points** and **precious
stones (gems)** in the US PS3 Ultimate profile. Officer progression/stats,
existing weapons and published inventory arrays are inspected read only.
Original PS3 Warriors Orochi 3, Japanese/European Ultimate, Vita, PS4, Xbox
and PC Definitive Edition remain separate profiles and are not accepted here.

## Copy, edit and return to the console

Export a decrypted `APP.BIN` using Apollo Save Tool. Keep the original console
export and work on a separate copied directory. Keep that export's original
`PARAM.SFO` beside the copied `.bin`; exactly `NPUB31505-SAVEDATA` is required.
The parser reads only the save-directory identity and retains a digest of the
opaque metadata to detect changes. Use the two individual controls, Review
Changes and Undo. Save As writes atomically to a new `.bin` file with an
automatic backup. The destination must remain beside the same unchanged
`PARAM.SFO`; restore also requires exact US metadata.

Reimport and resign the edited gameplay export with Apollo before PS3 loading.
This application does not encrypt exports, rebuild `PARAM.PFD`, change ownership
or sign console saves. The shared copied-save self-test copies original bounded
`PARAM.SFO` unchanged beside its private outputs. No account value is extracted
or modified; do not publish metadata files, backups or test outputs. Ordinary
Save As does not manufacture or copy metadata for another destination.

## Exact profile and field evidence

| Check | Qualified US PS3 Ultimate layout |
| --- | --- |
| Plaintext file | Exactly `0x2119CA` bytes (2,169,290) after external PFD decryption |
| Revision | Little-endian u32 `0x140318F1` at offset zero |
| Officer structure | 150 serialized records: four-byte marker `188DD000` at `0xECE8 + index * 0x2B0`; 145 ordinary records and five internal records |
| Weapon structure | 2,320 records: four-byte marker `B88BD000` at `0xC800C + index * 0x1C` |
| Region/edition context | Mandatory bounded original `PARAM.SFO`, exact save-directory `NPUB31505-SAVEDATA` |
| Growth points | u32 little-endian `0x1378`, manual range 0–9,999,999 |
| Precious stones | u32 little-endian `0x137C`, manual range 0–999,999 |

The PC port shares length, revision and many logical positions. That is
insufficient qualification: its serialized class markers differ. Every PS3
record marker is independently validated; PC markers are rejected. Changing a
marker, revision or length rejects input before editing.

Both controls set `maxable=False`. Published/manual limits are not automatically
applied to player saves. One genuine sample has a gem balance above the supported
edit range; it remains unchanged on open, no-op Save As and Max. Assigning the
original unusual value removes a staged edit. Only the selected four bytes
change; unknown data, progression, ownership, equipment and story are preserved.

The independently read primary
[2015 PS3 Ultimate direct-edit discussion](https://nextgenupdate.com/forums/ps3-mods-answered-questions/848494-brute-force-cheats-request-warriors-orochi-3-ultimate.html)
reports that direct little-endian hex edits at `0x1378` and `0x137C` work. The
author labels `0x05F5E0FF` as 9,999,999 although it is 99,999,999; that erroneous
conversion is not implemented. Correct 9,999,999 encoding is `7F969800`; gems
999,999 encode as `3F420F00`. The fuller console patch list later appears in the
thread, but other systems lack sufficient field-specific loaded-edit evidence.

The [Apollo PS3 patch database](https://github.com/bucanero/apollo-patches/tree/main/PS3)
provides offset/width/stride leads in `NPUB50173.savepatch` and
`NPEB02052.savepatch`. Those IDs are not accepted as the genuine US profile.
Two downloaded US exports independently establish `NPUB31505-SAVEDATA` and its
record structure. Public facts are independently implemented; no Apollo GPL
implementation or patch catalogue is copied into this adapter. Original source
copies remain outside the checkout.

## Integrity and validation limits

The field-specific direct-edit report supports writing these two balances
without an additional gameplay integrity rewrite. Their published patches do
not specify one. The writer preserves all other bytes and reparses the complete
structural profile after edits. This does not establish that every unknown
gameplay section lacks a native checksum. Arbitrary corruption in opaque data
cannot be detected. PFD authentication, encryption and reimport/resigning remain
external; the self-test does not claim verified native checksums.

Two genuine freely shared exports were obtained privately from
[GameFAQs save 28430](https://gamefaqs.gamespot.com/ps3/720582-warriors-orochi-3-ultimate/saves/28430)
and [save 23948](https://gamefaqs.gamespot.com/ps3/720582-warriors-orochi-3-ultimate/saves/23948).
Both metadata titles explicitly identify Ultimate. GameFAQs aggregates related
editions' saves: older approximately 919 KB original-WO3 archives do not qualify
this approximately 2.1 MB Ultimate profile. PFD decryption was implemented
privately from documented AES/container facts without running game/editor
binaries. No save, owner identifier, key or private analysis is included in Git.

`tests/test_wo3u_ps3.py` distinguishes generated fixtures from genuine files.
`WO3U_PS3_US_COPIES` optionally contains an OS-path-separated list of copied
decrypted `.bin` inputs, each beside its original `PARAM.SFO`. Genuine checks
establish byte-exact no-op roundtrips and surgical/reparsed edits for both
resources. Procedural checks cover foreign markers, truncation, context changes,
bounds, higher values, immutable snapshots, invalid pending edits, backups,
restore and source safety. Tk checks search, Apply, Review, Undo, Max preservation,
inspection, themes, backup, Save As and restore; supplied private inputs make
that workflow use a genuine copied export. These are **file and GUI tests**.
No locally edited save was loaded or re-saved in an actual PS3 game here.

Seven focused tests passed with both private genuine exports and a virtual Tk
display, including actual GUI theme application and Restore Backup dialogs.
The registered copied-save self-test also passed independently for each genuine
export: two fields checked, zero fields automatically changed, exact source/no-op
preservation and backup restore. Both reports correctly identify external
integrity, `native_integrity_verified: false` and `in_game_load_tested: false`.

## Rich systems and exact blockers

| System | Coverage and remaining evidence |
| --- | --- |
| Growth points and gems | Individual edits implemented; no EXP allocation, leveling, fusion/spending transaction or reward generation |
| Other balances | Crystal/ticket candidate bytes inspected; native setter or field-specific console edited-load evidence needed |
| Officer identity/names | Standard/internal indices inspected; exact PS3 roster-ID/name table needed |
| Five officer stats | Published offsets inspected; native PS3 setters or controlled edited-load/action pairs needed for natural bounds and promotion/upgrade allocation dependencies |
| Level, EXP, proficiency, skills, promotions | Stored progression inspected; coherent thresholds, reset/reward flags and skill prerequisites unqualified |
| Weapons/fusion/equipment | Existing IDs, slots, reinforcement and attached IDs/ranks inspected; PS3 descriptor ownership, ranked/binary semantics, natural bounds, compatibility and equipped references need native routines or controlled equip/fuse pairs |
| Attribute orbs | 58 candidate balance bytes inspected without guessed names; ID catalogue, acquisition flags and field-specific integrity/load evidence required |
| Crafting materials | 295 candidate quantities in seven spans inspected; holes/padding preserved. Ordered names, stock limits, discovery/recipe flags and acquisition dependencies unqualified |
| Mounts/equipped items | Preserved; ownership/equip references, enhancement and unlocked-slot prerequisites need controlled equip/acquisition pairs |
| Relationships/companions | Preserved; directed/symmetric identity, support thresholds and flags need controlled bond changes |
| Story, stages, collections | Preserved separately; campaign/Gauntlet identity, unlock/reward flags, keystones/allies, Duel cards, gallery/music/movie/costume bits need controlled action pairs |
| Other regions/editions | Rejected by exact context; genuine fixtures and independent region/revision qualification needed |
| Integrity outside resources | No global checksum-absence claim; native PS3 serializer/loader or controlled corruption/reload evidence required |
| Actual PS3 edited loading | Not performed here; public resource report is external evidence, not a local test |
