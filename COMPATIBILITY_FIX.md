# v0.3.2 save compatibility fix

Thanks to **GoooD1** for reporting the opening error and supplying a save
that made it reproducible.

## Confirmed cause

v0.3.1 required exactly four records in `GuardDataArray`, matching the original
development sample. The reported save has two complete `GuardSaveData` records.
Its supported Unreal header, trailer and other checked array sizes match the
original sample. Requiring four bodyguard teams was an editor assumption, not
an established format requirement.

The parser now requires the exact supported array/record type, a fully parsed
record list and a matching serialized count. Each saved team retains its field,
growth and equipment validation. Team index checks and equipment planning use
the actual saved records. The editor does not add teams or change their names,
order, member names, appearance, type, gender or empty flags.

## Existing bonuses versus authored bonuses

The reported save also contains an Iron Crossbow with Attack +1. It has one
known normal bonus and otherwise valid serialized fields. This bonus falls
outside the conservative ranged-weapon drop profile verified for editing.
The supplied save alone does not establish how the bonus was obtained or
prove broader bodyguard fusion rules.

Reading an existing weapon no longer treats every out-of-profile bonus as
structural corruption. Distinct positive normal bonuses with the supported
saved representation can be displayed. Copies without a verified editing
profile are clearly labeled **view-only**. Their bonus controls are disabled,
direct bonus changes are refused, and bulk maximum actions preserve their
complete weapon records. Collection templates are not manufactured from them.

Acquiring weapons or changing supported copies still uses the same strict
family, tier, value and slot limits. Duplicate bonuses, nonpositive normal
values, rare inventory items in weapon bonus slots, malformed structures,
wrong inventory identities and invalid equipment references remain errors.

## Validation and privacy

Regression tests cover two- and four-team saves, unchanged encrypted round
trips, edits and safe rejection of absent team indexes. The private supplied
saves remain outside the source and release packages. Published tests allow
an explicit optional `DW3_TEST_REPORTED_SAVE` path for the reported fixture.

The owner reported in-game success with v0.3.1. In-game acceptance of this new
compatibility update is still awaiting player feedback; binary validation
does not establish every possible game behavior.
