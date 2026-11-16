import csv
import time
import json
import os
import tempfile
from pathlib import Path

import requests

BASE="https://codeforces.com/api"
def _default_get(path):
    response=requests.get(f"{BASE}/{path}",timeout=30);response.raise_for_status();data=response.json()
    if data.get("status")!="OK":raise RuntimeError(data.get("comment","Codeforces API error"))
    return data["result"]
def _fetch(handle,kind,get):
    cache=Path("cache")/f"{handle.lower()}_{kind}.json"
    try:
        if kind=="info": data=get(f"user.info?handles={handle}")[0]
        else: data=get(f"user.{kind}?handle={handle}")
        cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(json.dumps(data),encoding="utf-8")
        return data,False
    except Exception:
        if cache.exists():return json.loads(cache.read_text(encoding="utf-8")),True
        raise
def fetch_user_status(handle,get=_default_get):return _fetch(handle,"status",get)
def fetch_user_rating(handle,get=_default_get):return _fetch(handle,"rating",get)
def fetch_user_info(handle,get=_default_get):return _fetch(handle,"info",get)
def refresh_problems_csv(path="codeforces_all_problems.csv",max_age_hours=24,get=_default_get):
    target=Path(path)
    if target.exists() and ( time.time()-target.stat().st_mtime < max_age_hours*3600):return {"refreshed":False,"reason":"fresh"}
    try:
        from fetch_all_problems import division
        contests={c["id"]:c for c in get("contest.list")}; result=get("problemset.problems")
        stats={(x["contestId"],x["index"]):x.get("solvedCount",0) for x in result.get("problemStatistics",[])}
        rows=[]
        for p in result["problems"]:
            c=contests.get(p["contestId"],{}); name=c.get("name","")
            rows.append({"contestId":p.get("contestId"),"contestName":name,"division":division(name),"phase":c.get("phase",""),"startTime":c.get("startTimeSeconds",""),"problemIndex":p.get("index",""),"problemName":p.get("name",""),"rating":p.get("rating",""),"tags":";".join(p.get("tags",[])),"solvedCount":stats.get((p.get("contestId"),p.get("index")),0)})
        fields=["contestId","contestName","division","phase","startTime","problemIndex","problemName","rating","tags","solvedCount"]
        target.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(dir=target.parent,prefix=target.name,suffix=".tmp",text=True)
        try:
            with os.fdopen(fd,"w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            os.replace(name,target)
        finally:
            if os.path.exists(name):os.unlink(name)
        return {"refreshed":True,"rows":len(rows)}
    except Exception as e:return {"refreshed":False,"reason":str(e)}
