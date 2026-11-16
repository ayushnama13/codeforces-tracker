import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import analytics
import cf_api
import config
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from state_store import StateStore, valid_handle

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATE_DIR = BASE_DIR / "state"
PROBLEMS_CSV = BASE_DIR / "codeforces_all_problems.csv"
BUNDLE_TTL = 600
_bundles = {}
_problems_lock = threading.Lock()
_problems_mtime = None
problems_df = None


def _reload_problems():
    """Load the problems CSV on first use and again whenever its mtime changes."""
    global problems_df, _problems_mtime
    try:
        mtime = PROBLEMS_CSV.stat().st_mtime
    except OSError:
        mtime = None
    if mtime is not None and mtime != _problems_mtime:
        with _problems_lock:
            if mtime != _problems_mtime:
                problems_df = analytics.load_problems(PROBLEMS_CSV)
                _problems_mtime = mtime
    if problems_df is None:
        raise HTTPException(status_code=503, detail="problem list not downloaded yet; try again in a minute")


@asynccontextmanager
async def lifespan(app):
    threading.Thread(target=cf_api.refresh_problems_csv, args=(str(PROBLEMS_CSV),), daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)


def _handle(handle):
    if not valid_handle(handle):
        raise HTTPException(status_code=400, detail="invalid handle")
    return handle


def _store(handle):
    return StateStore(base_dir=STATE_DIR, handle=handle)


def _bundle(handle, force=False):
    _reload_problems()
    key = handle.lower()
    current = _bundles.get(key)
    now = time.time()
    if current and not force and now - current["loaded_at"] < BUNDLE_TTL:
        return current
    try:
        subs, stale_subs = cf_api.fetch_user_status(handle)
        rating, stale_rating = cf_api.fetch_user_rating(handle)
        info, stale_info = cf_api.fetch_user_info(handle)
    except cf_api.HandleNotFound as exc:
        raise HTTPException(status_code=404, detail=f"no Codeforces user called {handle}") from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Codeforces is unreachable and nothing is cached") from exc
    bundle = {"subs": subs, "rating": rating, "info": info,
              "stale": bool(stale_subs or stale_rating or stale_info),
              "loaded_at": int(now)}
    _bundles[key] = bundle
    return bundle


def _meta(handle, bundle):
    try:
        updated = int(PROBLEMS_CSV.stat().st_mtime)
    except OSError:
        updated = None
    return {"handle": handle, "stale": bundle["stale"],
            "loaded_at": bundle["loaded_at"], "problems_rows": len(problems_df),
            "problems_updated": updated}


def _data(handle):
    handle = _handle(handle)
    return handle, _bundle(handle)


def _pid(pid):
    try:
        cid, index = analytics.parse_problem_id(pid)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid problem id") from exc
    return cid, index, f"{cid}{index}"


def _common(handle, bundle):
    now = int(time.time())
    return now, _meta(handle, bundle), bundle["subs"], bundle["rating"], bundle["info"], _store(handle)


@app.get("/api/{handle}/today")
def today(handle: str):
    handle, b = _data(handle)
    now, meta, subs, rating, info, store = _common(handle, b)
    hidden = store.data.get("hidden", [])
    user_rating = info.get("rating")
    reviews = analytics.review_queue(subs, store, now, config.TIMEZONE, daily_cap=10)
    upsolve = analytics.upsolve_queue(problems_df, subs, user_rating)
    return {"meta": meta, "summary": analytics.summary(subs, info, now, config.TIMEZONE),
            "rating_history": analytics.rating_history(rating)[-30:],
            "daily": analytics.daily_pick(problems_df, subs, user_rating, now, config.TIMEZONE, store, hidden),
            "reviews": reviews, "upsolve": upsolve[:10], "upsolve_total": len(upsolve),
            "calendar": analytics.activity_calendar(subs, now, config.TIMEZONE, days=371)}


@app.get("/api/{handle}/practice")
def practice(handle: str, band: int = None):
    handle, b = _data(handle)
    now, meta, subs, rating, info, store = _common(handle, b)
    all_ladders = analytics.ladders(problems_df, subs)
    default = min(3500, max(800, ((info.get("rating") or analytics.DEFAULT_RATING) // 100) * 100))
    by_band = {item["band"]: item for item in all_ladders}
    ladder = by_band.get(band) or by_band.get(default) or (all_ladders[0] if all_ladders else None)
    recommend = analytics.recommend(problems_df, subs, info.get("rating"), now,
                                    hidden=store.data.get("hidden", []), tz=config.TIMEZONE)
    return {"meta": meta, "recommend": recommend,
            "ladders": [{k: item[k] for k in ("band", "total", "solved")} for item in all_ladders],
            "ladder": ladder}


@app.get("/api/{handle}/progress")
def progress(handle: str):
    handle, b = _data(handle)
    now, meta, subs, rating, info, store = _common(handle, b)
    return {"meta": meta, "summary": analytics.summary(subs, info, now, config.TIMEZONE),
            "rating_history": analytics.rating_history(rating), "rank_bands": analytics.RANK_BANDS,
            "calendar": analytics.activity_calendar(subs, now, config.TIMEZONE),
            "contests": analytics.contest_history(rating, subs, problems_df),
            "weak_tags": analytics.weak_tags(subs), "daily_history": analytics.daily_history(store, subs)}


@app.get("/api/{handle}/coverage")
def coverage(handle: str, axis: str = "letter", last_n: int = None, div: list[str] = Query(None)):
    handle, b = _data(handle)
    if axis not in ("letter", "tag"):
        raise HTTPException(status_code=400, detail="bad axis")
    now, meta, subs, rating, info, store = _common(handle, b)
    try:
        heatmap = analytics.heatmap(problems_df, subs, axis, last_n_contests=last_n, divisions=div)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    divisions = sorted(str(x) for x in problems_df["division"].dropna().unique()) if "division" in problems_df else []
    return {"meta": meta, "heatmap": heatmap, "divisions": divisions}


@app.get("/api/{handle}/revision")
def revision(handle: str):
    handle, b = _data(handle)
    now, meta, subs, rating, info, store = _common(handle, b)
    return {"meta": meta, "reviews": analytics.review_queue(subs, store, now, config.TIMEZONE, daily_cap=50),
            "backlog": store.data["backlog"], "hidden": store.data["hidden"], "revise": store.data["revise"]}


@app.get("/api/{handle}/problem/{pid}")
def problem(handle: str, pid: str):
    handle, b = _data(handle)
    cid, index, _ = _pid(pid)
    try:
        return analytics.problem_detail(b["subs"], problems_df, cid, index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="problem not found") from exc


@app.post("/api/{handle}/review/{pid}")
def mark_review(handle: str, pid: str):
    handle = _handle(handle)
    _, _, key = _pid(pid)
    _store(handle).mark_reviewed(key, int(time.time()))
    return {"ok": True}


@app.post("/api/{handle}/hide/{pid}")
def hide(handle: str, pid: str):
    handle = _handle(handle)
    _, _, key = _pid(pid)
    _store(handle).hide(key)
    return {"ok": True}


@app.post("/api/{handle}/revise/{pid}")
def mark_revise(handle: str, pid: str):
    handle = _handle(handle)
    _, _, key = _pid(pid)
    _store(handle).mark_revise(key)
    return {"ok": True}


@app.delete("/api/{handle}/revise/{pid}")
def unmark_revise(handle: str, pid: str):
    handle = _handle(handle)
    _, _, key = _pid(pid)
    _store(handle).unmark_revise(key)
    return {"ok": True}


class BacklogRequest(BaseModel):
    id: str


@app.post("/api/{handle}/backlog")
def add_backlog(handle: str, request: BacklogRequest):
    handle = _handle(handle)
    cid, index, key = _pid(request.id)
    _reload_problems()
    matches = problems_df[(problems_df.contestId == cid) & (problems_df.problemIndex.astype(str).str.upper() == index)]
    if matches.empty:
        raise HTTPException(status_code=404, detail="problem not found")
    p = matches.iloc[0]
    store = _store(handle)
    store.add_backlog({"id": key, "contestId": cid, "index": index, "name": p.problemName,
                       "rating": None if pd.isna(p.rating) else int(p.rating), "tags": list(p.tags),
                       "url": f"https://codeforces.com/contest/{cid}/problem/{index}", "added_on": int(time.time())})
    return {"ok": True}


@app.delete("/api/{handle}/backlog/{pid}")
def remove_backlog(handle: str, pid: str):
    handle = _handle(handle)
    _, _, key = _pid(pid)
    _store(handle).remove_backlog(key)
    return {"ok": True}


@app.post("/api/{handle}/refresh")
def refresh(handle: str):
    handle = _handle(handle)
    _bundles.pop(handle.lower(), None)
    bundle = _bundle(handle)
    return {"meta": _meta(handle, bundle)}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
