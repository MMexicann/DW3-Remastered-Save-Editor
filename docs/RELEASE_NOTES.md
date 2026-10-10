# Universal Koei Tecmo Save Editor v1.6

More games and platforms, clearer equipment/inventory views and an organized
source package, with Mexican's branding, Light/Dark themes, backups, Undo and
Review Changes retained.

- **Dynasty Warriors 6, PC:** named playable-officer unlocks, existing horse
  combat stats and searchable officer, weapon and horse records.
- **Dynasty Warriors 9 Empires, PC:** existing item quantities and searchable
  inventory/custom-officer records in SYSTEMDATA saves.
- **Warriors Orochi Z, PC:** Stock EXP, officer base attack, existing weapon attack bonuses,
  attribute capacity and owned attribute ranks, with searchable records.
- **Warriors All-Stars, PC:** available gold and existing material quantities in campaign slots,
  with separate lifetime-gold inspection.
- **Hyrule Warriors, Wii U:** rupees, existing materials/map cards, weapon stars
  and ordinary skill-seal KO counters, with named equipment inspection.
- **Hyrule Warriors: Age of Calamity, Switch:** rupees, discovered materials,
  trophies and reports, existing weapon protection and named seal inspection.
- **Hyrule Warriors: Definitive Edition, Switch:** rupees, existing named
  material quantities and searchable characters, fairy food and weapons.
- **Fire Emblem Warriors, Switch:** gold, existing materials, weapon stars
  and ordinary skill-seal KO counters, with named character/weapon inspection.
- **Dynasty Warriors 7, PS3:** gold and officer stats/skill points for US/EU
  decrypted exports.
- **Samurai Warriors 4, PS3:** gold and eight gems, with level/EXP proficiency
  inspection for US decrypted exports.
- **Dynasty Warriors 7 Empires, PS3:** system bonus points for US decrypted
  system exports.

The game library groups entries by platform and defaults to Windows PC.
Find records searches every inspector column. Source files now live in separate
game packages, shared utilities, documentation and build-tool folders, with a
supported-game list generated from the registry.

Download **UniversalKoeiTecmoSaveEditor-v1.6.exe** for the standalone Windows app,
or the **Windows ZIP** for the same executable and documentation. No Python
installation is needed. Open a separate save copy, review edits and use Save As.
Console editors use extracted/decrypted exports; export and reimport/resign PS3
saves with Apollo Save Tool.

From source with Python/Tk: `python -m pip install -e .`, then
`python -m koei_editor`.
