"""Public weapon-rule boundaries; no save or installed game is required."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import officer_weapon_editor as w
from models import SaveError

class WeaponRuleTests(unittest.TestCase):
    def info(self):
        return {'owned':True,'array':'WeaponDataArray','weapon_id':6,'blue_limit':6,'blue_minimum':0,
                'skills':[{'id':None,'value':0} for _ in range(9)]}

    def test_weapon_caps_differ_from_equipped_item_caps(self):
        expected={0:24,1:24,2:90,3:90,4:30,5:60,6:60,7:60,8:60,9:60,10:30,11:30,12:30,25:48,26:30,27:18}
        self.assertEqual({i:max(w.allowed_values(self.info(),i)) for i in w.NORMAL_ITEMS},expected)

    def test_nonreachable_values_are_excluded(self):
        self.assertNotIn(19,w.allowed_values(self.info(),0))
        self.assertNotIn(22,w.allowed_values(self.info(),0))
        for value in (22,25,28,43):self.assertNotIn(value,w.allowed_values(self.info(),4))

    def test_stock_exception_is_local_and_exact(self):
        info=self.info();info.update(array='UniqueWeaponDataArray',weapon_id=116)
        self.assertIn(43,w.allowed_values(info,4))
        for value in (31,40,42,44):self.assertNotIn(value,w.allowed_values(info,4))

    def test_normal_count_duplicate_and_rare_boundaries(self):
        info=self.info();skills=[{'id':i,'value':1} for i in range(6)]+[{'id':None,'value':0} for _ in range(3)]
        self.assertEqual(w.validate_skills(info,skills),skills)
        for invalid in (skills[:6]+[{'id':6,'value':1}]+skills[7:],
                        skills[:6]+[{'id':0,'value':1}]+skills[7:],
                        skills[:6]+[{'id':40,'value':0}]+skills[7:]):
            with self.assertRaises(SaveError):w.validate_skills(info,invalid)
        info['blue_minimum']=1
        with self.assertRaises(SaveError):w.validate_skills(info,[{'id':None,'value':0} for _ in range(9)])

if __name__=='__main__':unittest.main()
