import csv
import re
import requests

BASE = "https://codeforces.com/api"


def get(path):
    resp = requests.get(f"{BASE}/{path}", timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK":
        raise RuntimeError(data.get("comment", "Codeforces API error"))
    return data["result"]


def division(name):
    m = re.search(r"Div\. ?(\d)", name)
    if "Div. 1 + Div. 2" in name or "Div.1 + Div.2" in name:
        return "Div1+Div2"
    if m:
        return f"Div{m.group(1)}"
    if "Educational" in name:
        return "Educational"
    if "Global Round" in name:
        return "Global"
    return "Other"


def main():
    contests = {c["id"]: c for c in get("contest.list")}
    problems = get("problemset.problems")["problems"]

    rows = []
    for p in problems:
        c = contests.get(p["contestId"], {})
        name = c.get("name", "")
        rows.append(
            {
                "contestId": p["contestId"],
                "contestName": name,
                "division": division(name),
                "phase": c.get("phase", ""),
                "startTime": c.get("startTimeSeconds", ""),
                "problemIndex": p["index"],
                "problemName": p["name"],
                "rating": p.get("rating", ""),
                "tags": ";".join(p.get("tags", [])),
            }
        )

    out_file = "codeforces_all_problems.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_file}")


if __name__ == "__main__":
    main()
