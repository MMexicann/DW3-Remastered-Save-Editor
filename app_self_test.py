"""Opt-in, hidden packaged-app validation against an explicitly selected copy.

Invoked only with --self-test INPUT.sav NEW_OUTPUT_DIRECTORY. Never runs during
normal use. Exercises actual GUI callbacks while replacing their file dialogs.
"""
from pathlib import Path
import hashlib
import json
import sys
import traceback
from models import Change, fields
from save_parser import read_save, parse_bytes, safe_path
import save_writer
import bodyguard_editor as bg
import bodyguard_growth as growth
import officer_weapon_editor as weapon


def run(editor, fixture: Path, output_directory: Path):
    fixture=safe_path(fixture)
    output=safe_path(output_directory)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Self-test output directory must be new or empty.')
    output.mkdir(parents=True,exist_ok=True)
    gui=sys.modules[type(editor).__module__]
    checks=[];errors=[];warnings=[]
    original_hash=hashlib.sha256(fixture.read_bytes()).hexdigest()
    report={'packaged':bool(getattr(sys,'frozen',False)),'checks':checks}
    saved_dialogs={}
    def replace(owner,name,implementation):
        saved_dialogs.setdefault((owner,name),getattr(owner,name))
        setattr(owner,name,implementation)
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    def payload(document,prop):
        return document.plaintext[prop['data_offset']:prop['data_offset']+prop['data_size']]
    try:
        copy=output/'input-copy.sav'
        copy.write_bytes(fixture.read_bytes())
        original=read_save(copy)
        original_guards=bg.weapon_state(original)
        def expected_guard_max(row):
            before=original_guards[row['slot']]
            return {skill['id']:skill['value'] for skill in (bg.max_skills(row['weapon_id'],before['skills']) if before['weapon_id']==row['weapon_id'] else bg.max_skills(row['weapon_id']))}
        replace(gui.messagebox,'askyesno',lambda *args,**kwargs:True)
        replace(gui.messagebox,'showinfo',lambda *args,**kwargs:None)
        replace(gui.messagebox,'showerror',lambda *args,**kwargs:errors.append(str(args)))
        replace(gui.messagebox,'showwarning',lambda *args,**kwargs:warnings.append(str(args)))
        replace(gui.filedialog,'askopenfilename',lambda *args,**kwargs:str(copy))
        editor.open()
        check('Open-copy callback creates byte-identical backup',editor.document is not None and editor.backup.read_bytes()==original.encrypted)
        first_backup=editor.backup
        check('All seven tabs and 42 officers/43 items load',len(editor.tabs)==7 and len(editor.officers.get_children())==42 and len(editor.items.get_children())==43)
        editor.stage_many([Change('officer',0,'Attack',149)])
        previous_document=editor.document
        previous_changes=editor.changes.copy()
        normal_refresh=editor.refresh
        refresh_calls=[0]
        def failing_refresh_once():
            refresh_calls[0]+=1
            if refresh_calls[0]==1:raise RuntimeError('Simulated open display failure')
            return normal_refresh()
        replace(editor,'refresh',failing_refresh_once)
        editor.open()
        check('Failed open retains previous document',editor.document is previous_document)
        check('Failed open retains staged edits and original backup',editor.changes==previous_changes and editor.backup==first_backup)
        check('Failed open reports one clear error',len(errors)==1)
        errors.clear()
        editor.refresh=normal_refresh
        editor.discard()
        concurrent_copy=output/'concurrent-copy.sav'
        concurrent_copy.write_bytes(original.encrypted)
        concurrent_document=read_save(concurrent_copy)
        normal_serialize=save_writer.serialize
        def replace_during_serialize(*args,**kwargs):
            result=normal_serialize(*args,**kwargs)
            concurrent_copy.write_bytes(b'Concurrent edit during save')
            return result
        replace(save_writer,'serialize',replace_during_serialize)
        refused=False
        try:save_writer.write_save(concurrent_document,concurrent_copy,overwrite=True)
        except ValueError:refused=True
        finally:save_writer.serialize=normal_serialize
        check('Changed destination is refused before replacement',refused and concurrent_copy.read_bytes()==b'Concurrent edit during save')
        check('Concurrent edit refusal leaves no audit or temporary file',not list(output.glob('concurrent-copy.sav.*.changes.json')) and not list(output.glob('.concurrent-copy.sav.*.tmp')))
        invalid_backup=save_writer.backup_save(original,output/'invalid-manifest')
        invalid_backup.with_suffix('.json').write_text('[]',encoding='utf-8')
        refused=False
        try:save_writer.restore_backup(invalid_backup,output/'invalid-manifest-restored.sav')
        except ValueError:refused=True
        check('Malformed backup manifest cannot create an output',refused and not (output/'invalid-manifest-restored.sav').exists())
        editor.officer_filter.set('no officer matches this search')
        check('Empty officer search is safe',not editor.officers.get_children())
        editor.max_selected()
        editor.officer_filter.set('')
        editor.item_filter.set('no item matches this search')
        check('Empty item search is safe',not editor.items.get_children())
        editor.item_filter.set('')
        editor.max_selected()
        check('Max selected stages legitimate stats',editor.value('officer',0,'Attack')==150 and editor.value('officer',0,'MaxHealth')==250)
        editor.undo()
        check('Batch undo returns to original',not editor.changes)
        editor.max_items()
        check('All 16 normal-item limits are staged',all(editor.value('item',i,'Value')==cap for i,cap in save_writer.ITEM_CAPS.items()))
        editor.discard()
        check('Discard clears staged edits',not editor.changes)
        missing=next((i for i in save_writer.ITEM_CAPS if not editor.original_value(Change('item',i,'Owned',True))),None)
        if missing is not None:
            editor.stage_many([Change('item',missing,'Owned',True),Change('item',missing,'Value',save_writer.ITEM_CAPS[missing])])
            editor.stage_many([Change('item',missing,'Owned',False)])
            check('Cancel item acquisition also cancels its value',not editor.changes)
        editor.weapons.selection_set('unique:89');editor.select_weapon()
        check('Weapon details display readable bonuses','Base attack' in editor.weapon_detail.get())
        editor.weapon_filter.set('no weapon matches this search')
        check('Empty weapon search disables bonus editing safely',not editor.weapons.get_children() and editor.current_weapon_data_id is None)
        editor.max_selected_weapon_rolls();editor.weapon_filter.set('')
        editor.weapons.selection_set('WeaponDataArray:36');editor.select_weapon()
        check('Fused weapon has editable rare identity with no numeric roll',editor.current_weapon_data_id==36 and str(editor.weapon_bonus_boxes[6].cget('state'))=='readonly' and str(editor.weapon_bonus_value_boxes[6].cget('state'))=='disabled')
        editor.weapon_bonus_names[6].set('The Way of Musou');editor.change_weapon_bonus(6);editor.apply_weapon_rolls()
        rare_change=weapon.state(editor.document,36,list(editor.changes.values()))
        check('Rare Apply uses final slot with zero value',rare_change['skills'][8]=={'id':18,'value':0} and rare_change['skills'][:6]==weapon.state(original,36)['skills'][:6])
        editor.weapon_element.set('Wind');editor.apply_weapon_element()
        elemental=weapon.state(editor.document,36,list(editor.changes.values()))
        check('Element Apply preserves existing hit and other flags',elemental['elements']==32 and elemental['attr'] & ~weapon.ELEMENT_MASK==weapon.state(original,36)['attr'] & ~weapon.ELEMENT_MASK)
        edited_attributes,attribute_audit=save_writer.serialize(editor.document,list(editor.changes.values()))
        reread_attributes=parse_bytes(edited_attributes)
        check('Rare and element GUI changes serialize and read back',weapon.state(reread_attributes,36)['skills']==elemental['skills'] and weapon.state(reread_attributes,36)['attr']==elemental['attr'])
        check('Attribute workflow records verified byte audit',bool(attribute_audit['plaintext_changes']))
        editor.undo();editor.undo()
        check('Rare and element undo restores original pending state',not editor.changes)
        editor.weapon_bonus_values[0].set('1');editor.apply_weapon_rolls()
        check('Actual bonus Apply callback writes selected legal roll into pending state',weapon.state(editor.document,36,list(editor.changes.values()))['skills'][0]['value']==1)
        editor.undo();check('Weapon bonus undo restores original',not editor.changes)
        editor.weapon_bonus_names[1].set(editor.weapon_bonus_names[0].get());editor.change_weapon_bonus(1);editor.apply_weapon_rolls()
        check('GUI refuses duplicate normal bonuses',bool(errors) and not editor.changes)
        errors.clear();editor.select_weapon()
        editor.max_selected_weapon_rolls()
        check('Max selected preserves six bonus identities and rare slot position',weapon.state(editor.document,36,list(editor.changes.values()))['skills']==weapon.max_existing_skills(original,36))
        editor.undo()
        editor.weapons.selection_set('unique:116');editor.select_weapon();editor.unlock_selected_weapon()
        check('Pending unique acquisition enables its bonus controls',editor.current_weapon_data_id==10027 and str(editor.weapon_roll_button.cget('state'))=='normal')
        editor.max_selected_weapon_rolls()
        pending=weapon.state(editor.document,10027,list(editor.changes.values()))
        check('Unique-specific Attack43 stock exception retained',next(s['value'] for s in pending['skills'] if s['id']==4)==43)
        editor.discard();check('Discard clears acquisition and bonus edits together',not editor.changes)
        editor.max_all_weapon_rolls()
        check('Max All Owned stages only verified owned copies',all(c.category=='weapon_roll' for c in editor.changes.values()) and all(weapon.state(original,c.index)['owned'] for c in editor.changes.values()))
        editor.discard()
        check('Saved teams, ten BG items and fifteen BG weapon definitions load',len(editor.bodyguards.get_children())==len(original.records('GuardDataArray')) and len(editor.guard_items.get_children())==10 and len(editor.guard_weapons.get_children())==15)
        editor.bodyguards.selection_set('1');editor.select_bodyguard()
        check('Growth budget describes the actual selected team',editor.guard_budget.get().startswith(f'Growth points: {growth.spent(bg.team_state(original,1)["BGLevels"])} / {growth.budget(bg.team_state(original,1)["SPoint"])}'))
        editor.bodyguard_merit.set('99999')
        for index,variable in editor.guard_growth_inputs.items():variable.set(str(growth.LEVEL_CAPS[index]))
        editor.apply_bodyguard()
        check('GUI rejects growth that exceeds the shared budget',bool(errors) and not editor.changes)
        errors.clear();editor.select_bodyguard()
        for mode in growth.PRESET_NAMES:
            editor.max_bodyguard(mode)
            check(f'Legal {mode} growth preset and automatic Count/AI',bg.team_state(editor.document,1,list(editor.changes.values()))['BGLevels']==growth.safe_preset(99999,mode))
            editor.undo()
            check(f'{mode} growth undo returns to original',not editor.changes)
        editor.bodyguard_merit.set('0')
        for variable in editor.guard_growth_inputs.values():variable.set('0')
        editor.apply_bodyguard()
        check('Merit can decrease with a valid final growth allocation',bg.team_state(editor.document,1,list(editor.changes.values()))['BGLevels']==[0]*6)
        editor.undo()
        editor.max_guard_items()
        check('BG item maximum uses nine verified rolls and rare ownership',all(s['owned'] and s['value']==bg.GUARD_ITEMS[i]['max_value'] for i,s in bg.item_state(editor.document,list(editor.changes.values())).items()))
        editor.undo()
        editor.max_guard_weapons()
        pool=bg.weapon_state(editor.document,list(editor.changes.values()))
        check('All fifteen BG weapon types acquire legal maximum bonuses; view-only copies preserved',{s['weapon_id'] for s in pool if s['weapon_id'] is not None}==set(bg.GUARD_WEAPONS) and all({skill['id']:skill['value'] for skill in s['skills']}==expected_guard_max(s) if s['editable'] else s['skills']==bg.weapon_state(original)[s['slot']]['skills'] for s in pool if s['weapon_id'] is not None))
        row=next(s for s in pool if s['weapon_id']==175)
        editor.guard_weapons.selection_set(f'slot:{row["slot"]}');editor.select_guard_weapon()
        for index,skill in enumerate(bg.max_skills(175)):
            editor.guard_bonus_items[index].set(next(label for label,item in editor.guard_bonus_choices.items() if item==skill['id']))
            editor.guard_bonus_values[index].set(str(bg.GUARD_WEAPONS[175]['allowed_values_by_guard_item_id'][str(skill['id'])][0]))
        editor.apply_guard_bonuses()
        check('Actual per-copy bonus callback accepts legal dropdown choices',('guard_weapon_slot',row['slot'],'Skills') in editor.changes)
        editor.max_guard_weapon()
        check('Max selected copies clears older custom overrides',('guard_weapon_slot',row['slot'],'Skills') not in editor.changes and {skill['id']:skill['value'] for skill in bg.weapon_state(editor.document,list(editor.changes.values()))[row['slot']]['skills']}==expected_guard_max(row))
        editor.discard()
        editor.remove_grind()
        check('Remove The Grind leaves story and availability alone',not any(c.category=='unlock' for c in editor.changes.values()))
        editor.max_all_weapon_rolls()
        check('Remove The Grind preserves team equipment choices',all(bg.team_state(editor.document,i,list(editor.changes.values()))['MemberWeapon']==bg.team_state(original,i)['MemberWeapon'] and bg.team_state(editor.document,i,list(editor.changes.values()))['MemberItem']==bg.team_state(original,i)['MemberItem'] for i in range(len(original.records('GuardDataArray')))))
        editor.equip_best_guard_weapons()
        check('Explicit Equip Best uses inventory references of five correct families',bg.team_state(editor.document,1,list(editor.changes.values()))['MemberWeapon'][:5]==bg.best_weapon_refs(editor.document,list(editor.changes.values())))
        editor.guard_equip_item.set(next(label for label,item in editor.guard_equip_item_choices.items() if item==9));editor.apply_guard_equipment()
        check('Equipment callback selects the owned Healing Scroll',bg.team_state(editor.document,1,list(editor.changes.values()))['MemberItem']==9)
        editor.guard_items.selection_set('9');editor.select_guard_item();editor.guard_item_owned.set(False);editor.apply_guard_item()
        check('GUI prevents removal of an equipped BG item',bool(errors) and bg.item_state(editor.document,list(editor.changes.values()))[9]['owned'])
        errors.clear();editor.select_guard_item()
        edited_path=output/'edited.sav'
        editor.save_to(edited_path)
        check('Actual GUI Save As succeeds and clears staged edits',not errors and edited_path.exists() and not editor.changes and editor.document.source==edited_path)
        edited=read_save(edited_path)
        for i in range(42):
            values=fields(edited.records('PCSaveDataArray')[i])
            check(f'Officer {i} verified maxima',all(values[name]['value']==cap for name,cap in save_writer.CAPS.items()))
        for i,item in save_writer.ITEMS.items():
            values=fields(edited.records('EquipItemDataArray')[i])
            check(f'Item {i} legitimate ownership/value',values['EquipItemID']['value']=='EEquipItemID::'+item['enum'] and values['Value']['value']==save_writer.ITEM_CAPS.get(i,0))
        check('All saved bodyguard teams have legal maximum Merit and balanced growth',all(
            fields(edited.records('GuardDataArray')[i])['SPoint']['value']==99999 and
            fields(edited.records('GuardDataArray')[i])['BGLevels']['value']['values']==growth.safe_preset()
            for i in range(len(edited.records('GuardDataArray')))))
        for i,state in bg.item_state(edited).items():
            check(f'BG item {i} verified maximum/rare ownership',state['owned'] and state['value']==bg.GUARD_ITEMS[i]['max_value'])
        pool=bg.weapon_state(edited)
        for weapon_id in bg.GUARD_WEAPONS:
            copies=[s for s in pool if s['weapon_id']==weapon_id]
            check(f'BG weapon {weapon_id} owned with legal tier-specific bonuses or preserved view-only copies',bool(copies) and all({skill['id']:skill['value'] for skill in s['skills']}==expected_guard_max(s) if s['editable'] else s['skills']==bg.weapon_state(original)[s['slot']]['skills'] for s in copies))
        check('Equipped BG item and inventory choices survive save/readback',bg.team_state(edited,1)['MemberItem']==9 and bg.team_state(edited,1)['MemberWeapon'][:5]==bg.best_weapon_refs(edited))
        check('Bodyguard-Musou cached item selections preserved',all(fields(a)['BGMusouEquipItem']['value']==fields(b)['BGMusouEquipItem']['value'] for a,b in zip(original.records('PCSaveDataArray'),edited.records('PCSaveDataArray'))))
        supported=list(save_writer.UNIQUE_WEAPONS.values())
        check('All 84 unique weapons including Ziluan readable',len(supported)==84 and all(
            fields(edited.records('UniqueWeaponDataArray')[w['unique_save_index']])['WeaponID']['value']==w['weapon_enum'] for w in supported))
        allowed={'PCSaveDataArray','EquipItemDataArray','WeaponDataArray','UniqueWeaponDataArray','CollectedWeaponDataArray','GuardDataArray','GuardEquipItemDataArray','GuardWeaponDataArray'}
        for before in weapon.states(original):
            after=weapon.state(edited,before['data_id'])
            check(f'Weapon copy {before["data_id"]} maximum existing bonuses preserved properties',after['skills']==weapon.max_existing_skills(original,before['data_id']) and after['attr']==before['attr'] and after['weapon_id']==before['weapon_id'])
        check('Officer equipped weapon references preserved',all(fields(a)['WeaponDataID']['value']==fields(b)['WeaponDataID']['value'] for a,b in zip(original.records('PCSaveDataArray'),edited.records('PCSaveDataArray'))))
        check('Every other top-level property payload preserved',all(payload(original,p)==payload(edited,edited.properties[name]) for name,p in original.properties.items() if name not in allowed))
        check('Edited save reserializes exactly',save_writer.serialize(edited)[0]==edited.encrypted)
        check('Byte-change report created',len(list(output.glob('edited.sav.*.changes.json')))==1)
        editor.stage_many([Change('officer',0,'Attack',149)])
        editor.save_changes()
        check('Confirmed replace backs up prior edited bytes',any(p.read_bytes()==edited.encrypted for p in (output/'DW3EditorBackups').glob('*.sav')) and fields(read_save(edited_path).records('PCSaveDataArray')[0])['Attack']['value']==149)
        replace(gui.filedialog,'askopenfilename',lambda *args,**kwargs:str(first_backup))
        restored_path=output/'restored.sav'
        replace(gui.filedialog,'asksaveasfilename',lambda *args,**kwargs:str(restored_path))
        editor.restore()
        check('Actual Restore callback restores original to new copy',restored_path.read_bytes()==original.encrypted)
        editor.unlock_everything()
        combined,_=save_writer.serialize(editor.document,list(editor.changes.values()))
        all_unlocked=parse_bytes(combined)
        check('Unlock Everything enables only supported officer/stage flags',all_unlocked.properties['CanUseCharaArray']['value']['values'][:42]==[1]*42 and all_unlocked.properties['CanUseScenarioArray']['value']['values'][:108]==[1]*108 and all_unlocked.properties['CanUseScenarioArray']['value']['values'][108:]==original.properties['CanUseScenarioArray']['value']['values'][108:])
        check('Unlock Everything preserves story completion',all_unlocked.properties['ClearScenarioArray']['value']==original.properties['ClearScenarioArray']['value'] and all_unlocked.properties['EngiClearCharaArray']['value']==original.properties['EngiClearCharaArray']['value'])
        editor.discard()
        replace(gui,'read_save',lambda path:(_ for _ in ()).throw(OSError('Simulated postcommit reopen failure')))
        editor.stage_many([Change('officer',0,'Attack',150)])
        after_warning=output/'saved-with-reopen-warning.sav'
        editor.save_to(after_warning)
        check('Postcommit reopen failure is reported as saved',after_warning.exists() and editor.document is None and not editor.changes and warnings and editor.status.get().startswith('Saved'))
        check('No save failures reported',not errors)
        check('Input working copy remains byte-identical',copy.read_bytes()==original.encrypted)
        report['success']=True
    except Exception:
        report['success']=False
        report['error']=traceback.format_exc()
    finally:
        for (owner,name),value in saved_dialogs.items():setattr(owner,name,value)
        report['fixture_sha256']=original_hash
        report['fixture_unchanged']=hashlib.sha256(fixture.read_bytes()).hexdigest()==original_hash
        report['errors']=errors;report['warnings']=warnings
        if not report['fixture_unchanged']:report['success']=False
        (output/'self-test-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not report['success']:raise RuntimeError(report.get('error','Self-test failed'))
    return True
