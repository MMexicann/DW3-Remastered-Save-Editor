"""Sorting/copying preserves row selections and formats visible values."""
import tkinter as tk
from tkinter import ttk
import unittest

from koei_editor.shared.table_tools import attach_sorting, copy_selected, sort_table, sort_key


class TableToolsTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.table = ttk.Treeview(self.root, columns=('name', 'value'), show='headings')
        self.table.heading('name', text='Record')
        self.table.heading('value', text='Value')
        self.table.insert('', 'end', iid='ten', values=('Weapon 10', '1,000'))
        self.table.insert('', 'end', iid='two', values=('Weapon 2', '9'))
        self.table.insert('', 'end', iid='unknown', values=('Unknown\trow', '-'))
        attach_sorting(self.table)

    def tearDown(self):
        if hasattr(self, 'root'):
            self.root.destroy()

    def test_numeric_and_natural_sort_retain_selected_native_row_ids(self):
        self.table.selection_set('ten')
        sort_table(self.table, 'value')
        self.assertEqual(self.table.get_children(), ('two', 'ten', 'unknown'))
        self.assertEqual(self.table.selection(), ('ten',))
        sort_table(self.table, 'name')
        self.assertLess(self.table.index('two'), self.table.index('ten'))
        sort_table(self.table, 'name')
        self.assertGreater(self.table.index('two'), self.table.index('ten'))

    def test_keyboard_copy_on_focused_table(self):
        self.table.pack()
        self.root.update()
        self.table.focus_force()
        self.table.selection_set('two')
        self.table.event_generate('<Control-c>')
        self.root.update()
        self.assertEqual(self.root.clipboard_get(), 'Record\tValue\nWeapon 2\t9')

    def test_large_native_integer_values_sort_without_float_rounding(self):
        self.assertLess(sort_key('18,446,744,073,709,551,614'),
                        sort_key('18,446,744,073,709,551,615'))

    def test_copy_uses_display_order_headers_and_no_selection_leaves_clipboard(self):
        self.table.clipboard_clear()
        self.table.clipboard_append('previous')
        self.assertFalse(copy_selected(self.table))
        self.assertEqual(self.root.clipboard_get(), 'previous')
        self.table.selection_set(('unknown', 'two'))
        sort_table(self.table, 'value')
        self.assertTrue(copy_selected(self.table))
        self.assertEqual(self.root.clipboard_get(), 'Record\tValue\nWeapon 2\t9\nUnknown row\t-')


if __name__ == '__main__':
    unittest.main()
