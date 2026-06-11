import requests
import pandas as pd
from collections import defaultdict, Counter
from config import FOCUS_TAGS


def fetch_submissions(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK":
        raise RuntimeError(data.get("comment", "Codeforces API error"))
    return data["result"]


def preprocess(submissions):
    solved = {}
    problem_history = {}

    verdicts = Counter()
    monthly = defaultdict(int)

    attempts = defaultdict(int)
    ac = defaultdict(int)

    contest_tag = defaultdict(int)
    practice_tag = defaultdict(int)

    for s in submissions:
        verdict = s.get("verdict")
        if verdict:
            verdicts[verdict] += 1

        p = s["problem"]
        if "contestId" not in p:
            continue
        pid = (p["contestId"], p["index"])
        tags = p.get("tags", [])

        for tag in tags:
            attempts[tag] += 1

        if s.get("verdict") == "OK":
            ts = pd.to_datetime(s["creationTimeSeconds"], unit="s")

            # revision history
            if pid not in problem_history:
                problem_history[pid] = {
                    "name": p["name"],
                    "contestId": p["contestId"],
                    "index": p["index"],
                    "rating": p.get("rating"),
                    "tags": tags,
                    "first_solved": ts,
                    "last_solved": ts,
                }
            else:
                problem_history[pid]["last_solved"] = ts

            if pid not in solved:
                solved[pid] = p
                monthly[ts.strftime("%Y-%m")] += 1

                ptype = s["author"]["participantType"]
                is_contest = ptype == "CONTESTANT"

                for tag in tags:
                    ac[tag] += 1
                    if tag in FOCUS_TAGS:
                        if is_contest:
                            contest_tag[tag] += 1
                        else:
                            practice_tag[tag] += 1

    df = pd.DataFrame(solved.values())

    return (
        df,
        verdicts,
        monthly,
        attempts,
        ac,
        contest_tag,
        practice_tag,
        problem_history,
    )
