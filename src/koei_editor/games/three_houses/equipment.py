"""Small independently transcribed set of ordinary weapon identity facts.

Public evidence: imouto1994/fe3h-editor, commit
5e4a73b71f28feb271ccdbc614ea934517c235b5, SaveEditor/Database.cs,
EssentialItems source comments. These are factual identities, not a copied
catalog or extracted game asset. They establish eligibility, not natural caps.
Unknown, unique, quest and DLC-dependent identities remain read only.
The revision-23 source hashcade/feth-save-editor core/Database.cs at commit
b9f53f0e01a3dd2cd24c96f97f1a829e51a1f00d independently retains these identity
comments; private inspected exports corroborate occupied records in both profiles.
"""
from types import MappingProxyType

ORDINARY_EQUIPMENT = MappingProxyType({
    131: 'Brave Sword+',
    132: 'Killing Edge+',
    137: 'Brave Lance+',
    138: 'Killer Lance+',
    143: 'Brave Axe+',
    144: 'Killer Axe+',
    149: 'Brave Bow+',
    150: 'Killer Bow+',
    153: 'Steel Gauntlets+',
    154: 'Silver Gauntlets+',
    168: 'Rapier+',
    175: 'Wo Dao+',
})
