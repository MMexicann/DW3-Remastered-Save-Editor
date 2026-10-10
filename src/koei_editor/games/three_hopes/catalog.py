"""Named format facts from async-amethyst/few2-010-binary-templates.
Commit 9b6e9946e5a33e182f80fbe3553e7c2afbebbdcb.
MIT License

Copyright (c) 2022 SilentLuna

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CHARACTERS = {0: 'Byleth (male)', 1: 'Byleth (female)', 2: 'Edelgard', 3: 'Dimitri', 4: 'Claude', 5: 'Hubert', 6: 'Ferdinand', 7: 'Linhardt', 8: 'Caspar', 9: 'Bernadetta', 10: 'Dorothea', 11: 'Petra', 12: 'Dedue', 13: 'Felix', 14: 'Ashe', 15: 'Sylvain', 16: 'Mercedes', 17: 'Annette', 18: 'Ingrid', 19: 'Lorenz', 20: 'Raphael', 21: 'Ignatz', 22: 'Lysithea', 23: 'Marianne', 24: 'Hilda', 25: 'Leonie', 26: 'Seteth', 27: 'Flayn', 28: 'Hanneman', 29: 'Manuela', 30: 'Gilbert', 31: 'Alois', 32: 'Catherine', 33: 'Shamir', 34: 'Cyril', 35: 'Jeralt', 36: 'Rhea', 37: 'Sothis', 38: 'Kronya', 39: 'Solon', 40: 'Thales', 41: 'Cornelia', 42: 'Death Knight', 43: 'Kostas', 44: 'Lonato', 45: 'Miklan', 46: 'Randolph', 47: 'Flame Emperor', 48: 'Anna', 49: 'Jeritza', 50: 'Rodrigue', 51: 'Judith', 52: 'Nader', 53: 'Monica', 54: 'Lord Arundel', 55: 'Tomas', 56: 'Nemesis', 58: 'Seiros', 100: 'Yuri', 101: 'Balthus', 102: 'Constance', 103: 'Hapi', 110: 'Shez (male)', 111: 'Shez (female)', 112: 'Holst', 116: 'Gatekeeper', 117: 'Arval', 140: 'Arval2'}

WEAPONS = {6: 'Iron Sword', 7: 'Steel Sword', 8: 'Silver Sword', 9: 'Brave Sword', 10: 'Killing Edge', 11: 'Training Sword', 12: 'Iron Lance', 13: 'Steel Lance', 14: 'Silver Lance', 15: 'Brave Lance', 16: 'Killer Lance', 17: 'Training Lance', 18: 'Iron Axe', 19: 'Steel Axe', 20: 'Silver Axe', 21: 'Brave Axe', 22: 'Killer Axe', 23: 'Training Axe', 24: 'Iron Bow', 25: 'Steel Bow', 26: 'Silver Bow', 27: 'Brave Bow', 28: 'Killer Bow', 29: 'Training Bow', 30: 'Iron Gauntlets', 31: 'Steel Gauntlets', 32: 'Silver Gauntlets', 33: 'Training Gauntlets', 34: 'Levin Sword', 35: 'Bolt Axe', 36: 'Magic Bow', 37: 'Javelin', 39: 'Spear', 41: 'Short Axe', 42: 'Tomahawk', 43: 'Longbow', 45: 'Armorslayer', 46: 'Rapier', 47: 'Horseslayer', 48: 'Hammer', 49: 'Blessed Lance', 50: 'Blessed Bow', 51: 'Devil Sword', 52: 'Devil Axe', 53: 'Wo Dao', 54: 'Crescent Sickle', 55: 'Swordof Seiros', 56: 'Swordof Begalta', 57: 'Swordof Moralta', 58: 'Cursed Ashiya Sword', 59: 'Swordof Zoltan', 60: 'Thunderbrand', 61: 'Blutgang', 63: 'Lanceof Zoltan', 64: 'Lanceof Ruin', 65: 'Areadbhar', 66: 'Luin', 67: 'Spearof Assal', 68: 'Scytheof Sariel', 69: 'Arrowof Indra', 70: 'Freikugel', 71: 'Crusher', 72: 'Axeof Ukonvasara', 73: 'Axeof Zoltan', 74: 'Tathlum Bow', 75: 'The Inexhaustible', 76: 'Bowof Zoltan', 77: 'Failnaught', 78: 'Dragon Claws', 79: 'Mace', 80: 'Athame', 81: 'Ridill', 82: 'Aymr', 83: 'Dark Creator Sword', 84: 'Venin Edge', 85: 'Venin Lance', 86: 'Venin Axe', 87: 'Venin Bow', 88: 'Mercurius', 89: 'Gradivus', 90: 'Hauteclere', 91: 'Parthia', 92: 'Killer Knuckles', 93: 'Aura Knuckles', 94: 'Rusted Iron Sword', 95: 'Rusted Steel Sword', 96: 'Rusted Silver Sword', 97: 'Rusted Brave Sword', 98: 'Rusted Mercurius', 99: 'Rusted Iron Lance', 100: 'Rusted Steel Lance', 101: 'Rusted Silver Lance', 102: 'Rusted Brave Lance', 103: 'Rusted Gradivus', 104: 'Rusted Iron Axe', 105: 'Rusted Steel Axe', 106: 'Rusted Silver Axe', 107: 'Rusted Brave Axe', 108: 'Rusted Hauteclere', 109: 'Rusted Iron Bow', 110: 'Rusted Steel Bow', 111: 'Rusted Silver Bow', 112: 'Rusted Brave Bow', 113: 'Rusted Parthia', 114: 'Rusted Iron Gauntlets', 115: 'Rusted Steel Gauntlets', 116: 'Rusted Silver Gauntlets', 117: 'Rusted Dragon Claws', 118: 'Sublime Creator Sword', 127: 'Vajra Mushti', 128: 'Tattered Iron Tome', 129: 'Iron Tome', 130: 'Defenders Tome', 131: 'Steel Tome', 132: 'Exorcists Tome', 133: 'Heretics Tome', 134: 'Killer Tome', 135: 'Inverted Tome', 136: 'Silver Tome', 137: 'Brave Tome', 138: 'Foreign Tome', 139: 'Abyssal Tome', 140: 'Sages Tome', 141: 'Scholars Tome', 142: 'Wind Callers Genesis', 143: 'Scrollof Talos', 144: 'Amalthea', 145: 'Hrotti', 146: 'Ichor Scroll', 147: 'Suttungrs Mystery', 148: 'Jarngreipr', 149: 'Labraunda', 150: 'Dahaka', 151: 'Knight Captains Sword', 153: 'Shamshir', 154: 'Training Tome', 155: 'Tattered Steel Tome', 156: 'Tattered Silver Tome', 157: 'Tattered Brave Tome', 158: 'Tattered Scholars Tome', 159: 'Rusted Killing Edge', 160: 'Rusted Killer Lance', 161: 'Rusted Killer Axe', 162: 'Rusted Killer Bow', 163: 'Rusted Killer Knuckles', 164: 'Tattered Killer Tome', 166: 'Wingthresher', 167: 'Heavy Spear', 168: 'Flycatcher', 169: 'Wolf Fangs'}
