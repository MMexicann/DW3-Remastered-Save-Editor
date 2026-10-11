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
