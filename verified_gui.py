"""Shared scalar save editor with retained independent sessions."""
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from appearance import Appearance
from copy_storage import atomic_new
from adapter_contract import BoundScalarAdapter
from scalar_presentation import ScalarPresentation
import verified_editor as backend


class Editor(Appearance):
    game_id = None
    backend = backend
    save_extension = '.dat'
    subtitle = 'Windows PC save editor'
    limit_heading = 'Edit limit'
    summary = ''
    presentation_type = ScalarPresentation

    def __init__(self, root, parent=None, theme='Light', on_theme=None):
        self.root, self.on_theme = root, on_theme
        self.adapter = BoundScalarAdapter(self.game_id, self.save_extension, self.backend)
        self.layout = self.adapter.get_format()
        self.presentation = self.presentation_type(self.backend, self.game_id)
        self.style = ttk.Style(root)
        self.theme_name = tk.StringVar(root, value=theme)
        self.document, self.backup = None, None
        self.changes, self.history = {}, []
        self.apply_theme(theme)
        host = parent if parent is not None else root
        header = ttk.Frame(host, padding=(22, 16))
        header.pack(fill='x')
        ttk.Label(header, text=self.layout.title, font=(self.font_family, 18, 'bold')).pack(anchor='w')
        ttk.Label(header, text=self.subtitle, style='Muted.TLabel').pack(anchor='w', pady=(5, 0))
        summary = self.summary or 'Edit save values and review changes.'
        ttk.Label(header, text=summary, wraplength=990).pack(anchor='w', pady=(8, 0))
        bar = ttk.Frame(host, padding=(22, 0))
        bar.pack(fill='x')
        ttk.Button(bar, text='Open Save Copy', command=self.open, style='Primary.TButton').pack(side='left')
        self.save_buttons = []
        for label, callback in (('Save As...', self.save_as), ('Backup Save', self.make_backup),
                                ('Review Changes', self.review), ('Undo', self.undo)):
            button = ttk.Button(bar, text=label, command=callback, state='disabled')
            button.pack(side='left', padx=(8, 0))
            self.save_buttons.append(button)
        ttk.Button(bar, text='Restore Backup...', command=self.restore).pack(side='left', padx=8)
        self.filename = tk.StringVar(root, value=f'Open a separate {self.save_extension} copy to begin.')
        ttk.Label(host, textvariable=self.filename, padding=(22, 12)).pack(anchor='w')
        filter_bar = ttk.Frame(host, padding=(22, 0))
        filter_bar.pack(fill='x')
        ttk.Label(filter_bar, text='Find fields').pack(side='left', padx=(0, 8))
        self.search = tk.StringVar(root)
        self.search_entry = ttk.Entry(filter_bar, textvariable=self.search, width=40)
        self.search_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(filter_bar, text='Clear', command=lambda: self.search.set('')).pack(side='left', padx=(8, 0))
        tools = ttk.Frame(host, padding=(22, 8))
        tools.pack(fill='x')
        self.group = tk.StringVar(root, value='All fields')
        groups = ('All fields',) + tuple(dict.fromkeys(field.group for field in self.layout.fields))
        groups += self.presentation.extra_groups
        select = ttk.Combobox(tools, textvariable=self.group, values=groups, state='readonly', width=18)
        self.group_selector = select
        select.pack(side='left')
        select.bind('<<ComboboxSelected>>', lambda _event: self.refresh())
        ttk.Label(tools, text='Value').pack(side='left', padx=(18, 8))
        self.value = tk.StringVar(root)
        ttk.Entry(tools, textvariable=self.value, width=15).pack(side='left')
        self.edit_buttons = []
        for label, callback in (('Apply Selected', self.apply_selected),
                                ('Max Selected', self.max_selected), ('Max Visible Fields', self.max_visible)):
            button = ttk.Button(tools, text=label, command=callback, state='disabled')
            button.pack(side='left', padx=(8, 0))
            self.edit_buttons.append(button)
        inspect = ttk.Button(tools, text='Inspect Data', command=self.show_inspector, state='disabled')
        inspect.pack(side='right', padx=4)
        self.edit_buttons.append(inspect)
        # Reserve field guidance and status before the expanding table.
        feedback = ttk.Frame(host)
        feedback.pack(side='bottom', fill='x')
        self.selection_info = tk.StringVar(root, value='Select a record to inspect its values.')
        self.selection_label = ttk.Label(feedback, textvariable=self.selection_info, wraplength=1000,
                                         padding=(22, 8), style='Muted.TLabel')
        self.selection_label.pack(anchor='w')
        self.status = tk.StringVar(root, value='Copy-only editing. The opened file is never overwritten.')
        self.status_label = ttk.Label(feedback, textvariable=self.status, padding=(22, 15), wraplength=1000)
        self.status_label.pack(anchor='w')
        frame = ttk.Frame(host, padding=(22, 0))
        frame.pack(fill='both', expand=True)
        self.fields = ttk.Treeview(frame, columns=('slot', 'field', 'original', 'pending', 'limit'),
                                  show='headings', selectmode='extended')
        for column, label, width in (('slot', 'Record', 140), ('field', 'Field', 210),
                                     ('original', 'Opened value', 160), ('pending', 'Pending value', 160),
                                     ('limit', self.limit_heading, 160)):
            self.fields.heading(column, text=label)
            self.fields.column(column, width=width)
        self.fields.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=self.fields.yview)
        scroll.pack(side='right', fill='y')
        self.fields.configure(yscrollcommand=scroll.set)
        self.fields.bind('<<TreeviewSelect>>', self.selected)
        self.search.trace_add('write', lambda *_args: self.refresh())
        if parent is None:
            root.title(self.layout.title + ' — Save Editor')
            root.protocol('WM_DELETE_WINDOW', self.close)

    def apply_theme(self, name):
        super().apply_theme(name)
        if self.on_theme is not None:
            self.on_theme(name)

    def dirty_ok(self):
        return not self.changes or messagebox.askyesno('Pending Edits', 'Discard pending edits and continue?')

    def update_filename(self, prefix):
        text = prefix + self.document.source.name + self.presentation.filename_suffix(self.document)
        self.filename.set(text)

    def open(self):
        path = filedialog.askopenfilename(title='Open a Separate Save Copy',
                                          filetypes=[(self.layout.title + ' save copy', '*' + self.save_extension)])
        if not path:
            return
        try:
            document = self.adapter.read_save(path, self.game_id)
            if not self.dirty_ok():
                return
            backup = self.adapter.backup(document)
        except Exception as error:
            messagebox.showerror('Cannot Open Save', str(error))
            return
        self.document, self.backup = document, backup
        self.changes, self.history = {}, []
        for button in self.save_buttons + self.edit_buttons:
            button.configure(state='normal')
        self.update_filename('Opened copy: ')
        self.status.set('Opened save copy. Automatic backup: ' + backup.name)
        self.refresh()

    def refresh(self):
        selected = self.fields.selection()
        self.fields.delete(*self.fields.get_children())
        self.selection_info.set('Select a record to inspect its values.')
        if self.document is None:
            return
        fields = self.adapter.fields_for(self.document)
        groups = ('All fields',) + tuple(dict.fromkeys(field.group for field in fields))
        self.group_selector.configure(values=groups)
        if self.group.get() not in groups:
            self.group.set('All fields')
        tokens = self.search.get().casefold().split()
        for field in fields:
            if self.group.get() not in ('All fields', field.group):
                continue
            original = field.value(self.document.payload)
            record = self.record_name(field)
            searchable = f'{field.label} {field.group} {record} {field.id}'.casefold()
            if any(token not in searchable for token in tokens):
                continue
            pending = str(self.changes[field.id]) if field.id in self.changes else '-'
            self.fields.insert('', 'end', iid=field.id,
                               values=(record, field.label, f'{original:,}', pending, f'{field.maximum:,}'))
        self.fields.selection_set([key for key in selected if self.fields.exists(key)])

    def selected(self, _event=None):
        keys = self.fields.selection()
        if keys and self.document:
            field = self.adapter.field_map(self.document)[keys[0]]
            self.value.set(str(self.changes.get(field.id, field.value(self.document.payload))))
            self.selection_info.set(self.presentation.field_hint(self.document, field))

    def record_name(self, field):
        return self.presentation.record_name(field)

    def show_inspector(self):
        if self.document is None:
            return
        document = self.document
        dialog = tk.Toplevel(self.root)
        dialog.title('Mapped Save Data - Read Only')
        dialog.geometry('1000x600')
        ttk.Label(dialog, text='Opened data: progression and content associations. Pending edits appear in the main editor.',
                  padding=12, wraplength=960).pack(anchor='w')
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=12, pady=8)
        def table(title, columns, rows, note):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=title)
            tools = ttk.Frame(frame, padding=(6, 6))
            tools.pack(fill='x')
            ttk.Label(tools, text='Find records').pack(side='left', padx=(0, 8))
            query = tk.StringVar(dialog)
            ttk.Entry(tools, textvariable=query).pack(side='left', fill='x', expand=True)
            if note:
                ttk.Label(frame, text=note, padding=8, wraplength=950).pack(side='bottom', anchor='w')
            body = ttk.Frame(frame)
            body.pack(fill='both', expand=True)
            view = ttk.Treeview(body, columns=columns, show='headings')
            for column in columns:
                view.heading(column, text=column)
                view.column(column, width=180)
            view.grid(row=0, column=0, sticky='nsew')
            body.rowconfigure(0, weight=1)
            body.columnconfigure(0, weight=1)
            scroll = ttk.Scrollbar(body, orient='vertical', command=view.yview)
            scroll.grid(row=0, column=1, sticky='ns')
            horizontal = ttk.Scrollbar(body, orient='horizontal', command=view.xview)
            horizontal.grid(row=1, column=0, sticky='ew')
            view.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
            records = tuple((view.insert('', 'end', values=row),
                             ' '.join(str(value) for value in row).casefold()) for row in rows)
            def filter_rows(*_args):
                tokens = query.get().casefold().split()
                for identity, text in records:
                    if all(token in text for token in tokens):
                        view.move(identity, '', 'end')
                    else:
                        view.detach(identity)
            query.trace_add('write', filter_rows)
            return view
        for content in self.presentation.inspection_tables(document):
            table(content.title, content.columns, content.rows, content.note)
        ttk.Button(dialog, text='Close', command=dialog.destroy).pack(pady=10)
        self.apply_theme(self.theme_name.get())

    def stage_values(self, values):
        if self.document is None:
            return
        try:
            result = dict(self.changes)
            for key, value in values.items():
                result = self.adapter.stage(self.document, result, key, value)
            if result != self.changes:
                self.history.append(dict(self.changes))
                self.changes = result
                self.refresh()
            self.status.set(f'{len(self.changes)} pending field edits. Review changes before saving a new copy.')
        except Exception as error:
            messagebox.showerror('Cannot Stage Edit', str(error))

    def apply_selected(self):
        try:
            value = int(self.value.get())
        except ValueError:
            messagebox.showerror('Invalid Value', 'Enter a whole number.')
            return
        self.stage_values({key: value for key in self.fields.selection()})

    def max_selected(self):
        if self.document:
            self.stage_values(self.adapter.limit_values(self.document, self.changes, self.fields.selection()))

    def max_visible(self):
        if self.document:
            self.stage_values(self.adapter.limit_values(self.document, self.changes, self.fields.get_children()))

    def undo(self):
        if self.history:
            self.changes = self.history.pop()
            self.refresh()
            self.status.set(f'Undo complete. {len(self.changes)} pending edits.')

    def review(self):
        if self.document is None:
            return
        document = self.document
        rows = self.adapter.review(document, self.changes)
        dialog = tk.Toplevel(self.root)
        dialog.title('Review Changes')
        dialog.geometry('700x480')
        ttk.Label(dialog, text=f'{self.layout.title}\n{len(rows)} staged field edits', padding=15).pack(anchor='w')
        tree = ttk.Treeview(dialog, columns=('field', 'before', 'after'), show='headings')
        for column, label in (('field', 'Field / slot'), ('before', 'Before'), ('after', 'After')):
            tree.heading(column, text=label)
        for field, before, after in rows:
            tree.insert('', 'end', values=(field.label + (f' / {self.record_name(field)}' if field.slot else ''), before, after))
        tree.pack(fill='both', expand=True, padx=15)
        def export():
            path = filedialog.asksaveasfilename(title='Export Change Review', defaultextension='.changes.json')
            if path:
                report = {'game_id': self.game_id, 'source_sha256': document.sha256,
                          'changes': [{'field': field.id, 'before': before, 'after': after}
                                      for field, before, after in rows]}
                try:
                    if not path.lower().endswith('.changes.json'):
                        raise ValueError('Choose a .changes.json review file.')
                    atomic_new(json.dumps(report, indent=2).encode(), path)
                except Exception as error:
                    messagebox.showerror('Cannot Export Review', str(error))
        ttk.Button(dialog, text='Export Review...', command=export).pack(side='left', padx=15, pady=12)
        ttk.Button(dialog, text='Close', command=dialog.destroy).pack(side='right', padx=15)
        self.apply_theme(self.theme_name.get())

    def save_changes(self):
        self.save_as()

    def save_as(self):
        if self.document is None:
            return
        path = filedialog.asksaveasfilename(title='Save Edited Copy As', defaultextension=self.save_extension,
                                           initialdir=self.document.source.parent,
                                           initialfile=self.document.source.stem + '.edited' + self.save_extension, confirmoverwrite=False)
        if path:
            self.save_to(path)

    def save_to(self, path):
        try:
            document = self.adapter.save_as(self.document, self.changes, path)
        except Exception as error:
            messagebox.showerror('Cannot Save Copy', str(error))
            return
        self.document = document
        self.changes, self.history = {}, []
        self.update_filename('Opened edited copy: ')
        self.refresh()
        self.status.set('Edited copy saved. Original snapshot backed up.')

    def make_backup(self):
        if self.document:
            try:
                self.backup = self.adapter.backup(self.document)
                self.status.set('Opened bytes backed up: ' + self.backup.name)
            except Exception as error:
                messagebox.showerror('Backup Failed', str(error))

    def restore(self):
        path = filedialog.askopenfilename(title='Choose a Backup for This Game',
                                          filetypes=[('Save backup', '*' + self.save_extension)])
        if not path:
            return
        destination = filedialog.asksaveasfilename(title='Restore to a New Copy',
                                                  defaultextension=self.save_extension, confirmoverwrite=False)
        if destination:
            try:
                self.adapter.restore(path, destination, self.game_id)
                self.status.set('Backup restored to a new copy.')
            except Exception as error:
                messagebox.showerror('Restore Failed', str(error))

    def close(self):
        if self.dirty_ok():
            self.root.destroy()
