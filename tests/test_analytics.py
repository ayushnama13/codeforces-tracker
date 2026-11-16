import json
import pandas as pd
import pytest
import analytics as a
from state_store import StateStore

def test_parse():
    assert a.parse_problem_id('1784D2')==(1784,'D2')
    assert a.parse_problem_id(' 2000a ')==(2000,'A')
    with pytest.raises(ValueError):a.parse_problem_id('bad')

def test_states_and_summary(subs,info):
    states=a.problem_states(subs)
    assert '2189C1' in states
    s=a.summary(subs,info,1789154972)
    assert s['submissions']==len(subs) and isinstance(s['current_streak'],int)
    assert json.dumps(s)

def test_calendar(subs):
    cal=a.activity_calendar(subs,1789154972,days=371)
    assert len(cal)==371
    assert sum(x['submissions'] for x in cal)==sum(1 for s in subs if cal[0]['date'] <= a._date(s['creationTimeSeconds'],'Asia/Kolkata').isoformat() <= cal[-1]['date'])

def test_weak_tags():
    subs=[]
    for i,(idx,verdict) in enumerate([('A','OK'),('B','WRONG_ANSWER'),('C','OK')]):
        subs.append({'id':i,'creationTimeSeconds':100+i,'problem':{'contestId':1,'index':idx,'tags':['dp'],'rating':1200},'author':{},'verdict':verdict})
    assert a.weak_tags(subs,3)==[{'tag':'dp','attempted':3,'solved':2,'solve_rate':.667,'avg_rating_solved':1200,'max_rating_solved':1200}]

def test_heatmap_recommend(subs,problems_path):
    df=a.load_problems(problems_path)
    h=a.heatmap(df,subs,'letter')
    assert len(h['cells'])==len(h['rows'])
    assert all(len(row)==len(h['cols']) for row in h['cells'])
    assert all(c['solved']+c['attempted']+c['unseen']==c['total'] for row in h['cells'] for c in row)
    assert a.heatmap(df,subs,'letter',divisions=['nothing'])=={'rows':[],'cols':[],'cells':[]}
    r=a.recommend(df,subs,1476,1789154972,hidden=['2194A'])
    assert r==a.recommend(df,subs,1476,1789154972,hidden=['2194A'])
    states=a.problem_states(subs)
    solved={k for k,v in states.items() if v['status']=='solved'}
    for tier,lo,hi in [('comfortable',1300,1500),('stretch',1501,1700),('hard',1701,1900)]:
        assert r[tier], tier
        for p in r[tier]: assert lo<=p['rating']<=hi and p['id'] not in solved
    assert all(p['id']!='2194A' for v in r.values() for p in v)

def test_misc_public_json(subs,rating,info,problems_path,tmp_path):
    df=a.load_problems(problems_path)
    values=[a.problem_states(subs),a.summary(subs,info,1789154972),a.activity_calendar(subs,1789154972,days=10),a.rating_history(rating),a.contest_history(rating,subs,df),a.weak_tags(subs,1),a.heatmap(df,subs,'tag'),a.recommend(df,subs,1476,1789154972),a.upsolve_queue(df,subs,1476),a.ladders(df,subs,2)]
    for x in values:json.dumps(x)
    q=a.upsolve_queue(df,subs,1476)
    expected={k for k,v in a.problem_states(subs).items() if v['status']=='attempted'}
    assert expected <= {x['id'] for x in q}

def test_daily_detail_review(subs,problems_path,tmp_path):
    df=a.load_problems(problems_path); store=StateStore(tmp_path,'testuser')
    # daily pick stable after solving the chosen item
    pick=a.daily_pick(df,[],1476,1789154972,'Asia/Kolkata',store)
    assert pick['problem'] is not None
    if True:
        assert a.daily_pick(df,[],1476,1789154972,'Asia/Kolkata',store)['problem']==pick['problem']
        key=pick['problem']; synthetic={'id':1,'creationTimeSeconds':1789155000,'problem':{'contestId':key['contestId'],'index':key['index'],'name':key['name'],'tags':key['tags'],'rating':key['rating']},'author':{},'verdict':'OK'}
        assert a.daily_pick(df,[synthetic],1476,1789154972,'Asia/Kolkata',store)['done']
    hand=[]
    for i,(t,v) in enumerate([(100,'WRONG_ANSWER'),(400,'WRONG_ANSWER'),(700,'OK')]):
        hand.append({'id':i,'creationTimeSeconds':t,'problem':{'contestId':8,'index':'C1','name':'x','tags':['dp'],'rating':1500},'author':{'participantType':'PRACTICE'},'verdict':v})
    d=a.problem_detail(hand,df,8,'C1')
    assert d['tries']==3 and d['minutes_to_ac']==10
    st=StateStore(tmp_path,'reviewer'); st.mark_revise('8C1')
    for i in range(3):st.mark_reviewed('8C1',100+i*86400)
    assert a.review_queue(hand,st,200000)['mastered']==1
    st.hide('8C1'); assert not a.review_queue(hand,st,200000)['due']
    assert json.dumps(d)
