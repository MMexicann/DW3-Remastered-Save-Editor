"""Native WO3 PC ordinary-item references, separate from acquisition/rank.

The packed officer serializer writes six signed selectors; the native equipment
menu checks the 64-bit ownership mask and rejects duplicate selectors. IDs
28..31 are the separate mount category and stay outside this control.
"""
from koei_editor.games.dw3.models import SaveError

ITEM_OWNERSHIP_OFFSET, ITEM_RANK_OFFSET, ITEM_COUNT = 0xD9AC, 0xD9B4, 64
EQUIPPED_ITEM_OFFSET, ITEM_SLOT_COUNT_OFFSET, EMPTY_ITEM = 38, 44, 255
MOUNT_IDS = frozenset(range(28, 32))


def owned_items(payload):
    mask = int.from_bytes(payload[ITEM_OWNERSHIP_OFFSET:ITEM_OWNERSHIP_OFFSET + 8], 'little')
    return tuple(identity for identity in range(ITEM_COUNT)
                 if identity not in MOUNT_IDS and mask & (1 << identity)
                 and int.from_bytes(payload[ITEM_RANK_OFFSET + 2 * identity:
                                            ITEM_RANK_OFFSET + 2 * identity + 2], 'little') > 0)


def qualified_slots(payload, officer_base):
    count = payload[officer_base + ITEM_SLOT_COUNT_OFFSET]
    if not 2 <= count <= 6:
        return 0
    selectors = payload[officer_base + EQUIPPED_ITEM_OFFSET:
                        officer_base + EQUIPPED_ITEM_OFFSET + 6]
    allowed = owned_items(payload)
    active = [identity for identity in selectors[:count] if identity != EMPTY_ITEM]
    if (any(identity not in allowed for identity in active)
            or len(active) != len(set(active))
            or any(identity != EMPTY_ITEM for identity in selectors[count:])):
        return 0
    return count


def options(payload):
    return ((EMPTY_ITEM, 'Unequipped'),) + tuple(
        (identity, f'Owned item ID {identity}') for identity in owned_items(payload))


def validate_selectors(original, changed, officer_base):
    count = qualified_slots(original, officer_base)
    if not count:
        raise SaveError('This officer has an unsupported existing item-equipment layout.')
    allowed = owned_items(original)
    selectors = changed[officer_base + EQUIPPED_ITEM_OFFSET:
                        officer_base + EQUIPPED_ITEM_OFFSET + count]
    active = [identity for identity in selectors if identity != EMPTY_ITEM]
    if any(identity not in allowed for identity in active):
        raise SaveError('Select an already owned ordinary item with an existing positive rank.')
    if len(active) != len(set(active)):
        raise SaveError('An officer cannot equip the same item in two slots. Unequip it first.')
