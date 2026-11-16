import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import config

def valid_handle(h): return bool(re.fullmatch(r"[A-Za-z0-9_.-]{3,24}",str(h)))
def _id(cid,idx): return f"{int(cid)}{str(idx).upper()}"
def _ts(v):
    """ISO string -> unix seconds; naive strings were written in local time by the old app."""
    d=datetime.fromisoformat(v.replace("Z","+00:00"))
    if d.tzinfo is None: d=d.replace(tzinfo=ZoneInfo(config.TIMEZONE))
    return int(d.timestamp())
def _defaults(): return {"backlog":[],"hidden":[],"revise":[],"reviews":{},"daily":{}}
class StateStore:
    def __init__(self,base_dir="state",handle=None,legacy_paths=None):
        handle=handle or config.HANDLE
        if not valid_handle(handle): raise ValueError("invalid Codeforces handle")
        self.handle=handle; self.base_dir=Path(base_dir); self.path=self.base_dir/f"{handle.lower()}.json"; self.data=_defaults()
        self.legacy_paths=legacy_paths or {"backlog":Path("revision_problems.json"),"hidden":Path("hidden_revision.json"),"reviews":Path("review_log.json")}
        self.base_dir.mkdir(parents=True,exist_ok=True)
        if self.path.exists():self.load()
        elif handle.lower()==config.HANDLE.lower():self._migrate()
    def load(self):
        with self.path.open(encoding="utf-8") as f:self.data={**_defaults(),**json.load(f)}
        return self.data
    def save(self):
        self.base_dir.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(dir=self.base_dir,prefix=self.path.name,suffix=".tmp")
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(self.data,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)
    def _migrate(self):
        paths=self.legacy_paths
        if Path(paths["backlog"]).exists():
            seen=set()
            for p in json.loads(Path(paths["backlog"]).read_text()):
                item=dict(p);item["id"]=_id(item["contestId"],item["index"])
                if item["id"] in seen: continue
                seen.add(item["id"])
                for k in ("added_on","last_solved"):
                    if isinstance(item.get(k),str): item[k]=_ts(item[k])
                self.data["backlog"].append(item)
        if Path(paths["hidden"]).exists():self.data["hidden"]=[_id(*x) for x in json.loads(Path(paths["hidden"]).read_text())]
        if Path(paths["reviews"]).exists():
            source=json.loads(Path(paths["reviews"]).read_text())
            for key,vals in source.items():
                cid,idx=re.match(r"^(\d+)([A-Za-z][0-9]?)$",key).groups()
                self.data["reviews"][_id(cid,idx)]=[_ts(v) for v in vals]
        self.save()
    def add_backlog(self,problem):
        item=dict(problem);item.setdefault("id",_id(item["contestId"],item["index"]));self.remove_backlog(item["id"]);self.data["backlog"].append(item);self.save()
    def remove_backlog(self,id): self.data["backlog"]=[p for p in self.data["backlog"] if p.get("id")!=id];self.save()
    def hide(self,id):
        if id not in self.data["hidden"]:self.data["hidden"].append(id)
        self.save()
    def mark_revise(self,id):
        if id not in self.data["revise"]:self.data["revise"].append(id)
        self.save()
    def unmark_revise(self,id):self.data["revise"]=[x for x in self.data["revise"] if x!=id];self.save()
    def mark_reviewed(self,id,now):self.data["reviews"].setdefault(id,[]).append(int(now));self.save()
    def get_daily(self,date):return self.data["daily"].get(date)
    def set_daily(self,date,item):self.data["daily"][date]=dict(item);self.save()
