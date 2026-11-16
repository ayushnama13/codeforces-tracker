import math
import random
import re
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

import config

DEFAULT_RATING = 1200  # used for unrated handles
RATING_BANDS = ["800-1000", "1100-1300", "1400-1600", "1700-1900", "2000-2200", "2300-2500", "2600+"]
RANK_BANDS = [
    {"name": "newbie", "min": 0, "max": 1199, "color": "gray"},
    {"name": "pupil", "min": 1200, "max": 1399, "color": "green"},
    {"name": "specialist", "min": 1400, "max": 1599, "color": "cyan"},
    {"name": "expert", "min": 1600, "max": 1899, "color": "blue"},
    {"name": "candidate master", "min": 1900, "max": 2099, "color": "violet"},
    {"name": "master", "min": 2100, "max": 2299, "color": "orange"},
    {"name": "international master", "min": 2300, "max": 2399, "color": "orange"},
    {"name": "grandmaster", "min": 2400, "max": 2599, "color": "red"},
    {"name": "international grandmaster", "min": 2600, "max": 2999, "color": "red"},
    {"name": "legendary grandmaster", "min": 3000, "max": None, "color": "red"},
]

def parse_problem_id(s):
    m = re.match(r"^\s*(\d+)\s*([A-Za-z][0-9]?)\s*$", str(s))
    if not m:
        raise ValueError(f"invalid problem id: {s}")
    return int(m.group(1)), m.group(2).upper()

def _pid(cid, idx): return f"{int(cid)}{str(idx).upper()}"
def _json_num(v):
    if pd.isna(v): return None
    return int(v) if float(v).is_integer() else float(v)
def load_problems(path):
    df = pd.read_csv(path, dtype={"problemIndex": str})
    if "solvedCount" not in df: df["solvedCount"] = 0
    df["contestId"] = pd.to_numeric(df["contestId"], errors="coerce")
    df["rating"] = pd.to_numeric(df.get("rating"), errors="coerce")
    df["startTime"] = pd.to_numeric(df.get("startTime"), errors="coerce")
    df["solvedCount"] = pd.to_numeric(df["solvedCount"], errors="coerce").fillna(0).astype(int)
    df["letter"] = df["problemIndex"].fillna("").astype(str).str[0].str.upper()
    df["tags"] = df["tags"].fillna("").astype(str).map(lambda x: [t for t in x.split(";") if t])
    df = df[df["contestId"].notna()].copy()
    df["contestId"] = df["contestId"].astype(int)
    df["id"] = df["contestId"].astype(str) + df["problemIndex"].astype(str).str.upper()
    return df

def _status_series(df, states):
    """'solved' / 'attempted' / 'unseen' for every row of a problems frame."""
    return df["id"].map(lambda k: states[k]["status"] if k in states else "unseen")

def problem_states(subs):
    grouped = defaultdict(list)
    for s in subs:
        p=s.get("problem") or {}; cid=p.get("contestId")
        if cid is None: continue
        key=_pid(cid,p.get("index", "")); grouped[key].append(s)
    out={}
    for key, items in grouped.items():
        items=sorted(items,key=lambda x:x.get("creationTimeSeconds",0))
        ok_idx=next((i for i,s in enumerate(items) if s.get("verdict")=="OK"),None)
        p=items[0].get("problem",{}); first=items[0].get("creationTimeSeconds")
        ok=items[ok_idx] if ok_idx is not None else None
        out[key]={"contestId":int(p["contestId"]),"index":str(p["index"]).upper(),"name":p.get("name",""),"rating":_json_num(p.get("rating")),"tags":list(p.get("tags") or []),"status":"solved" if ok else "attempted","tries":ok_idx+1 if ok else len(items),"first_ts":int(first) if first is not None else None,"first_ok_ts":int(ok.get("creationTimeSeconds")) if ok else None,"last_ts":int(items[-1].get("creationTimeSeconds",0)),"solved_in_contest":bool(ok and (ok.get("author") or {}).get("participantType")=="CONTESTANT"),"participated_contest":any((s.get("author") or {}).get("participantType") in ("CONTESTANT","OUT_OF_COMPETITION") for s in items)}
    return out

def _date(ts,tz): return datetime.fromtimestamp(int(ts),ZoneInfo(tz)).date()
def summary(subs, info, now, tz=config.TIMEZONE):
    dates={_date(s["creationTimeSeconds"],tz) for s in subs if s.get("creationTimeSeconds") is not None}
    today=_date(now,tz); anchor=today if today in dates else today-timedelta(days=1); streak=0
    while anchor in dates: streak+=1; anchor-=timedelta(days=1)
    longest=run=0; prev=None
    for d in sorted(dates):
        run=run+1 if prev and d==prev+timedelta(days=1) else 1; longest=max(longest,run); prev=d
    states=problem_states(subs)
    return {"handle":info.get("handle"),"rating":info.get("rating"),"maxRating":info.get("maxRating"),"rank":info.get("rank"),"maxRank":info.get("maxRank"),"solved":sum(s["status"]=="solved" for s in states.values()),"attempted_unsolved":sum(s["status"]=="attempted" for s in states.values()),"submissions":len(subs),"current_streak":streak,"longest_streak":longest}

def activity_calendar(subs,now,tz=config.TIMEZONE,days=371):
    end=_date(now,tz); start=end-timedelta(days=days-1); counts=defaultdict(lambda:[0,0]); solved_at={}
    for s in subs:
        ts=s.get("creationTimeSeconds"); p=s.get("problem") or {}
        if ts is None: continue
        d=_date(ts,tz)
        if start<=d<=end: counts[d][0]+=1
        if s.get("verdict")=="OK" and p.get("contestId") is not None:
            key=_pid(p["contestId"],p.get("index","")); solved_at[key]=min(solved_at.get(key,ts),ts)
    for ts in solved_at.values():
        d=_date(ts,tz)
        if start<=d<=end: counts[d][1]+=1
    return [{"date":(start+timedelta(days=i)).isoformat(),"submissions":counts[start+timedelta(days=i)][0],"solved":counts[start+timedelta(days=i)][1]} for i in range(days)]

def rating_history(rating):
    return [{"contestId":int(x["contestId"]),"contestName":x.get("contestName",""),"time":int(x["ratingUpdateTimeSeconds"]),"rank":int(x["rank"]),"oldRating":int(x["oldRating"]),"newRating":int(x["newRating"]),"delta":int(x["newRating"])-int(x["oldRating"])} for x in rating]

def contest_history(rating,subs,problems_df):
    states=problem_states(subs); rows=[]
    for x in rating:
        cid=int(x["contestId"]); subset=problems_df[problems_df.contestId==cid]; solved=0; up=0
        for _,p in subset.iterrows():
            s=states.get(_pid(cid,p.problemIndex))
            if s and s["status"]=="solved":
                if s["solved_in_contest"]: solved+=1
                elif s["first_ok_ts"] and s["first_ok_ts"]>int(x["ratingUpdateTimeSeconds"]): up+=1
        rows.append({"contestId":cid,"contestName":x.get("contestName",""),"division":subset.iloc[0].get("division","") if len(subset) else "","time":int(x["ratingUpdateTimeSeconds"]),"rank":int(x["rank"]),"delta":int(x["newRating"])-int(x["oldRating"]),"newRating":int(x["newRating"]),"solved_in_contest":solved,"upsolved_later":up,"total_problems":int(len(subset))})
    return sorted(rows,key=lambda r:r["time"],reverse=True)

def weak_tags(subs,min_attempted=3):
    states=problem_states(subs); agg=defaultdict(lambda:[set(),set(),[]])
    for k,s in states.items():
        for t in s["tags"]:
            agg[t][0].add(k)
            if s["status"]=="solved": agg[t][1].add(k); agg[t][2].append(s["rating"])
    out=[]
    for t,(attempted,solved,ratings) in agg.items():
        if len(attempted)<min_attempted: continue
        vals=[int(x) for x in ratings if x is not None]
        out.append({"tag":t,"attempted":len(attempted),"solved":len(solved),"solve_rate":round(len(solved)/len(attempted),3),"avg_rating_solved":round(sum(vals)/len(vals)) if vals else None,"max_rating_solved":max(vals) if vals else None})
    return sorted(out,key=lambda x:(x["solve_rate"],-x["attempted"],x["tag"]))

def _band(r):
    if r<1100:return "800-1000"
    if r<1400:return "1100-1300"
    if r<1700:return "1400-1600"
    if r<2000:return "1700-1900"
    if r<2300:return "2000-2200"
    if r<2600:return "2300-2500"
    return "2600+"
def heatmap(problems_df,subs,axis,last_n_contests=None,divisions=None):
    if axis not in ("letter","tag"): raise ValueError("axis must be 'letter' or 'tag'")
    df=problems_df[problems_df.rating.notna()]
    if divisions is not None: df=df[df.division.isin(divisions)]
    if last_n_contests is not None:
        cs=df.groupby("contestId").startTime.max().sort_values(ascending=False).head(last_n_contests).index; df=df[df.contestId.isin(cs)]
    if df.empty: return {"rows":[],"cols":[],"cells":[]}
    df=df.assign(status=_status_series(df,problem_states(subs)))
    if axis=="letter":
        df=df.assign(row=df.letter,col=(df.rating//100*100).astype(int))
        cols=sorted(df.col.unique().tolist())
    else:
        df=df.assign(row=df.tags,col=df.rating.map(_band)).explode("row").dropna(subset=["row"])
        cols=list(RATING_BANDS)
    counts=df.groupby(["row","col","status"]).size()
    totals=df.groupby("row").size()
    rows=sorted(totals.index.tolist()) if axis=="letter" else sorted(totals.index.tolist(),key=lambda t:(-int(totals[t]),t))
    get=lambda r,c,st:int(counts.get((r,c,st),0))
    cells=[[{"total":get(r,c,"solved")+get(r,c,"attempted")+get(r,c,"unseen"),"solved":get(r,c,"solved"),"attempted":get(r,c,"attempted"),"unseen":get(r,c,"unseen")} for c in cols] for r in rows]
    return {"rows":[str(r) for r in rows],"cols":cols,"cells":cells}

def _item(p,states=None):
    cid=int(p.contestId); idx=str(p.problemIndex); rating=_json_num(p.rating); tags=list(p.tags); sc=int(p.solvedCount)
    return {"id":_pid(cid,idx),"contestId":cid,"index":idx,"name":p.problemName,"rating":rating,"tags":tags,"solvedCount":sc,"url":f"https://codeforces.com/contest/{cid}/problem/{idx}"}
def recommend(problems_df,subs,user_rating,now,hidden=(),per_tier=5,tz=config.TIMEZONE):
    user_rating=user_rating or DEFAULT_RATING
    df=problems_df[problems_df.rating.notna()].copy(); states=problem_states(subs); hidden=set(hidden); weakest={x["tag"]:x["solve_rate"] for x in weak_tags(subs)[:3]}; r=int(round(user_rating/100)*100); tiers={"comfortable":[],"stretch":[],"hard":[]}
    solved={k for k,v in states.items() if v["status"]=="solved"}
    eligible=df[~df["id"].isin(solved|hidden)]
    for tier,(lo,hi,inc) in {"comfortable":(r-200,r,True),"stretch":(r+1,r+200,True),"hard":(r+201,r+400,True)}.items():
        cand=eligible[(eligible.rating>=lo)&(eligible.rating<=hi)].copy()
        maxsc=max(cand.solvedCount) if len(cand) else 1; rng=random.Random(_date(now,tz).isoformat())
        starts=cand.startTime.fillna(0).astype(float) if len(cand) else pd.Series(dtype=float)
        newest=float(starts.max()) if len(starts) else 0
        oldest=float(starts.min()) if len(starts) else 0
        records=[]
        for _,p in cand.iterrows():
            item=_item(p); score=2*sum(t in weakest for t in item["tags"])+(item["solvedCount"]/maxsc if maxsc else 0)
            recency=(float(p.startTime or 0)-oldest)/(newest-oldest) if newest>oldest else 0
            score+=0.1*recency
            records.append((score,rng.random(),item))
        records.sort(key=lambda a:(-a[0],a[1],a[2]["id"]))
        for score,_,item in records[:per_tier]:
            matching=[t for t in item["tags"] if t in weakest]
            item["reason"]=(f"{matching[0]} is one of your weakest tags ({weakest[matching[0]]:.0%} of tried problems solved); {item['rating']-user_rating:+g} vs your rating" if matching else f"Rated {item['rating']}, {item['rating']-user_rating:+g} vs your rating")
            tiers[tier].append(item)
    return tiers

def daily_pick(problems_df,subs,user_rating,now,tz,store,hidden=()):
    user_rating=user_rating or DEFAULT_RATING
    date=_date(now,tz).isoformat(); existing=store.get_daily(date)
    if existing is not None: item=existing
    else:
        rec=recommend(problems_df,subs,user_rating,now,hidden,tz=tz); picks=rec["stretch"] or rec["comfortable"]; item=picks[0] if picks else None
        if item is not None: store.set_daily(date,item)
    if item is None:return {"date":date,"problem":None,"done":False}
    start=int(datetime.combine(_date(now,tz),datetime.min.time(),tzinfo=ZoneInfo(tz)).timestamp())
    state=problem_states(subs).get(item["id"]); done=bool(state and state["first_ok_ts"] is not None and state["first_ok_ts"]>=start)
    return {"date":date,"problem":item,"done":done}

def daily_history(store,subs):
    states=problem_states(subs); result=[]
    for date, item in sorted(store.data.get("daily",{}).items(),reverse=True):
        result.append({"date":date,"id":item.get("id"),"done":bool(states.get(item.get("id"),{}).get("first_ok_ts") and states[item["id"]]["first_ok_ts"]>=int(datetime.fromisoformat(date).replace(tzinfo=ZoneInfo(config.TIMEZONE)).timestamp()))})
    return result

def upsolve_queue(problems_df,subs,user_rating):
    user_rating=user_rating or DEFAULT_RATING
    states=problem_states(subs); out=[]
    last_verdict={}
    for sub in subs:
        p=sub.get("problem") or {}
        if p.get("contestId") is not None:
            key=_pid(p["contestId"],p.get("index",""))
            if key not in last_verdict or sub.get("creationTimeSeconds",0)>=last_verdict[key][0]:
                last_verdict[key]=(sub.get("creationTimeSeconds",0),sub.get("verdict"))
    for key,s in states.items():
        if s["status"]!="attempted":continue
        out.append({"id":key,"contestId":s["contestId"],"index":s["index"],"name":s["name"],"rating":s["rating"],"tags":s["tags"],"url":f"https://codeforces.com/contest/{s['contestId']}/problem/{s['index']}","source":"attempted","tries":s["tries"],"last_ts":s["last_ts"],"last_verdict":last_verdict.get(key,(0,None))[1]})
    participated={s["contestId"] for s in states.values() if s["participated_contest"]}
    for _,p in problems_df[problems_df.contestId.isin(participated)].iterrows():
        key=_pid(p.contestId,p.problemIndex)
        if key in states:continue
        if pd.notna(p.rating) and p.rating>user_rating+300:continue
        out.append({"id":key,"contestId":int(p.contestId),"index":str(p.problemIndex),"name":p.problemName,"rating":_json_num(p.rating),"tags":list(p.tags),"url":f"https://codeforces.com/contest/{int(p.contestId)}/problem/{p.problemIndex}","source":"contest","tries":0,"last_ts":int(p.startTime) if pd.notna(p.startTime) else 0,"last_verdict":None})
    return sorted(out,key=lambda x:(0,-x["last_ts"]) if x["source"]=="attempted" else (1,-x["last_ts"]))

def ladders(problems_df,subs,size=40):
    states=problem_states(subs); out=[]
    for band in range(800,3501,100):
        df=problems_df[problems_df.rating==band].sort_values(["solvedCount","contestId"],ascending=[False,False]).head(size)
        items=[]
        for _,p in df.iterrows():
            item=_item(p); item.pop("solvedCount"); item["solvedCount"]=int(p.solvedCount); item["solved"]=states.get(item["id"],{}).get("status")=="solved"; items.append(item)
        total=int((problems_df.rating==band).sum()); solved=sum(1 for p in problems_df[problems_df.rating==band].itertuples() if states.get(_pid(p.contestId,p.problemIndex),{}).get("status")=="solved")
        out.append({"band":band,"total":total,"solved":solved,"problems":items})
    return out

def problem_detail(subs,problems_df,contest_id,index):
    key=_pid(contest_id,index); state=problem_states(subs).get(key)
    if state is None:raise KeyError(key)
    matches=problems_df[(problems_df.contestId==int(contest_id))&(problems_df.problemIndex.astype(str).str.upper()==str(index).upper())]
    p=matches.iloc[0] if len(matches) else None
    items=sorted([s for s in subs if (s.get("problem") or {}).get("contestId")==int(contest_id) and str((s.get("problem") or {}).get("index","")).upper()==str(index).upper()],key=lambda s:s.get("creationTimeSeconds",0))
    ts=state["first_ts"]; ok=state["first_ok_ts"]
    return {"id":key,"name":state["name"],"rating":_json_num(p.rating) if p is not None else state["rating"],"tags":list(p.tags) if p is not None else state["tags"],"url":f"https://codeforces.com/contest/{int(contest_id)}/problem/{str(index).upper()}","status":state["status"],"tries":state["tries"],"first_ts":ts,"first_ok_ts":ok,"minutes_to_ac":(ok-ts)//60 if ok is not None else None,"solved_in_contest":state["solved_in_contest"],"submissions":[{"id":int(s["id"]),"time":int(s["creationTimeSeconds"]),"verdict":s.get("verdict"),"participantType":(s.get("author") or {}).get("participantType"),"passedTestCount":int(s.get("passedTestCount",0)),"language":s.get("programmingLanguage")} for s in items]}

REVIEW_INTERVALS_DAYS=[7,30,90]
HARD_TRIES=4  # 3+ failed submissions before the first AC
def review_queue(subs,store,now,tz=config.TIMEZONE,daily_cap=10):
    states=problem_states(subs); items={}
    for p in store.data.get("backlog",[]): items[p.get("id")]=("backlog",p)
    for key in store.data.get("revise",[]): items.setdefault(key,("revise",{}))
    for key,s in states.items():
        if s["status"]=="solved" and s["tries"]>=HARD_TRIES:items.setdefault(key,("hard",s))
    due=[]; upcoming=0; mastered=0; hidden=set(store.data.get("hidden",[])); today=_date(now,tz)
    for key,(source,p) in items.items():
        if key in hidden:continue
        reviews=store.data.get("reviews",{}).get(key,[])
        if len(reviews)>=len(REVIEW_INTERVALS_DAYS):mastered+=1;continue
        s=states.get(key,{})
        added=p.get("added_on")
        if isinstance(added,str):
            try: added=datetime.fromisoformat(added).replace(tzinfo=None).replace(tzinfo=ZoneInfo(tz)).timestamp()
            except ValueError: added=None
        # The clock starts at the most recent touch: latest submission or the day it was added.
        candidates=[x for x in (s.get("last_ts"),added) if x is not None]
        if not candidates: continue
        base=max(candidates)
        base=int(reviews[-1]) if reviews else int(base)
        interval=REVIEW_INTERVALS_DAYS[len(reviews)]
        due_ts=base+interval*86400
        due_day=_date(due_ts,tz); overdue=max(0,(today-due_day).days)
        if due_ts>now:upcoming+=1;continue
        due.append({"id":key,"name":p.get("name",s.get("name","")),"rating":p.get("rating",s.get("rating")),"tags":p.get("tags",s.get("tags",[])),"url":p.get("url",f"https://codeforces.com/contest/{s.get('contestId',0)}/problem/{s.get('index','')}"),"source":source,"due_date":due_day.isoformat(),"overdue_days":overdue,"reviews_done":len(reviews)})
    due.sort(key=lambda x:(-x["overdue_days"],x["due_date"],x["id"]))
    return {"due":due[:daily_cap],"upcoming":upcoming,"mastered":mastered}
