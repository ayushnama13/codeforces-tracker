import json
from pathlib import Path

import analytics
import server
from fastapi.testclient import TestClient


FIXTURES = Path(__file__).parent / "fixtures"


def client_setup(monkeypatch, tmp_path):
    def fetch(filename):
        return json.loads((FIXTURES / filename).read_text())

    calls = {"status": 0, "rating": 0, "info": 0}

    def mocked(name, filename):
        def call(handle):
            calls[name] += 1
            return fetch(filename), False
        return call

    monkeypatch.setattr(server.cf_api, "fetch_user_status", mocked("status", "user_status.json"))
    monkeypatch.setattr(server.cf_api, "fetch_user_rating", mocked("rating", "user_rating.json"))
    monkeypatch.setattr(server.cf_api, "fetch_user_info", mocked("info", "user_info.json"))
    monkeypatch.setattr(server.cf_api, "refresh_problems_csv", lambda *a, **k: None)
    server.PROBLEMS_CSV = FIXTURES / "problems.csv"
    server.problems_df = analytics.load_problems(server.PROBLEMS_CSV)
    server._problems_mtime = server.PROBLEMS_CSV.stat().st_mtime
    server.STATE_DIR = tmp_path / "state"
    server._bundles.clear()
    return TestClient(server.app), calls


def test_all_get_routes(monkeypatch, tmp_path):
    client, _ = client_setup(monkeypatch, tmp_path)
    expected = {
        "today": {"meta", "summary", "rating_history", "daily", "reviews", "upsolve", "upsolve_total", "calendar"},
        "practice": {"meta", "recommend", "ladders", "ladder"},
        "progress": {"meta", "summary", "rating_history", "rank_bands", "calendar", "contests", "weak_tags", "daily_history"},
        "coverage": {"meta", "heatmap", "divisions"},
        "revision": {"meta", "reviews", "backlog", "hidden", "revise"},
    }
    for route, keys in expected.items():
        response = client.get(f"/api/Ayushanma/{route}")
        assert response.status_code == 200
        assert keys <= response.json().keys()
    assert client.get("/api/Ayushanma/problem/1097B").status_code == 200


def test_validation_errors(monkeypatch, tmp_path):
    client, _ = client_setup(monkeypatch, tmp_path)
    for handle in ("bad%20handle%21", "a"):
        assert client.get(f"/api/{handle}/today").status_code == 400
    assert client.get("/api/Ayushanma/coverage?axis=nope").status_code == 400
    assert client.get("/api/Ayushanma/problem/bad").status_code == 400
    assert client.get("/api/Ayushanma/problem/999999Z").status_code == 404


def test_review_hide_and_backlog(monkeypatch, tmp_path):
    client, _ = client_setup(monkeypatch, tmp_path)
    assert client.post("/api/Ayushanma/review/1097B").json() == {"ok": True}
    assert server.StateStore(server.STATE_DIR, "Ayushanma").data["reviews"]["1097B"]
    before = client.get("/api/Ayushanma/practice").json()
    first_pick = next(item for tier in before["recommend"].values() for item in tier)
    assert client.post(f"/api/Ayushanma/hide/{first_pick['id']}").status_code == 200
    today = client.get("/api/Ayushanma/today").json()
    review_ids = [item["id"] for item in today["reviews"]["due"]]
    practice = client.get("/api/Ayushanma/practice").json()
    recommend_ids = [item["id"] for tier in practice["recommend"].values() for item in tier]
    assert first_pick["id"] not in review_ids + recommend_ids
    assert client.post("/api/Ayushanma/backlog", json={"id": "2194A"}).status_code == 200
    assert any(x["id"] == "2194A" for x in client.get("/api/Ayushanma/revision").json()["backlog"])
    assert client.delete("/api/Ayushanma/backlog/2194A").status_code == 200
    assert not any(x["id"] == "2194A" for x in client.get("/api/Ayushanma/revision").json()["backlog"])


def test_refresh_and_bundle_cache(monkeypatch, tmp_path):
    client, calls = client_setup(monkeypatch, tmp_path)
    assert client.get("/api/Ayushanma/progress").status_code == 200
    assert calls == {"status": 1, "rating": 1, "info": 1}
    assert client.get("/api/Ayushanma/today").status_code == 200
    assert calls == {"status": 1, "rating": 1, "info": 1}
    response = client.post("/api/Ayushanma/refresh")
    assert response.status_code == 200 and "meta" in response.json()
    assert calls == {"status": 2, "rating": 2, "info": 2}


def _total(heatmap):
    return sum(cell["total"] for row in heatmap["cells"] for cell in row)


def test_division_filter_and_band_fallback(monkeypatch, tmp_path):
    client, _ = client_setup(monkeypatch, tmp_path)
    everything = client.get("/api/Ayushanma/coverage").json()
    one = client.get("/api/Ayushanma/coverage", params=[("div", "Div3")]).json()
    two = client.get("/api/Ayushanma/coverage", params=[("div", "Div3"), ("div", "Div4")]).json()
    assert 0 < _total(one["heatmap"]) < _total(two["heatmap"]) < _total(everything["heatmap"])
    # 1476 -> default band 1400; an unknown band falls back to it instead of returning null
    assert client.get("/api/Ayushanma/practice?band=850").json()["ladder"]["band"] == 1400
    assert client.get("/api/Ayushanma/practice?band=1600").json()["ladder"]["band"] == 1600


def test_unknown_handle_and_offline(monkeypatch, tmp_path):
    client, _ = client_setup(monkeypatch, tmp_path)

    def missing(handle):
        raise server.cf_api.HandleNotFound("handles: User with handle nobody_here not found")

    monkeypatch.setattr(server.cf_api, "fetch_user_status", missing)
    assert client.get("/api/nobody_here/today").status_code == 404

    def offline(handle):
        raise ConnectionError("network down")

    monkeypatch.setattr(server.cf_api, "fetch_user_status", offline)
    assert client.get("/api/someone_else/today").status_code == 503


def test_missing_problem_list_is_503(monkeypatch, tmp_path):
    client, _ = client_setup(monkeypatch, tmp_path)
    server.PROBLEMS_CSV = tmp_path / "absent.csv"
    server.problems_df = None
    server._problems_mtime = None
    assert client.get("/api/Ayushanma/today").status_code == 503
