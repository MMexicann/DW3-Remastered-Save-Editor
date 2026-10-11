"""Presentation-only sorting and copying for save-editor tables."""
import re
from decimal import Decimal


def sort_key(value):
    text = str(value).strip().casefold()
    number = text.replace(',', '')
    if re.fullmatch(r'-?\d+(?:\.\d+)?', number):
        return (0, Decimal(number))
    return (1, tuple((0, int(part)) if part.isdigit() else (1, part)
                     for part in re.split(r'(\d+)', text)))


def sort_table(view, column=None, reverse=None):
    if column is None:
        state = getattr(view, '_sort_state', None)
        if state is None:
            return
        column, reverse = state
    elif reverse is None:
        previous = getattr(view, '_sort_state', None)
        reverse = previous is not None and previous[0] == column and not previous[1]
    view._sort_state = (column, reverse)
    rows = sorted(view.get_children(), key=lambda row: sort_key(view.set(row, column)),
                  reverse=reverse)
    for position, row in enumerate(rows):
        view.move(row, '', position)


def attach_sorting(view):
    def copy_shortcut(_event):
        copy_selected(view)
        return "break"
    view.bind("<Control-c>", copy_shortcut, add="+")
    for column in view.cget('columns'):
        view.heading(column, command=lambda name=column: sort_table(view, name))


def copy_selected(view):
    """Copy displayed selected rows, in display order, as tab-separated text."""
    selected = set(view.selection())
    rows = [view.item(row, 'values') for row in view.get_children() if row in selected]
    if not rows:
        return False
    def cell(value):
        return str(value).replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')
    headers = [view.heading(column, 'text') for column in view.cget('columns')]
    text = '\n'.join('\t'.join(cell(value) for value in row) for row in [headers] + rows)
    view.clipboard_clear()
    view.clipboard_append(text)
    return True
