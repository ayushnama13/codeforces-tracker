import csv
import json
import time
import cf_api

def test_refresh(tmp_path):
    path=tmp_path/'problems.csv';path.write_text('old')
    path.touch(); import os; os.utime(path,(0,0))
    assert cf_api.refresh_problems_csv(path,get=lambda _:(_ for _ in ()).throw(RuntimeError('offline'))) == {'refreshed':False,'reason':'offline'}
    assert path.read_text()=='old'
    def fake(endpoint):
        if endpoint=='contest.list':return [{'id':1,'name':'Codeforces Round 1 (Div. 2)','phase':'FINISHED','startTimeSeconds':100}]
        return {'problems':[{'contestId':1,'index':'A','name':'A problem','rating':800,'tags':['math']}], 'problemStatistics':[{'contestId':1,'index':'A','solvedCount':42}]}
    result=cf_api.refresh_problems_csv(path,get=fake)
    assert result=={'refreshed':True,'rows':1}
    assert list(csv.DictReader(path.open()))[0]['solvedCount']=='42'

def test_user_cache(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls=[]
    assert cf_api.fetch_user_info('abc',lambda q: calls.append(q) or [{'handle':'abc'}])==({'handle':'abc'},False)
    assert calls==['user.info?handles=abc']
    assert cf_api.fetch_user_info('abc',lambda _: (_ for _ in ()).throw(RuntimeError('offline')))==({'handle':'abc'},True)
