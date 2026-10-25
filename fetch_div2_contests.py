import requests
import csv
from time import sleep

BASE = "https://codeforces.com/api"

def get_div2_last200():
    resp = requests.get(f"{BASE}/contest.list")
    resp.raise_for_status()
    data = resp.json()
    assert data["status"] == "OK"
    contests = data["result"]

    div2 = []
    for c in contests:
        if (
            c.get("phase") == "FINISHED"
            and c.get("type") == "CF"
            and "Div. 2" in c.get("name", "")
        ):
            div2.append(c)
        if len(div2) >= 200:
            break
    return div2

def fetch_problems_for_contest(cid):
    # only 1 row of standings is needed to access problems metadata
    params = {"contestId": cid, "from": 1, "count": 1}
    resp = requests.get(f"{BASE}/contest.standings", params=params)
    resp.raise_for_status()
    data = resp.json()
    if data["status"] != "OK":
        return None, []
    contest_name = data["result"]["contest"]["name"]
    problems = data["result"]["problems"]
    return contest_name, problems

def main():
    div2 = get_div2_last200()
    rows = []

    for c in div2:
        cid = c["id"]
        contest_name, problems = fetch_problems_for_contest(cid)
        if contest_name is None:
            continue
        for p in problems:
            idx = p.get("index", "")
            if not idx or idx[0] not in "ABCD":
                continue
            rows.append(
                {
                    "contestId": cid,
                    "contestName": contest_name,
                    "problemIndex": idx,
                    "problemName": p.get("name", ""),
                    "rating": p.get("rating", ""),
                    "tags": ";".join(p.get("tags", [])),
                }
            )
          # polite delay for API

    out_file = "codeforces_div2_last200_AtoD.csv"
    if not rows:
        raise RuntimeError("No rows collected; check API or filters.")

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "contestId",
                "contestName",
                "problemIndex",
                "problemName",
                "rating",
                "tags",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_file}")

if __name__ == "__main__":
    main()
