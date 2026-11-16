import json
import pytest
from state_store import StateStore

def test_round_trip_and_invalid(tmp_path):
    with pytest.raises(ValueError):StateStore(tmp_path,'bad handle')
    s=StateStore(tmp_path,'valid_user');s.add_backlog({'contestId':1784,'index':'D2','name':'x','tags':[]});s.hide('1784D2');s.mark_revise('1784D2');s.mark_reviewed('1784D2',123);s.set_daily('2026-01-01',{'id':'1784D2'})
    z=StateStore(tmp_path,'VALID_USER')
    assert z.data==s.data

def test_legacy_copy(tmp_path):
    files={
      'backlog':tmp_path/'revision_problems.json','hidden':tmp_path/'hidden_revision.json','reviews':tmp_path/'review_log.json'}
    contents={'backlog':[{'name':'x','contestId':1784,'index':'D2','rating':1700,'tags':['dp'],'url':'u','added_on':100}], 'hidden':[[1784,'D2']], 'reviews':{'1784D2':['2025-01-01T00:00:00Z']}}
    before={}
    for k,p in files.items():p.write_text(json.dumps(contents[k]));before[k]=p.read_bytes()
    s=StateStore(tmp_path/'state','Ayushanma',legacy_paths=files)
    assert s.data['backlog'][0]['id']=='1784D2' and s.data['hidden']==['1784D2'] and s.data['reviews']['1784D2']==[1735689600]
    assert all(files[k].read_bytes()==before[k] for k in files)
