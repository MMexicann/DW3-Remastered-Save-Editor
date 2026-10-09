"""Shared scalar save editor with retained independent sessions."""
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from appearance import Appearance
from copy_storage import atomic_new
from game_content import record_label
import verified_editor as backend


class Editor(Appearance):
    game_id = None
    backend = backend
    save_extension = '.dat'
    subtitle = 'Windows PC save editor'
    limit_heading = 'Edit limit'
    summary = ''
    feature_summaries = {
        'dw8xl': 'Resources, officer stats and weapon attribute ranks.',
        'pw3': 'Character stats, special bars and skill slots.',
    }

    def __init__(self, root, parent=None, theme='Light', on_theme=None):
        self.root, self.on_theme = root, on_theme
        self.layout = self.backend.get_format(self.game_id)
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
        summary = self.summary or self.feature_summaries.get(self.game_id, 'Edit save values and review changes.')
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
        tools = ttk.Frame(host, padding=(22, 8))
        tools.pack(fill='x')
        self.group = tk.StringVar(root, value='All fields')
        groups = ('All fields',) + tuple(dict.fromkeys(field.group for field in self.layout.fields))
        if self.game_id == 'dw8xl':
            groups += ('Weapon attributes',)
        select = ttk.Combobox(tools, textvariable=self.group, values=groups, state='readonly', width=18)
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
        text = prefix + self.document.source.name
        if self.game_id == 'pw3':
            text += f' · Observed Beli: {self.backend.observed_beli(self.document):,} (read only)'
        self.filename.set(text)

    def open(self):
        path = filedialog.askopenfilename(title='Open a Separate Save Copy',
                                          filetypes=[(self.layout.title + ' save copy', '*' + self.save_extension)])
        if not path:
            return
        try:
            document = self.backend.read_save(path, self.game_id)
            if not self.dirty_ok():
                return
            backup = self.backend.backup(document)
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
        for field in self.backend.fields_for(self.document):
            if self.group.get() not in ('All fields', field.group):
                continue
            original = field.value(self.document.payload)
            record = self.record_name(field)
            pending = str(self.changes[field.id]) if field.id in self.changes else '-'
            self.fields.insert('', 'end', iid=field.id,
                               values=(record, field.label, f'{original:,}', pending, f'{field.maximum:,}'))
        self.fields.selection_set([key for key in selected if self.fields.exists(key)])

    def selected(self, _event=None):
        keys = self.fields.selection()
        if keys and self.document:
            field = self.backend.field_map(self.document)[keys[0]]
            self.value.set(str(self.changes.get(field.id, field.value(self.document.payload))))
            if hasattr(self.backend, 'field_hint'):
                self.selection_info.set(self.backend.field_hint(self.document, field.id))
            elif self.game_id in ('dw8xl', 'pw3') and field.group in ('Characters', 'Officers') and field.slot:
                progress = self.backend.progression(self.document, field.slot)
                model = (f"Observed health curve: {progress['observed_health']:,}. "
                         if progress['observed_health'] is not None else '')
                extra = (f"Leadership {progress['leadership']}, XP {progress['leadership_experience']:,}; "
                         f"equipped weapon slots {progress['weapon_slots']} (read only)."
                         if self.game_id == 'dw8xl' else 'Direct stat boosts may reset on level-up.')
                self.selection_info.set(f"Record {field.slot}: level {progress['level']} and XP "
                                        f"{progress['experience']:,} (read only). {model}"
                                        + extra)
            elif field.group == 'Weapon attributes':
                record = self.backend.weapon(self.document, field.slot)
                self.selection_info.set(f"Weapon slot {field.slot}: ID {record['id']}; stored attack {record['attack']}. "
                                        'Only supported existing attribute ranks change. Identity, affinity and attack stay intact.')
            else:
                self.selection_info.set(f'Edit range: {field.minimum:,} to {field.maximum:,}. '
                                        'Max preserves higher existing values.')

    def record_name(self, field):
        if hasattr(self.backend, 'record_label'):
            return self.backend.record_label(field.slot, field.group)
        return record_label(self.game_id, field.slot, field.group) if field.slot else field.group

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
        def table(title, columns):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=title)
            view = ttk.Treeview(frame, columns=columns, show='headings')
            for column in columns:
                view.heading(column, text=column)
                view.column(column, width=180)
            view.pack(side='left', fill='both', expand=True)
            scroll = ttk.Scrollbar(frame, orient='vertical', command=view.yview)
            scroll.pack(side='right', fill='y')
            view.configure(yscrollcommand=scroll.set)
            return view
        if hasattr(self.backend, 'inspection_rows'):
            view = table('Mapped records', ('Group', 'Record / field', 'Opened value'))
            for row in self.backend.inspection_rows(document):
                view.insert('', 'end', values=(row['group'], row['label'], row['value']))
            ttk.Button(dialog, text='Close', command=dialog.destroy).pack(pady=10)
            self.apply_theme(self.theme_name.get())
            return
        columns = ('Record', 'Level', 'XP') + (('Leadership', 'Leadership XP', 'Weapon slots') if self.game_id == 'dw8xl' else ())
        view = table('Progression', columns)
        for slot, progress in enumerate(self.backend.progressions(document), 1):
            values = (record_label(self.game_id, slot, 'Officers' if self.game_id == 'dw8xl' else 'Characters'),
                      progress['level'], f"{progress['experience']:,}")
            if self.game_id == 'dw8xl':
                values += (progress['leadership'], progress['leadership_experience'], str(progress['weapon_slots']))
            view.insert('', 'end', values=values)
        if self.game_id == 'dw8xl':
            view = table('Existing weapons', ('Slot', 'Weapon ID', 'Affinity ID', 'Stored attack', 'Attribute ID:rank'))
            for record in self.backend.weapons(document):
                attributes = ', '.join(f'{identity}:{rank}' for identity, rank in record['attributes'] if identity != 255)
                view.insert('', 'end', values=(record['slot'], record['id'], record['affinity'], record['attack'], attributes))
        else:
            view = table('Costume associations', ('Character', 'Local slot', 'Asset costume ID', 'Stored ID'))
            for record in self.backend.costume_associations(document):
                stored = 'Absent (255)' if record['stored_id'] == 255 else str(record['stored_id'])
                view.insert('', 'end', values=(record_label('pw3', record['slot'], 'Characters'), record['local_slot'],
                                              record['asset_costume_id'], stored))
            ttk.Label(dialog, text='Costume associations do not prove ownership, unlock or equipped state.', padding=8).pack(anchor='w')
        ttk.Button(dialog, text='Close', command=dialog.destroy).pack(pady=10)
        self.apply_theme(self.theme_name.get())

    def stage_values(self, values):
        if self.document is None:
            return
        try:
            result = dict(self.changes)
            for key, value in values.items():
                result = self.backend.stage(self.document, result, key, value)
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
            self.stage_values(self.backend.limit_values(self.document, self.changes, self.fields.selection()))

    def max_visible(self):
        if self.document:
            self.stage_values(self.backend.limit_values(self.document, self.changes, self.fields.get_children()))

    def undo(self):
        if self.history:
            self.changes = self.history.pop()
            self.refresh()
            self.status.set(f'Undo complete. {len(self.changes)} pending edits.')

    def review(self):
        if self.document is None:
            return
        document = self.document
        rows = self.backend.review(document, self.changes)
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
            document = self.backend.save_as(self.document, self.changes, path)
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
                self.backup = self.backend.backup(self.document)
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
                self.backend.restore(path, destination, self.game_id)
                self.status.set('Backup restored to a new copy.')
            except Exception as error:
                messagebox.showerror('Restore Failed', str(error))

    def close(self):
        if self.dirty_ok():
            self.root.destroy()
