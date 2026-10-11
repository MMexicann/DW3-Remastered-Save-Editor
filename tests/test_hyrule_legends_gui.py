"""Tk on copied procedural/genuine 3DS exports, not console game-load proof."""
import os
from pathlib import Path
import unittest
from koei_editor.games.hyrule_legends import parser as p
from koei_editor.games.hyrule_legends.editor import Editor
from tests.test_hyrule_legends import procedural_legends
from tests.test_hyrule_gui import GuiWorkflow


class LegendsGuiTests(GuiWorkflow,unittest.TestCase):
    backend=p;editor_type=Editor;fixture=staticmethod(procedural_legends)
    group,search,field,value='Weapon stars','Rod','weapon_1_stars',5


@unittest.skipUnless(os.environ.get('HYRULE_LEGENDS_COPY'),'Private native 3DS export absent')
class LegendsNativeGuiTests(GuiWorkflow,unittest.TestCase):
    backend=p;editor_type=Editor
    fixture=staticmethod(lambda:Path(os.environ['HYRULE_LEGENDS_COPY']).read_bytes())
    group,search,field,value='Resources','Rupees','rupees',123


class LegendsFairyGuiTests(GuiWorkflow,unittest.TestCase):
    backend=p;editor_type=Editor;fixture=staticmethod(procedural_legends)
    group,search,field,value='My Fairy','Name','fairy_1_name','Navi'


@unittest.skipUnless(os.environ.get('HYRULE_LEGENDS_COPY'),'Private native 3DS export absent')
class LegendsNativeFairyGuiTests(GuiWorkflow,unittest.TestCase):
    backend=p;editor_type=Editor
    fixture=staticmethod(lambda:Path(os.environ['HYRULE_LEGENDS_COPY']).read_bytes())
    group,search,field,value='My Fairy','Name','fairy_1_name','Navi'


class LegendsMapCardGuiTests(GuiWorkflow,unittest.TestCase):
    backend=p;editor_type=Editor;fixture=staticmethod(procedural_legends)
    group,search,field,value='Adventure map cards','Adventure: Compass','map_card_2efa',5
