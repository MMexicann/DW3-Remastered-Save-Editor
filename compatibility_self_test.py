"""Opt-in hidden GUI checks for explicitly supplied save copies."""
from pathlib import Path
import hashlib
import json
import sys
import traceback
from unittest.mock import patch
from models import Change, fields
from save_parser import read_save, parse_bytes, safe_path
import save_writer
import progression_editor as progression


def run(editor, fixture, output_directory):
    fixture=safe_path(Path(fixture)); output=safe_path(Path(output_directory))
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new or empty test output directory.')
    output.mkdir(parents=True,exist_ok=True)
    source=fixture.read_bytes(); digest=hashlib.sha256(source).hexdigest()
    checks=[]; errors=[]; notices=[]
    gui=sys.modules[type(editor).__module__]
    report={'packaged':bool(getattr(sys,'frozen',False)),'checks':checks}
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    try:
        copy=output/'input-copy.sav';copy.write_bytes(source)
        with patch.object(gui.filedialog,'askopenfilename',return_value=str(copy)), \
             patch.object(gui.messagebox,'showerror',side_effect=lambda *a,**k:errors.append(str(a))), \
             patch.object(gui.messagebox,'showwarning',side_effect=lambda *a,**k:notices.append(str(a))), \
             patch.object(gui.messagebox,'showinfo'), \
             patch.object(gui.messagebox,'askyesno',return_value=True):
            editor.open()
            check('Actual GUI opens supplied variant',editor.document is not None and not errors)
            original=editor.document
            check('Automatic backup is identical',editor.backup.read_bytes()==source)
            check('Officer rows respect actual saved count',len(editor.officers.get_children())==min(42,len(original.records('PCSaveDataArray'))))
            check('Bodyguard rows respect actual saved count',len(editor.bodyguards.get_children())==len(original.records('GuardDataArray')))
            unchanged,audit=save_writer.serialize(original)
            check('Unchanged serialization is byte-identical',unchanged==source and not audit['plaintext_changes'])
            target=output/'unchanged.sav';editor.save_to(target)
            check('Save As callback writes identical bytes',target.read_bytes()==source and not errors)
            saved_elixirs=original.properties['BeansNum']['value']
            check('Elixir form reads the saved balance',int(editor.elixir_input.get())==saved_elixirs and str(editor.elixir_entry.cget('state'))=='normal')
            for value in (0,999):
                editor.elixir_input.set(str(value));editor.apply_elixirs()
                raw,elixir_audit=save_writer.serialize(editor.document,list(editor.changes.values()))
                result=parse_bytes(raw)
                check('Elixir '+str(value)+' form output reads back',result.properties['BeansNum']['value']==value and not errors)
                offset=original.properties['BeansNum']['data_offset']
                check('Elixir '+str(value)+' changes only its scalar',result.plaintext[:offset]==original.plaintext[:offset] and result.plaintext[offset+4:]==original.plaintext[offset+4:])
                editor.discard()
            editor.max_elixirs()
            check('Max Elixirs form uses999',int(editor.elixir_input.get())==999)
            editor.undo()
            check('Undo restores saved Elixir balance',not editor.changes and int(editor.elixir_input.get())==saved_elixirs)
            prior=editor.changes.copy();error_count=len(errors)
            editor.elixir_input.set('1000');editor.apply_elixirs()
            check('Invalid Elixir input is rejected without changes',editor.changes==prior and len(errors)==error_count+1)
            errors.pop();editor.refresh_elixirs()
            editor.complete_all_musou();editor.elixir_input.set('17');editor.apply_elixirs()
            check('Combined Musou clear and Elixir input validates',not errors and progression.elixir_state(editor.document,list(editor.changes.values()))['value']==17)
            elixir_target=output/'elixirs17-with-clears.sav';editor.save_to(elixir_target)
            check('Save As reopens final17 balance',not errors and editor.document.properties['BeansNum']['value']==17 and int(editor.elixir_input.get())==17 and not editor.changes)
            check('Saved Elixir output is byte-stable',save_writer.serialize(read_save(elixir_target))[0]==elixir_target.read_bytes())
            # Reopen the untouched test copy before the existing feature checks.
            editor.open()
            check('Reopening original copy resets Elixir form',not errors and int(editor.elixir_input.get())==saved_elixirs)
            editor.stage_many([Change('officer',0,'Attack',150)])
            raw,audit=save_writer.serialize(editor.document,list(editor.changes.values()))
            reread=parse_bytes(raw)
            check('Ordinary stat edit reads back',fields(reread.records('PCSaveDataArray')[0])['Attack']['value']==150)
            check('Stat edit preserves all original bodyguard records',reread.properties['GuardDataArray']['value']==original.properties['GuardDataArray']['value'])
            editor.discard()
            editor.weapons.selection_set('unique:191');editor.select_weapon();editor.unlock_selected_weapon()
            check('Ziluan unique action applies without an error',not errors and editor.value('unique_weapon',191,'Owned'))
            zraw,zaudit=save_writer.serialize(editor.document,list(editor.changes.values()))
            zdoc=parse_bytes(zraw)
            check('Ziluan fourth weapon occupies native slot102',fields(zdoc.records('UniqueWeaponDataArray')[102])['WeaponID']['value']=='EWeaponID::WeaponID_191')
            check('Unique action preserves story completion',zdoc.properties['EngiClearCharaArray']['value']==original.properties['EngiClearCharaArray']['value'])
            editor.discard()
            for action in ('collect_all_weapons','unlock_side_stories','complete_all_musou'):
                getattr(editor,action)()
                check(action+' callback stages changes without errors',not errors)
                edited,edit_audit=save_writer.serialize(editor.document,list(editor.changes.values()))
                check(action+' output roundtrips',save_writer.serialize(parse_bytes(edited))[0]==edited)
                editor.discard()
            editor.remove_grind()
            check('Grind preset validates on supplied variant',not errors)
            edited,edit_audit=save_writer.serialize(editor.document,list(editor.changes.values()))
            grind=parse_bytes(edited)
            check('Grind preset preserves story completion',grind.properties['EngiClearCharaArray']['value']==original.properties['EngiClearCharaArray']['value'])
            editor.discard()
            check('Test input copy is untouched',copy.read_bytes()==source)
            check('No GUI error dialogs occurred',not errors)
        report['success']=True
    except Exception:
        report['success']=False;report['error']=traceback.format_exc()
    report['fixture_sha256']=digest
    report['fixture_unchanged']=hashlib.sha256(fixture.read_bytes()).hexdigest()==digest
    report['errors']=errors;report['notices']=notices
    report['success']=report['success'] and report['fixture_unchanged']
    (output/'compatibility-test-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not report['success']:raise RuntimeError(report.get('error','Compatibility test failed.'))
    return True
