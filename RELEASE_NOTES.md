# Universal Koei Tecmo Save Editor v1.4

This update adds Dynasty Warriors: Origins to the game library and makes it easier
for contributors to add new games.

## New in v1.4

- Origins Steam PC: edit Gold (0–999,999) and base-game Skill Points (0–999).
- Edit the separate DLC Skill Point balance (0–999) on supported revision 29 saves.
- Edit existing bond levels and training counts, provincial peace, and qualified
  existing weapon reinforcement from +0 up to +99. Max preserves training counts,
  unusual values, weapon identities, traits and equipment references.
- Manually mark 35 supported battle-clear history flags as cleared. Already
  cleared history cannot be reset; history flags are excluded from Max and do
  not advance the active campaign, establish endings or grant rewards.
- Support native Origins slot revisions 16, 17 and 29, including save integrity,
  backups, Undo, Review Changes and Save As.
- Find fields by name, group or record in scalar editors; Max Visible Fields
  applies to the filtered rows while hidden pending edits remain staged.
- Remember the selected Light/Dark appearance across application restarts.
- DW3 weapon bonuses now use stat names such as Attack, Luck and Musou in
  selection menus and change reviews.
- Add a documented adapter interface, starter template and shared tests for new
  game integrations.

## Supported games

- Dynasty Warriors 3: Complete Edition Remastered: officers, items, weapons,
  bodyguards, unlocks, Musou stories, collections and Huanglong Elixirs.
- Dynasty Warriors: Origins: Gold, base-game/DLC Skill Points, existing bonds,
  provincial peace, eligible weapon reinforcement and manual battle-clear history.
- Dynasty Warriors 4 Hyper: officers, weapons, items, bodyguards and difficulty.
- Dynasty Warriors 8: Xtreme Legends Complete Edition: resources, officer stats
  and existing weapon attribute ranks.
- One Piece: Pirate Warriors 3: character stats, special bars and skill slots.
- Dynasty Warriors 4: Xtreme Legends (USA PS2): supported `.psu` save exports.
- Atelier Sophie 2 (Steam PC 1.08 layout): item/equipment quality and alchemy EXP.

## How to run

Download the Windows EXE, or extract the Windows ZIP and run
`UniversalKoeiTecmoSaveEditor-v1.4.exe`. No Python or installation is needed.
Select your game, open a separate save copy, make your edits and choose **Save As**.
Keep an untouched backup outside the live save folder.

For Origins, open a copied `SLOT0000.dat` through `SLOT0008.dat`; `USER.dat` is
system data. Bond events and reward claims, character/weapon XP, learned skills,
active story progression, endings and unlock flags remain unchanged. Weapon editing
changes only qualified reinforcement levels; empty and reserved records are preserved.
