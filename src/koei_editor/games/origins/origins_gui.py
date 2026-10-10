"""Dedicated Origins copy workspace. No unverified gameplay controls are enabled."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from koei_editor.shared.appearance import Appearance, THEMES
import koei_editor.games.origins.origins_editor as origins


class Editor(Appearance):
    def __init__(self, root, parent=None, theme='Light', on_theme=None):
        self.root = root
        self.on_theme = on_theme
        self.document = None
        self.backup = None
        self.changes = {}
        self.history = []
        self.comparison = None
        self.style = ttk.Style(root)
        self.theme_name = tk.StringVar(root, value=theme)
        self.apply_theme(theme)
        host = parent if parent is not None else root
        header = ttk.Frame(host, padding=(22, 18))
        header.pack(fill='x')
        ttk.Label(header, text='DYNASTY WARRIORS: ORIGINS', font=(self.font_family, 19, 'bold')).pack(anchor='w')
        ttk.Label(header, text='Save copies & recovery', style='Muted.TLabel').pack(anchor='w', pady=(5, 0))
        bar = ttk.Frame(host, padding=(22, 0))
        bar.pack(fill='x')
        ttk.Button(bar, text='Open Save Copy', command=self.open, style='Primary.TButton').pack(side='left', padx=(0, 7))
        self.buttons = []
        for label, command in (('Backup Save', self.make_backup), ('Save Copy As…', self.save_as),
                               ('Compare Copy…', self.compare)):
            button = ttk.Button(bar, text=label, command=command, state='disabled')
            button.pack(side='left', padx=(0, 7))
            self.buttons.append(button)
        ttk.Button(bar, text='Restore Backup…', command=self.restore).pack(side='left')
        self.filename = tk.StringVar(root, value='Open a separate SLOT*.dat copy to begin.')
        self.backup_label = tk.StringVar(root, value='An automatic backup is created before your copy is displayed.')
        info = ttk.Frame(host, padding=(22, 12))
        info.pack(fill='x')
        ttk.Label(info, textvariable=self.filename).pack(anchor='w')
        ttk.Label(info, textvariable=self.backup_label, style='Muted.TLabel').pack(anchor='w', pady=(5, 0))
        self.notebook = ttk.Notebook(host)
        self.notebook.pack(fill='both', expand=True, padx=22, pady=(0, 12))
        overview = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(overview, text='Save Overview')
        self.summary = tk.StringVar(root, value='No save copy open.')
        ttk.Label(overview, textvariable=self.summary, wraplength=960, justify='left').pack(anchor='w')
        ttk.Label(overview, text='Gameplay editing is awaiting save-format verification.',
                  style='Section.TLabel').pack(anchor='w', pady=(22, 7))
        ttk.Label(overview, text='Copies and backups retain every byte. The editor does not decrypt this file or change its gameplay data.',
                  wraplength=960, style='Muted.TLabel').pack(anchor='w')
        capabilities = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(capabilities, text='Feature Support')
        ttk.Label(capabilities, text='Each feature needs a verified field mapping and safe limits.',
                  style='Section.TLabel').pack(anchor='w', pady=(0, 12))
        self.features = ttk.Treeview(capabilities, columns=('support',), height=11)
        self.features.heading('#0', text='Feature')
        self.features.heading('support', text='Availability')
        self.features.column('#0', width=330)
        self.features.column('support', width=420)
        self.features.pack(fill='both', expand=True)
        for label in origins.EVIDENCE['features']:
            self.features.insert('', 'end', text=label, values=('Awaiting verification — editing disabled',))
        comparisons = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(comparisons, text='Copy Comparison')
        self.comparison_summary = tk.StringVar(root, value='Compare a before/after copy to find changed file regions.')
        ttk.Label(comparisons, textvariable=self.comparison_summary, wraplength=960).pack(anchor='w', pady=(0, 12))
        self.ranges = ttk.Treeview(comparisons, columns=('offset', 'length'), show='headings', height=9)
        self.ranges.heading('offset', text='File offset (hex)')
        self.ranges.heading('length', text='Changed bytes')
        self.ranges.pack(fill='both', expand=True)
        self.export_button = ttk.Button(comparisons, text='Export Comparison…', command=self.export, state='disabled')
        self.export_button.pack(anchor='e', pady=(12, 0))
        guide = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(guide, text='Save Samples')
        ttk.Label(guide, text='What is needed to enable gameplay editing', style='Section.TLabel').pack(anchor='w')
        ttk.Label(guide, text=(
            'Provide copied Steam SLOT*.dat files, the game version and DLC state, and the values shown in game.\n\n'
            'Useful pairs are saves immediately before and after changing just one value: money, skill points, '
            'one weapon proficiency, one gem, one horse, one Battle Art, or one bond. Include a save with no '
            'intentional changes as a control.\n\n'
            'A public DLC save confirms one file fingerprint. It does not establish encryption, checksums, '
            'field offsets, or safe maximum values. Those must be verified before edits can be enabled.\n\n'
            'Keep samples private. Use separate copies and retain your own untouched backups.'),
            wraplength=940, justify='left').pack(anchor='w', pady=(12, 0))
        bottom = ttk.Frame(host, padding=(22, 0, 22, 15))
        bottom.pack(fill='x')
        self.status = tk.StringVar(root, value='Copy tools ready. Gameplay editing unavailable.')
        ttk.Label(bottom, textvariable=self.status, wraplength=700, style='Muted.TLabel').pack(side='left')
        ttk.Button(bottom, text='Review Changes', command=self.review).pack(side='right')
        ttk.Button(bottom, text='Undo', command=self.undo, state='disabled').pack(side='right', padx=7)
        if parent is None:
            root.title('Dynasty Warriors: Origins — Save Copy Tools')
            root.protocol('WM_DELETE_WINDOW', self.close)

    def apply_theme(self, name):
        super().apply_theme(name)
        if self.on_theme is not None:
            self.on_theme(name)

    def dirty_ok(self):
        return True  # No gameplay modifications can be staged.

    def open(self):
        path = filedialog.askopenfilename(title='Open an Origins Save Copy', filetypes=[('Origins copy', '*.dat')])
        if not path:
            return
        try:
            document = origins.inspect_copy(path)
            backup = origins.backup_copy(document)
        except Exception as error:
            messagebox.showerror('Cannot Open Copy', str(error))
            return
        self.document, self.backup, self.comparison = document, backup, None
        self.filename.set(f'Opened copy: {document.source.name}')
        self.backup_label.set(f'Automatic backup: {backup.name}')
        recognition = ('Matches the published Steam DLC reference file.' if document.reference else
                       'Unverified file: the name and size do not establish game identity.')
        self.summary.set(f'{recognition}\n\nSize: {len(document.raw):,} bytes\nSHA-256: {document.sha256}\n\n'
                         'Gameplay parsing, integrity checks and game loading have not been validated.')
        for button in self.buttons:
            button.configure(state='normal')
        self.ranges.delete(*self.ranges.get_children())
        self.export_button.configure(state='disabled')
        self.comparison_summary.set('Compare another explicit copy. File offsets are not gameplay edit offsets.')
        self.status.set('Original bytes backed up. Copy operations preserve every byte.')

    def require_save(self):
        if self.document is None:
            messagebox.showinfo('Open a Copy', 'Open an explicit Origins .dat copy first.')
            return False
        return True

    def make_backup(self):
        if not self.require_save():
            return
        try:
            self.backup = origins.backup_copy(self.document)
            self.backup_label.set(f'Backup: {self.backup.name}')
            self.status.set('Untouched opened-copy snapshot backed up with its SHA-256 manifest.')
        except Exception as error:
            messagebox.showerror('Backup Failed', str(error))

    def save_as(self):
        if not self.require_save():
            return
        path = filedialog.asksaveasfilename(title='Save Unchanged Copy As', defaultextension='.dat',
                                           initialfile=self.document.source.stem + '.copy.dat',
                                           initialdir=self.document.source.parent, confirmoverwrite=False)
        if path:
            try:
                origins.duplicate_copy(self.document, path)
                self.status.set('A new identical copy was saved. No gameplay values changed.')
            except Exception as error:
                messagebox.showerror('Cannot Save Copy', str(error))

    def save_changes(self):
        messagebox.showinfo('Gameplay Editing Unavailable', 'Origins gameplay edits are awaiting format verification.')

    def undo(self):
        pass  # Intentionally disabled until there is a verified gameplay editor.

    def review(self):
        messagebox.showinfo('Review Changes', 'No gameplay changes are staged. Origins copy tools preserve every byte.')

    def compare(self):
        if not self.require_save():
            return
        path = filedialog.askopenfilename(title='Choose an Origins After Copy', filetypes=[('Origins copy', '*.dat')])
        if not path:
            return
        try:
            after = origins.inspect_copy(path)
            report = origins.compare_copies(self.document, after)
        except Exception as error:
            messagebox.showerror('Cannot Compare', str(error))
            return
        self.comparison = report
        self.ranges.delete(*self.ranges.get_children())
        for row in report['ranges']:
            self.ranges.insert('', 'end', values=(f'0x{row["offset"]:X}', row['length']))
        self.comparison_summary.set(f'{report["changed_bytes"]:,} changed bytes in '
                                    f'{report["changed_range_count"]:,} regions. '
                                    'Only the first 128 regions are displayed. These are encrypted file offsets.')
        self.export_button.configure(state='normal')
        self.notebook.select(2)
        self.status.set('Comparison complete. Both input files remain untouched.')

    def export(self):
        if self.comparison is None:
            return
        path = filedialog.asksaveasfilename(title='Export Private Comparison',
                                           initialfile='origins-comparison.changes.json',
                                           defaultextension='.changes.json', confirmoverwrite=False)
        if path:
            try:
                origins.export_comparison(self.comparison, path)
                self.status.set('Private comparison report saved.')
            except Exception as error:
                messagebox.showerror('Cannot Export', str(error))

    def restore(self):
        backup = filedialog.askopenfilename(title='Choose an Origins Editor Backup', filetypes=[('Origins backup', '*.dat')])
        if not backup:
            return
        destination = filedialog.asksaveasfilename(title='Restore to a New Copy', defaultextension='.dat',
                                                  initialfile='SLOT.restored.dat', confirmoverwrite=False)
        if destination:
            try:
                origins.restore_backup(backup, destination)
                self.status.set('Backup verified and restored to a new copy.')
            except Exception as error:
                messagebox.showerror('Cannot Restore', str(error))

    def close(self):
        self.root.destroy()
