# Save compatibility changes in v0.7

Two independently supplied saves exposed a shared design error in the older
editor: observed counts and conservative rules for creating new values were
being applied as universal rules for reading existing saves.

## Confirmed failures

- A naturally expanded unique-weapon array has 104 complete records. Slot 103
  contains Ziluan's fifth weapon, `EWeaponID::WeaponID_192`. The earlier parser
  demanded exactly 84 records. Native acquisition uses `WeaponID - 89` for the
  unique slot and grows the array through that index. Ziluan's fourth weapon
  belongs at slot 102, and his fifth at slot 103.
- Another save has a bodyguard team with Merit 45,228 and six growth levels
  `[0, 1, 11, 1, 3, 1]`. Its allocated points total 15, within that Merit's
  15-point budget. Bow/Moveset level 3 exceeds a gate for allocating new points
  at that Merit. Applying that gate to an already saved team prevented opening
  the entire file. Existing levels must be read separately from new allocations.

## Structural checks versus edit rules

The parser verifies the encrypted envelope, padding, supported Unreal tagged
serialization, save class, complete property payloads, array lengths matching
their actual contents, types, scalar sizes, bool encodings and duplicate named
fields. Negative counts, truncated records and incompatible serialization still
fail. UE5 engine build numbers can differ when the known serialization contract
remains the same; a new serialization format is not blindly accepted.

Top-level arrays carry their own lengths. Initial sizes (50 officers, 500 regular
weapon slots, 84 unique slots and so on) are documentation, not read-time validity
rules. Known records can be edited when present. Reserved, additional and unknown
records are preserved. Controls bound their indexes by the actual saved arrays.

Saved gameplay values outside the verified authoring profile produce compatibility
notes instead of a blanket damaged-save error. Unknown weapon profiles are view-only.
Writers validate new values and changed references; an unusual untouched team or
inventory entry cannot invalidate an unrelated officer stat change. Unknown data
is never silently normalized on opening or unchanged re-saving.

Bodyguard Merit increases preserve allocated HP/Attack/Defense/Bow levels and
advance earned Count/AI. Explicit growth changes still enforce the shared budget
and allocation gates. Unsupported growth shapes remain view-only.

## Integrity and limits

Edits patch the parsed tagged properties, regenerate affected property sizes and
the big-endian envelope length, restore zero padding and re-encrypt with the
existing AES-256-ECB codec. The output is parsed again before writing. Unknown
headers, properties, timestamps, reserved records and unrelated payloads stay
byte-identical. A no-op serialization must reproduce the entire encrypted input.

Automatic backups, manifest verification, temporary output verification, atomic
replacement and concurrent-write detection remain enabled. Live saves and Steam
Cloud paths remain blocked.

This removes count-dependent failures across the known arrays; it cannot promise
support for every future game serialization change. An unrecognized binary
structure is refused safely rather than rewritten speculatively. A save that
already contains inconsistent gameplay data is preserved, not automatically repaired.

## Community reports

Thanks to OrdinalSumo for the Ziluan report and feature requests, Domenikus for
reporting the unique-array opening error, and revidwi for the bodyguard-growth
save. Earlier reports from GoooD1 and austinkun remain covered by regression tests.
