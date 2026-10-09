"""Independently curated PC content identities; provenance in GAME_MECHANICS.md.

No assets, samples or third-party implementations are bundled. Unknown IDs stay
unnamed. Costume association is not a claim of ownership or equipped state.
"""
PW3_CHARACTER_NAMES = {
    0:'Luffy', 1:'Zoro', 2:'Nami', 3:'Usopp', 4:'Sanji', 5:'Chopper', 6:'Robin',
    9:'Ace', 10:'Hancock', 22:'Perona', 26:'Law', 28:'Tashigi', 36:'Shanks',
    38:'Zoro (post-timeskip)', 39:'Nami (post-timeskip)', 43:'Robin (post-timeskip)',
}
DW8_ATTRIBUTE_NAMES = {7:'Velocity', 41:'Comet'}
PW3_COSTUME_ASSOCIATIONS = ((0, 7, 22), (1, 5, 23), (2, 6, 27), (2, 7, 30), (2, 8, 7), (3, 3, 25), (4, 1, 24), (5, 1, 26), (6, 2, 28), (9, 3, 29), (10, 1, 31), (10, 2, 20), (10, 3, 16), (10, 4, 5), (22, 1, 21), (22, 2, 17), (22, 3, 6), (26, 2, 2), (28, 2, 8), (36, 1, 9), (38, 1, 12), (39, 1, 18), (39, 2, 14), (39, 3, 3), (41, 1, 13), (43, 1, 19), (43, 2, 15), (43, 3, 4))


def record_label(game_id, slot, group):
    if group == 'Weapon attributes':
        return f'Weapon slot {slot:04}'
    if game_id == 'pw3':
        name = PW3_CHARACTER_NAMES.get(slot - 1)
        return f'{name} / {slot:02}' if name else f'Character slot {slot:02}'
    return f'Officer slot {slot:02}'
