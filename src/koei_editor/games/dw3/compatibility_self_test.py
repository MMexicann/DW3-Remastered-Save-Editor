"""Opt-in hidden GUI checks for explicitly supplied save copies."""
from pathlib import Path
import hashlib
import json
import sys
import traceback
from unittest.mock import patch
from koei_editor.games.dw3.models import Change, fields
from koei_editor.games.dw3.save_parser import read_save, parse_bytes, safe_path
import koei_editor.games.dw3.save_writer as save_writer
import koei_editor.games.dw3.progression_editor as progression
import koei_editor.games.dw3.bodyguard_customization as customization
import koei_editor.games.dw3.bodyguard_editor as guards
import koei_editor.games.dw3.officer_weapon_editor as weapons
import koei_editor.games.dw3.collection_editor as collections
import koei_editor.games.dw3.musou_slots as musou_slots
import koei_editor.games.dw3.weapon_collection as weapon_collection


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
            saved_elixirs=progression.elixir_state(original)['saved_value']
            check('Elixir form reads the saved balance',int(editor.elixir_input.get())==saved_elixirs and str(editor.elixir_entry.cget('state'))=='normal')
            for value in (0,999):
                editor.elixir_input.set(str(value));editor.apply_elixirs()
                raw,elixir_audit=save_writer.serialize(editor.document,list(editor.changes.values()))
                result=parse_bytes(raw)
                check('Elixir '+str(value)+' form output reads back',progression.elixir_state(result)['value']==value and not errors)
                if 'BeansNum' in original.properties:
                    offset=original.properties['BeansNum']['data_offset']
                    check('Elixir '+str(value)+' changes only its scalar',result.plaintext[:offset]==original.plaintext[:offset] and result.plaintext[offset+4:]==original.plaintext[offset+4:])
                elif value==0:
                    check('Omitted zero Elixir balance stays byte-identical',raw==source and 'BeansNum' not in result.properties)
                else:
                    check('Missing counter is created without altering other saved bytes',all(original.plaintext[prop['tag_offset']:prop['data_offset']+prop['data_size']]==result.plaintext[result.properties[name]['tag_offset']:result.properties[name]['data_offset']+result.properties[name]['data_size']] for name,prop in original.properties.items()))
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
            editor.unlock_guard_customization()
            check('Bodyguard appearance action applies on supplied variant',not errors)
            custom_raw,_=save_writer.serialize(editor.document,list(editor.changes.values()))
            custom_doc=parse_bytes(custom_raw)
            custom_state=customization.customization_state(custom_doc)
            check('Both Nanman models and four special colors read back unlocked',all(row['unlocked'] for family in ('appearances','outfits') for row in custom_state[family]))
            check('Appearance unlocks preserve equipped bodyguards and story completion',custom_doc.properties['GuardDataArray']['value']==original.properties['GuardDataArray']['value'] and custom_doc.properties['EngiClearCharaArray']['value']==original.properties['EngiClearCharaArray']['value'])
            editor.discard()
            editor.unlock_movies()
            check('Movie collection callback validates',not errors)
            movie_raw,_=save_writer.serialize(editor.document,list(editor.changes.values()))
            movie_doc=parse_bytes(movie_raw)
            movie_state=collections.collection_state(movie_doc)['movies']
            check('Supported movies unlock and roundtrip',movie_state['owned']==movie_state['total'] and save_writer.serialize(movie_doc)[0]==movie_raw)
            check('Movies preserve active campaigns and story completion',movie_doc.properties.get('EngiSaveDataArray',{}).get('value')==original.properties.get('EngiSaveDataArray',{}).get('value') and movie_doc.properties['EngiClearCharaArray']['value']==original.properties['EngiClearCharaArray']['value'])
            editor.discard()
            editor.unlock_music()
            check('Music collection callback validates', not errors)
            music_raw, _ = save_writer.serialize(editor.document, list(editor.changes.values()))
            music_doc = parse_bytes(music_raw)
            music_state = collections.collection_state(music_doc)['music']
            check('All 42 music gallery entries unlock and roundtrip', music_state['owned'] == music_state['total'] == 42 and save_writer.serialize(music_doc)[0] == music_raw)
            check('Music preserves active campaigns and story completion', music_doc.properties.get('EngiSaveDataArray', {}).get('value') == original.properties.get('EngiSaveDataArray', {}).get('value') and music_doc.properties['EngiClearCharaArray']['value'] == original.properties['EngiClearCharaArray']['value'])
            editor.undo()
            check('Music undo restores the original pending batch', not editor.changes)
            editor.unlock_weapons()
            editor.unique_weapon_element.set('Wind')
            editor.apply_unique_weapon_elements()
            check('Bulk unique element callback validates after unlocks', not errors)
            element_raw, _ = save_writer.serialize(editor.document, list(editor.changes.values()))
            element_doc = parse_bytes(element_raw)
            element_rows = [row for row in weapons.states(element_doc) if row['array'] == 'UniqueWeaponDataArray' and row['element_editable']]
            check('All 84 unique elements read back as Wind', len(element_rows) == 84 and all(row['elements'] == 32 for row in element_rows))
            editor.discard()
            slots=musou_slots.slot_state(editor.document)
            editor.remove_all_musou_saves()
            check('Musou run removal callback validates on supplied layout',not errors)
            slot_raw,_=save_writer.serialize(editor.document,list(editor.changes.values()))
            slot_doc=parse_bytes(slot_raw)
            check('All editable active campaign slots reset in place',all(not row['active'] for row in musou_slots.slot_state(slot_doc)['slots'] if row['editable']) and len(musou_slots.slot_state(slot_doc)['slots'])==len(slots['slots']))
            check('Campaign removal preserves permanent stats and overall clears',slot_doc.properties['PCSaveDataArray']['value']==original.properties['PCSaveDataArray']['value'] and slot_doc.properties['EngiClearCharaArray']['value']==original.properties['EngiClearCharaArray']['value'])
            check('Campaign removal output roundtrips byte-identically',save_writer.serialize(slot_doc)[0]==slot_raw)
            editor.discard()
            editor.max_items();editor.max_guard_items();editor.max_all_weapon_rolls();editor.max_guard_weapons()
            check('Maximum actions apply on supplied variant',not errors)
            max_raw,_=save_writer.serialize(editor.document,list(editor.changes.values()))
            max_doc=parse_bytes(max_raw)
            check('Normal item maximum never lowers original owned values',all(fields(max_doc.records('EquipItemDataArray')[i])['Value']['value']==weapons.max_item_value(original,i) for i,row in editor.editable_item_rows() if row['kind']=='normal'))
            check('Bodyguard item maximum never lowers original owned values',all(guards.item_state(max_doc)[i]['value']==guards.max_item_value(original,i) for i,row in guards.GUARD_ITEMS.items() if row['kind']=='normal'))
            check('Combined maximum output roundtrips byte-identically',save_writer.serialize(max_doc)[0]==max_raw)
            editor.discard()
            editor.remove_grind()
            check('Grind preset validates on supplied variant',not errors)
            edited,edit_audit=save_writer.serialize(editor.document,list(editor.changes.values()))
            grind=parse_bytes(edited)
            check('Grind preset preserves story completion',grind.properties['EngiClearCharaArray']['value']==original.properties['EngiClearCharaArray']['value'])
            editor.discard()
            editor.unlock_everything()
            check('Unlock Everything callback validates on supplied variant', not errors)
            everything_raw, _ = save_writer.serialize(editor.document, list(editor.changes.values()))
            everything = parse_bytes(everything_raw)
            check('Unlock Everything includes all side stories', all(row['unlocked'] and row['free_mode_unlocked'] for row in progression.progression_state(everything)['side_stories']))
            check('Unlock Everything includes music and movies', all(row['owned'] == row['total'] for row in collections.collection_state(everything).values()))
            check('Unlock Everything includes the weapon collection and Tactics costumes', weapon_collection.has_all_collection(everything) and weapon_collection.has_tactics_costumes(everything))
            check('Unlock Everything preserves story clears and active runs', everything.properties['EngiClearCharaArray']['value'] == original.properties['EngiClearCharaArray']['value'] and everything.properties['EngiSaveDataArray']['value'] == original.properties['EngiSaveDataArray']['value'])
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
