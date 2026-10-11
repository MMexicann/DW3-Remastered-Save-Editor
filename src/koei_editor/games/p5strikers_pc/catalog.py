"""Selected independently transcribed item-name/quantity-position facts.

Positions are relative to a native PC English slot, not executable addresses.
References and limitations are documented in docs/P5STRIKERS_PC_FORMAT.md.
No upstream program, cheat action or wholesale dataset is incorporated.
"""
# Public English Switch slot 1 starts at 0x88E52, identical PC body/name layout.
# This curated subset excludes recipes, valuables, incenses, equipment and IDs
# without a clear ordinary consumption/cooking role.
CONSUMABLES = (
    (0x869B2, 'Adhesive Bandage'), (0x869B8, 'Medicine'),
    (0x869DA, 'Devil Fruit'), (0x869DC, 'Life Stone'),
    (0x869DE, 'Bead'), (0x869E0, 'Bead Chain'),
    (0x869EE, 'Soul Drop'), (0x869F0, 'Snuff Soul'),
    (0x869F2, 'Chewing Soul'), (0x869F4, 'Soul Food'),
    (0x869F6, 'Soma'), (0x86A02, 'Revival Bead'),
    (0x86A04, 'Balm of Life'), (0x86A06, 'Rescue Pill'),
    (0x86A08, 'Resuscitation Pill'),
    (0x86AA2, 'Leblanc Coffee'), (0x86AA4, 'Gyutan Stew'),
    (0x86AA6, 'Salmon Bowl'), (0x86AA8, 'Leblanc Curry'),
    (0x86AAA, 'Miso Ramen'), (0x86AAC, 'Jingisukan'),
    (0x86AAE, 'Seafood Bowl'), (0x86AB0, 'Okinawa Soba'),
    (0x86AB2, 'Kyoto Curry'), (0x86AB4, 'Goya Chanpuru'),
    (0x86AB6, 'Goat Soup'), (0x86AB8, 'Churrasco'),
    (0x86ABA, 'Obanzai'), (0x86ABC, 'Okonomiyaki'),
    (0x86ABE, 'Crab Hot Pot'), (0x86AC0, 'Osaka Sushi'),
    (0x86AC2, 'Kushikatsu'), (0x86AC4, 'Master Coffee'),
    (0x86AC8, 'Master Curry'),
)
INGREDIENTS = (
    (0x86B06, 'Select Coffee Beans'), (0x86B08, 'Salmon'),
    (0x86B0A, 'Gyutan'), (0x86B0C, 'Carrot'),
    (0x86B0E, 'Onion'), (0x86B10, 'Pork'),
    (0x86B12, 'Rice'), (0x86B14, 'Flour'),
    (0x86B16, 'Miso'), (0x86B18, 'Lamb Meat'),
    (0x86B1A, 'Cabbage'), (0x86B1C, 'Tuna'),
    (0x86B1E, 'Egg'), (0x86B20, 'Beef'),
    (0x86B22, 'Cooking Awamori'), (0x86B24, 'Goya'),
    (0x86B26, 'Tofu'), (0x86B28, 'Goat Meat'),
    (0x86B2A, 'Kamo-Nasu Eggplant'), (0x86B2C, 'Crab'),
)

CHARACTERS = ('Protagonist', 'Ryuji', 'Morgana', 'Ann', 'Yusuke', 'Makoto',
              'Haru', 'Futaba', 'Sophia', 'Zenkichi')

# Selected consumable identities, individually cross-checked against the public
# worksheet and editor reference. Editing the stack does not apply the item.
INCENSES = (
    (0x869C6, 'Power Incense'), (0x869C8, 'Magic Incense'),
    (0x869CA, 'Guard Incense'), (0x869CC, 'Speed Incense'),
    (0x869CE, 'Luck Incense'), (0x869D0, 'HP Incense'),
    (0x869D2, 'SP Incense'),
)
REMEDIES = (
    (0x86A16, 'Hot and Sour Tea'), (0x86A18, 'Super Jolt'),
    (0x86A1A, 'Mental Floss'), (0x86A1C, 'Donut-Worry'),
    (0x86A1E, 'Soothing Towel'), (0x86A20, 'Wide Eye Drops'),
    (0x86A22, 'Repentance Ashes'), (0x86A24, 'Hiranya'),
    (0x86A26, 'Amrita Soda'),
)
SKILL_CARDS = (
    (0x871CA, 'Agi'), (0x871CC, 'Agilao'), (0x871CE, 'Agidyne'),
    (0x871D2, 'Maragi'), (0x871DA, 'Bufu'), (0x871DC, 'Bufula'),
    (0x871DE, 'Bufudyne'), (0x871E2, 'Mabufu'),
    (0x871EA, 'Zio'), (0x871EC, 'Zionga'), (0x871EE, 'Ziodyne'),
    (0x871F2, 'Mazio'), (0x871FA, 'Garu'), (0x871FC, 'Garula'),
    (0x871FE, 'Garudyne'), (0x87202, 'Magaru'),
    (0x8720A, 'Psi'), (0x87212, 'Mapsi'),
    (0x8721A, 'Frei'), (0x87222, 'Mafrei'),
    (0x8722A, 'Kouha'), (0x8723E, 'Eiha'),
    (0x87272, 'Dia'), (0x87278, 'Media'),
)

ITEM_GROUPS = (('Consumables', CONSUMABLES), ('Cooking ingredients', INGREDIENTS),
               ('Incenses', INCENSES), ('Ailment remedies', REMEDIES),
               ('Skill cards', SKILL_CARDS))
