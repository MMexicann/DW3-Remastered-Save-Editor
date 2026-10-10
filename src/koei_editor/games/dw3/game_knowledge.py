"""Authored game-mechanics notes; research never activates an editing adapter.

See GAME_MECHANICS.md for the detailed evidence and inspected source commits.
No third-party tutorial, asset, trainer or sample save is bundled.
"""
NOTES = {
    'dw3': ('Dynasty Warriors 3 Remastered',
            'The complete existing editor is retained.\n\n'
            'Native evidence in this project distinguishes permanent officer stats from equipment bonuses. '
            'Merit caps at 99,999; permanent Life/Musou at 250; Attack/Defense at 150. '
            'Item and weapon limits follow their shipped tables and reachable drop/fusion rules.\n\n'
            'Bodyguard point allocation is separate from automatic squad count and AI progression. '
            'Count thresholds are 25,000/50,000/75,000 Merit; AI thresholds are 30,000/60,000/90,000. '
            'The editor preserves those existing dependency rules.\n\n'
            'Musou completion follows each officer’s route. Three officers have no route. '
            'Story flags do not recreate battle records, scores, clear times or achievement events. '
            'Huanglong Elixirs cap at 999 and a first clear awards three.\n\n'
            'Evidence: verified_limits.json, item_limits.json, weapon_bonus_rules.json, '
            'bodyguard_growth.json and progression_routes.json in this project.'),
    'dw8xl': ('Dynasty Warriors 8 Xtreme Legends Complete Edition',
              'Available PC edits: resources, numbered permanent officer stats, four weapon-action '
              'compatibilities, qualified existing weapon affinity IDs and ranked attributes. '
              'Loading edited copies in the game remains untested.\n\n'
              'Published PC runtime instruction signatures corroborate processing ceilings of 1,500 '
              'for Attack/Defense, 9,999,999 for Gold and 9,999 for the inspected facility-material path. '
              'These are processing ceilings, not proof that every officer naturally reaches them.\n\n'
              'Health 1,000 comes from published save patches. Gems now use the 9,999 normal inventory cap corroborated by two independent Steam guides. '
              'Health has also been reported by community guides, but has not been independently '
              'established here as a natural progression maximum. Max actions use published editing limits.\n\n'
              'Officer level and EXP are separate from leadership and leadership EXP. Stored stats are '
              'separate from battle floats, current gauges and temporary bonuses. Equipment or progression '
              'may recalculate stats; the exact triggers need controlled PC checks.\n\n'
              'Weapon compatibility is stored separately for Dash, Dive, Shadow Sprint and Whirlwind. '
              'The PC fixture contains 25/50/75/100 units; the published four-star patch writes 100. '
              'Individual edits accept only these four observed values. This is not weapon EXP, '
              'weapon attribute rank or skill unlocking, and Max preserves higher existing values.\n\n'
              'Existing populated weapons with observed affinity IDs 0/1/2 permit individual affinity '
              'edits; unknown affinities remain inspection-only. Affinity is excluded from Max. '
              'Heaven/Earth/Man numeric ID labels remain unverified.\n\n'
              'Weapons have identity, affinity and six attribute IDs/ranks. Skills distinguish enabled, '
              'rankable and rank values. Bodyguards distinguish current/max skill level, skill EXP and bonds. '
              'Ambition facilities also track invested materials, rank, supervisors, roster and capacity. '
              'Ally current skill levels, skill EXP, support-skill IDs and male/female bonds are '
              'inspected read only across the physical record pool without inferring ownership. '
              'Those relationships must be mapped before new equipment/unlock edits are enabled.\n\n'
              'Sources: koko-tsuu/dw8xl_save_converter; Apollo NPUB31449 patches; '
              'Hexorg/CheatEngineTables PC v1.0.0.7 native instruction signatures. '
              'Runtime addresses are not disk-save offsets.'),
    'pw3': ('One Piece: Pirate Warriors 3',
            'Available PC edits: character record health, Attack/Defense, special bars and skill slots. '
            'Currency, level and EXP inspection is read only; medal/story editing is unavailable. '
            'Loading edited copies in the game remains untested.\n\n'
            'Two genuine PC saves corroborate the progression fields. Observed examples: '
            'level 1 / XP 0 / health 2,000; level 50 / XP 1,000,000 / health 5,000; '
            'level 100 / XP 3,000,000 / health 6,000. The observed health curve is inferred from saves, '
            'not proven from game code.\n\n'
            'Published boosts of 10,000 Health and 1,000 Attack/Defense exceed the observed natural '
            'progression values. Published patches explicitly warn that stat and bar boosts reset on '
            'level-up. Max uses these editing limits; it does not grant levels or progression upgrades.\n\n'
            'Special bars and skill slots do not follow level alone. Observed ranges are 1–4 bars and '
            '1–6 slots. Several record pairs share level/EXP but differ in stats, suggesting related '
            'variants; numbered slots avoid assigning unverified identities.\n\n'
            'The published money patch changes two fields. New PC runtime evidence names a corresponding adjacent pair current/earned Beli, but its exact save-base equivalence and legitimate cap remain uncorroborated. '
            'Beli stays read only. Coin rows also contain two independent bytes, so they cannot safely '
            'be treated as one 16-bit inventory count.\n\n'
            'Needed pairs: one level-up, one bar/slot upgrade, coin purchase and limit-break purchase, '
            'plus money earned/spent with displayed values.\n\n'
            'Sources: Ceraph1216/pirateWarriors3Save; gamesaves/OPPW3; Apollo NPEB02211 patches.'),
    'origins': ('Dynasty Warriors: Origins',
                'Research copy tools only. No gameplay save parser, field edits or numeric maxima are verified.\n\n'
                'Do not reuse DW3 or DW8 progression rules. A genuine Steam DLC save is available, '
                'but the player save encryption and integrity model remain unresolved.\n\n'
                'The public LINKDATA tools decode assets and stage scripts. Their unit courage “level” '
                'argument is an NPC/stage value, not player rank or weapon proficiency.\n\n'
                'Needed: a verified save decoder, then separate version/DLC-labelled pairs for proficiency, '
                'rank, skill purchase, Battle Art acquisition/equip, gem creation/equip, horse '
                'acquisition/equip, bond growth and story transitions.\n\n'
                'Sources: VdustR/game-save-dwo-d4h and Kelebek1/dwo. No player cap is inferred from asset labels.'),
    'berserk': ('Berserk and the Band of the Hawk',
                'PC research candidate; no verified PC save editor.\n\n'
                'Published PC tutorial translations describe character-level growth for vitality, '
                'Attack, Defense and Technique, and action-level unlocks at particular character levels. '
                'A numeric stat alone is not the whole progression state.\n\n'
                'Accessories support up to four inherited abilities and reinforcement through +9. '
                'Ability upgrades use matching-color materials; promotion and fusion also involve item '
                'class, consumed accessories and inherited-ability selection.\n\n'
                'Endless Eclipse floor rewards are per character, while desire completion is shared. '
                'Ongoing health/items/progress have separate persistence rules. These need distinct '
                'save fields; one “complete everything” flag would not model them.\n\n'
                'These tutorial semantics do not establish PC offsets, integrity or a character-level cap. '
                'Source: ayozetr/berserk-band-of-the-hawk-es, PC Steam tutorial translation entries.'),
    'pw4': ('One Piece: Pirate Warriors 4',
            'PC research candidate; no verified disk-save editor.\n\n'
            'Published PC runtime probes distinguish committed Beli rewards, medal/item IDs and counts, '
            'new-item flags and crew-point totals. Crew-point display values can differ from raw deltas. '
            'Soul reward fields remain explicitly unresolved in the source.\n\n'
            'Resource names and memory pointers are not proof of serialized save fields. Build/DLC-specific '
            'growth and Soul Map caps still need verification.\n\n'
            'Sources: Glubus/oppw4-sdk and Glubus/oppw4-data; runtime reward research from May 2026.'),
    'dw8_empires': ('Dynasty Warriors 8: Empires',
                    'PC research candidate; no verified native PC save sample in this workspace.\n\n'
                    'Published PC runtime structures distinguish officer Merit from Level; kingdom, '
                    'location and rank from virtue, friendship, fatigue and leadership; equipment '
                    'ownership from equipped indices; and six equipped stratagems from battle cooldowns. '
                    'Bonus points and lifetime earned points are separate.\n\n'
                    'These are different dependencies from DW8 XL. Reusing its parser or Max preset '
                    'would not preserve the Empires campaign model. Published patch titles can disagree '
                    'with their encoded values and do not establish PC caps.\n\n'
                    'Source: Hexorg/CheatEngineTables PC v1.0.0.4 runtime structure descriptions.'),
    'sw4ii': ('Samurai Warriors 4-II',
              'PC research candidate; no verified disk-save editor.\n\n'
              'Published PC runtime structures separate character EXP/level and stored/battle stats. '
              'Weapons distinguish rank, current/max level and eight ability IDs with eight ability '
              'levels. Mounts also have rank/current/max level and separate ability flags. '
              'Five colored strategy-tome balances are distinct resources.\n\n'
              'These observations do not establish normal caps or PC save offsets. Original 4, 4-II '
              'and 4 DX require independent format verification.\n\n'
              'Source: Hexorg/CheatEngineTables PC v1.0.0.3 runtime structure descriptions.'),
    'dw4hyper': ('Dynasty Warriors 4 Hyper (PC)',
                 'Available in the PC library using a published native format. The implementation '
                 'has procedural tests; no genuine PC copy or edited in-game load has been validated here.\n\n'
                 'The raw save.dat is 69,568 bytes, with a byte-sum checksum and no encryption. '
                 'This is the Windows Hyper edition. The linked DW4 XL editor instead handles PS2 '
                 'memory-card exports and is excluded from this PC application.\n\n'
                 'The candidate maps 42 named standard officers, playable flags, Life/Musou/Attack/Defense, '
                 'character EXP, weapon EXP, 32 items, four bodyguard teams\' points and three difficulties. '
                 'Names, equipped gear and existing custom characters are inspected without changes.\n\n'
                 'Item level 0 means locked; normal items use levels 1–20, orbs 1–4, and rare items '
                 'use ownership 0/1. Weapon EXP normally ranges through 36,000; 36,001 is the published '
                 'special level-10 weapon. Hyper has no level-11 weapons.\n\n'
                 'Stats use byte storage and EXP/points use 16-bit storage. Their normal caps and '
                 'bodyguard growth thresholds are unresolved, so bulk Max excludes them and difficulty. '
                 'Only playable flags, item limits and the special weapon EXP are bulk Max targets. '
                 'Custom creation, equipment writes, rankings and suspended battle editing are unavailable.\n\n'
                 'Source: talkative-platano/dw4hyper-save-editor, commit 3638c8dc23d2607b862a1105bfc9806e69d9e871. '
                 'Needed: a copied native PC save.dat, edition/build labels, displayed values and an in-game reload.'),
    'dw4xl_ps2': ('Dynasty Warriors 4 Xtreme Legends (PS2, USA)',
                  'Separate PS2 library entry using a published SLUS-20812 format. Independent genuine-export '
                  'and in-game validation remain pending. PCSX2 exports are PS2 saves.\n\n'
                  'Open only a copied .psu memory-card export containing BASLUS-20812. Its inner '
                  'gameplay file is 34,064 bytes, version 3, with a 16-bit byte-sum checksum. '
                  'The parser walks directory entries and preserves export metadata, icons and padding.\n\n'
                  'Officer stats and character points differ from weapon EXP. XL has five difficulties '
                  'and special Lv.10/Lv.11 weapon values 36,001/36,002. Its 41-item table includes '
                  'nine XL additions; item level 0 means locked, and rare items use ownership 0/1.\n\n'
                  'Max targets published item limits and Lv.11 weapon EXP. Stats, character/bodyguard '
                  'points and difficulty are excluded because normal caps remain unverified. '
                  'Equipped gear, names, rankings and unrelated data stay unchanged.\n\n'
                  'Source: talkative-platano/dw4xl-save-editor, commit b3ea895c6e854accd6860fd51ce69aeb024f53e9. '
                  'See DW4_PLATFORM_FORMATS.md for exact platform boundaries and sample needs.'),
    'dw6_original': ('Dynasty Warriors 6 (PC)',
                     'Native PC plaintext-reader lead; no verified editor in this application.\n\n'
                     'The published reader describes 41 officers, 168-byte records, eight weapons per '
                     'officer, skill and unlock masks, level/EXP and horse records. Its author documents '
                     'successful in-game edits. The source reads four bytes before several values; '
                     'their actual offsets differ from the named seek positions.\n\n'
                     'Weapon power is additive and skills are bitfields; changing identity can affect '
                     'inventory relationships. Community level-50 and horse-stat observations are '
                     'mechanics leads rather than verified save caps.\n\n'
                     'No genuine fixture, accepted size, title header or integrity rules are established '
                     'here. No writes are enabled from screenshots or reader offsets alone. '
                     'Needed: native PC save.dat plus single-change officer/weapon/horse pairs.\n\n'
                     'Source: cnopt/dynastywarriors6-reverse-engineering, commit f2152f67b031091a0268154203d25fa9f65d2664.'),
    'dw9_original': ('Dynasty Warriors 9 (PC)',
                     'Public PC save link found; download blocked. No native PC save decoder or editor verified.\n\n'
                     'The inspected PC custom-gem guide describes gem type and four separate bonus '
                     'type/value pairs, including adjacent duplicate runtime records. Gem identity, '
                     'element, rarity and bonuses are separate. Values may occupy more than one byte.\n\n'
                     'Guide signatures are patch dependent and address process memory. They cannot '
                     'establish disk offsets. Empires-only gem IDs must not be assigned to base DW9.\n\n'
                     'Needed: copied gameplay files from Documents/KoeiTecmo/Dynasty Warriors 9 for Steam '
                     'with full/trial, patch and DLC labels; purchase, gem/equip, officer progression and '
                     'story-completion pairs. The exact gameplay basename remains unverified.\n\n'
                     'Source: Steam PC guide 1367429596 and save thread 691996723218915728.'),
    'dw9_empires': ('Dynasty Warriors 9 Empires (PC)',
                    'Independent research candidate; no native PC save or disk decoder verified.\n\n'
                    'Six reputation tracks jointly gate titles. A campaign title differs from a CAW '
                    'template\'s Way of Life, and new campaigns reset progression.\n\n'
                    'Artifacts combine five rarities and seven elements. Rarity controls gem slots '
                    'and bounds weapon rarity; gem bonuses and elemental increases differ. Four Secret '
                    'Plans can be equipped, with ownership and acquisition stars separate from effects.\n\n'
                    'Reported proficiency milestones are 0/500/1,000 for one/three/big stars. '
                    'Preferred-weapon defaults, campaign gains and child inheritance are separate; '
                    'these observations are not validated save offsets or enforced caps.\n\n'
                    'Public hex and .caw import/export tools operate on a running process. Opening '
                    'or saving CAW screens can recalculate visible stats and other derived values. '
                    'A save editor needs the canonical serialized records and integrity model.\n\n'
                    'Needed: copied system data, campaign slot and known CAW template from '
                    'Documents/KoeiTecmo/Dynasty Warriors 9 Empires, with resource, reputation, '
                    'Secret Plan, gem and proficiency single-change pairs.\n\n'
                    'Sources: Steam PC guides 2705195639, 2732095060 and 3175407939.'),
    'wo3': ('Warriors Orochi 3 Ultimate Definitive Edition (PC)',
            'Public annotated PC archive found; download blocked. No PC save editor verified.\n\n'
            'Promotion, character level, accumulated EXP and growth-point allocation are distinct. '
            'Upgrade stones, weapon crafting, attribute ranks, equipment slots and character bonds '
            'also have separate progression rules. Console Ultimate and PC Definitive layouts '
            'require comparison before any field transfers.\n\n'
            'Needed: copied native SAVEDATA.BIN, build/DLC labels and promotion, crafting, '
            'bond and upgrade-stone before/after pairs. See PC_RESEARCH_RETRY.md for the public archive.'),
    'p5s': ('Persona 5 Strikers (PC)',
            'Research byte-stream codec only. A published 32-byte PC screenshot vector is reproduced; '
            'no complete PC save or gameplay editor has been validated.\n\n'
            'Independent stream recovery uses known version bytes and a low-24-bit stream class. '
            'It requires no account identifier. Read-only inspection checks the published PC size, '
            'ten bounded slot spans and layout marker. The checksum model remains unverified.\n\n'
            'The source converter handles names and slots differently between PC and console. '
            'The separate public gameplay editor is console based and its PC compatibility is '
            'untested; its fields are not enabled here.\n\n'
            'Needed: an unchanged copied native PC SAVEDATA.BIN, build labels and known in-game slot '
            'values to validate incoming integrity before considering gameplay writes.\n\n'
            'Source: zarroboogs/p5spc.saveutil, commit 2462a2043aba3bc551d2eb6b732a81d2374aa826.'),
}


def guide(game_id):
    title, text = NOTES.get(game_id, NOTES['dw3'])
    return title, text + ('\n\nDetailed provenance and sample requirements: GAME_MECHANICS.md, KOEI_FORMATS.md and PC_RESEARCH_RETRY.md. '
                         'Steam community guides were inspected; official manual downloads and wiki requests were blocked in the current '
                         'research environment. Unknown caps and dependencies remain unverified.')


def show_guide(root, game_id='dw3', font_family='Segoe UI'):
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    dialog = tk.Toplevel(root)
    dialog.title('Game Mechanics & Editing Limits')
    dialog.geometry('920x670')
    heading = ttk.Frame(dialog, padding=16)
    heading.pack(fill='x')
    selection = tk.StringVar(root, value=NOTES.get(game_id, NOTES['dw3'])[0])
    choices = ttk.Combobox(heading, textvariable=selection, values=[value[0] for value in NOTES.values()],
                           state='readonly', width=65)
    choices.pack(side='left', fill='x', expand=True)
    ttk.Button(heading, text='Close', command=dialog.destroy).pack(side='right', padx=(12, 0))
    text = ScrolledText(dialog, wrap='word', padx=16, pady=12, font=(font_family, 11))
    text.pack(fill='both', expand=True, padx=16, pady=(0, 16))
    def populate(_event=None):
        key = next(key for key, value in NOTES.items() if value[0] == selection.get())
        text.configure(state='normal')
        text.delete('1.0', 'end')
        title, body = guide(key)
        text.insert('1.0', title + '\n\n' + body)
        text.configure(state='disabled')
    choices.bind('<<ComboboxSelected>>', populate)
    populate()
    return dialog
