import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

REVISION_FILE = Path("revision_problems.json")
PROBLEMSET_API = "https://codeforces.com/api/problemset.problems"


def load_revision_problems():
    if not REVISION_FILE.exists():
        return []
    with open(REVISION_FILE, "r") as f:
        return json.load(f)


def save_revision_problems(problems):
    with open(REVISION_FILE, "w") as f:
        json.dump(problems, f, indent=2)


# ---------- CF PROBLEM LOOKUP ---------- #

_problem_cache = None


def _load_problemset():
    global _problem_cache
    if _problem_cache is None:
        data = requests.get(PROBLEMSET_API, timeout=30).json()
        problems = data["result"]["problems"]
        _problem_cache = {
            (p["contestId"], p["index"]): p for p in problems
        }
    return _problem_cache


def get_problem_by_id(problem_id: str):
    """
    problem_id: '1784D', '1572E'
    """
    contest_id = int(problem_id[:-1])
    index = problem_id[-1].upper()

    problemset = _load_problemset()
    key = (contest_id, index)

    if key not in problemset:
        raise ValueError("Problem not found on Codeforces")

    return problemset[key]


# ---------- REVISION BACKLOG ---------- #

def add_revision_by_id(problem_id: str):
    p = get_problem_by_id(problem_id)

    problems = load_revision_problems()

    url = f"https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}"

    problems.append(
        {
            "name": p["name"],
            "contestId": p["contestId"],
            "index": p["index"],
            "rating": p.get("rating"),
            "tags": p.get("tags", []),
            "url": url,
            "last_solved": datetime.now().isoformat(),
            "added_on": datetime.now().isoformat(),
        }
    )

    save_revision_problems(problems)
def remove_revision_problem(contest_id, index):
    problems = load_revision_problems()
    problems = [
        p for p in problems
        if not (p["contestId"] == contest_id and p["index"] == index)
    ]
    save_revision_problems(problems)
HIDDEN_FILE = Path("hidden_revision.json")


def load_hidden_problems():
    if not HIDDEN_FILE.exists():
        return set()
    with open(HIDDEN_FILE, "r") as f:
        return set(tuple(x) for x in json.load(f))


def hide_problem(contest_id, index):
    hidden = load_hidden_problems()
    hidden.add((contest_id, index))
    with open(HIDDEN_FILE, "w") as f:
        json.dump(list(hidden), f)


# ---------- SPACED REPETITION ---------- #

REVIEW_FILE = Path("review_log.json")
REVIEW_INTERVALS_DAYS = [7, 30, 90]


def load_reviews():
    if not REVIEW_FILE.exists():
        return {}
    with open(REVIEW_FILE, "r") as f:
        return json.load(f)


def mark_reviewed(contest_id, index):
    reviews = load_reviews()
    reviews.setdefault(f"{contest_id}{index}", []).append(datetime.now().isoformat())
    with open(REVIEW_FILE, "w") as f:
        json.dump(reviews, f, indent=2)


def review_status(contest_id, index, base_date, reviews):
    """
    Returns (due_date, label). due_date is None once all intervals are done.
    base_date: when the problem was solved/added, used until the first review.
    """
    done = reviews.get(f"{contest_id}{index}", [])
    if len(done) >= len(REVIEW_INTERVALS_DAYS):
        return None, "mastered"

    last = datetime.fromisoformat(done[-1]) if done else base_date
    due = last + timedelta(days=REVIEW_INTERVALS_DAYS[len(done)])
    days = (due.date() - datetime.now().date()).days
    if days <= 0:
        label = "due today" if days == 0 else f"overdue {-days}d"
    else:
        label = f"due in {days}d"
    return due, label
