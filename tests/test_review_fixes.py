import json
import analytics as a
from state_store import StateStore


def test_migration_iso_dates_and_duplicates(tmp_path):
    files = {"backlog": tmp_path / "b.json", "hidden": tmp_path / "h.json", "reviews": tmp_path / "r.json"}
    item = {"name": "Job Interview", "contestId": 1976, "index": "C", "rating": 1600, "tags": ["dp"],
            "added_on": "2026-01-21T11:18:51.107965", "last_solved": "2026-01-21T11:18:51.107965"}
    files["backlog"].write_text(json.dumps([item, item]))
    files["hidden"].write_text("[]")
    files["reviews"].write_text(json.dumps({"1976C": ["2026-02-01T10:00:00"]}))
    s = StateStore(tmp_path / "state", "ayushanma", legacy_paths=files)
    assert len(s.data["backlog"]) == 1 and isinstance(s.data["backlog"][0]["added_on"], int)
    q = a.review_queue([], s, now=1_800_000_000)
    assert [x["id"] for x in q["due"]] == ["1976C"] and q["due"][0]["reviews_done"] == 1


def test_review_queue_accepts_iso_added_on(tmp_path):
    s = StateStore(tmp_path, "someone")
    s.add_backlog({"contestId": 1, "index": "A", "name": "x", "tags": [], "added_on": "2026-01-01T00:00:00"})
    assert a.review_queue([], s, now=1_800_000_000)["due"][0]["id"] == "1A"


def test_heatmap_matches_brute_force(subs, problems_path):
    df = a.load_problems(problems_path)
    states = a.problem_states(subs)
    hm = a.heatmap(df, subs, "tag")
    rated = df[df.rating.notna()]
    for i, tag in enumerate(hm["rows"]):
        for j, band in enumerate(hm["cols"]):
            rows = rated[rated.tags.map(lambda t: tag in t) & rated.rating.map(lambda r: a._band(r) == band)]
            solved = sum(states.get(k, {}).get("status") == "solved" for k in rows["id"])
            assert hm["cells"][i][j]["total"] == len(rows) and hm["cells"][i][j]["solved"] == solved
    lm = a.heatmap(df, subs, "letter")
    assert sum(c["total"] for r in lm["cells"] for c in r) == len(rated)


def test_unrated_user_and_tries(subs, problems_path):
    df = a.load_problems(problems_path)
    rec = a.recommend(df, subs, None, now=1_800_000_000)
    assert all(1000 <= x["rating"] <= 1600 for t in rec.values() for x in t)
    assert a.upsolve_queue(df, subs, None)
    st = a.problem_states([
        {"creationTimeSeconds": 1, "verdict": "WRONG_ANSWER", "problem": {"contestId": 5, "index": "B", "name": "n"}, "author": {}},
        {"creationTimeSeconds": 2, "verdict": "OK", "problem": {"contestId": 5, "index": "B", "name": "n"}, "author": {}},
    ])
    assert st["5B"]["tries"] == 2
