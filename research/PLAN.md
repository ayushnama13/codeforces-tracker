# Improvement plan

Built from 111 tools surveyed in `cf-analytics.md`, `training.md`, `other-judges.md` and `aggregators.md`, plus a review of the current code and screenshots of the running app. Ranked by value for a single person training on Codeforces, using data the app can already get.

Current profile for reference: `ayushanma`, rating 1476 (specialist), 30 rated contests, 391 solved, 35 problems attempted but never solved.

## Tier 0: fix what exists

| # | Problem | Fix |
|---|---|---|
| F1 | `with_solved` is cached per handle with no TTL, so "% solved" and "Unsolved" heatmaps go stale after new solves | Key the cache on the solved set (or share the 10-minute TTL) |
| F2 | `get_problem_by_id` treats the last character as the index, so `1784D2` and `2000A1` fail | Split with a regex: digits, then the rest |
| F3 | Weak-tag "AC ratio" divides first solves by all submissions, so it measures retries | Per tag: problems solved / problems attempted, plus average rating solved |
| F4 | Every past solve enters the review queue as overdue (e.g. "overdue 1075d"), which is noise | Queue only opted-in problems: manual backlog, problems that took 3+ tries, and a "revise" mark; daily cap |
| F5 | Review, hidden and backlog files are shared across handles | Store state per handle |
| F6 | Server listened on all interfaces and keeps stopping | Bind to 127.0.0.1; add a `run.sh` launcher (optionally a systemd user service) |
| F7 | `codeforces_all_problems.csv` refreshes only by hand | Refetch on load when older than 24h (two API calls); also save `solvedCount` from `problemStatistics` |
| F8 | Tag x rating heatmap is mostly zeros at 100-point resolution | Rating buckets (e.g. 800-1000, 1100-1300, ...) |
| F9 | UI issues seen in screenshots: buttons truncated to "D."/"H.", Plotly toolbars always visible, rotated axis labels, revision tag defaults to "*special", "Deploy" button | Part of the redesign |

## Tier 1: high value, data already available

| # | Feature | Inspired by | Data |
|---|---|---|---|
| 1 | **Rating graph and current rank**: rating over time with rank colour bands, per-contest delta | cfviz, LeetCode Contest Stats, CP Insights | `user.rating`, `user.info` |
| 2 | **Recommender with solve-probability tiers**: unsolved problems at "comfortable / stretch / hard", biased to weak tags, with a one-line reason for each pick | AtCoder Problems recommendations, AlgoRadar, CF Stats, Improve-Codeforces | `problemset.problems` (+ `solvedCount`), `user.status` |
| 3 | **Upsolve queue**: attempted-but-unsolved problems, plus unsolved problems from contests you took part in | LaddersCF upsolve queue, unsolved-cf-problems | `user.status`, problems CSV |
| 4 | **Activity calendar and streaks**: GitHub-style daily grid (submissions / first ACs), current and longest streak | cfviz, AtCoder Problems, LeetCard, CodeTrace | `user.status` |
| 5 | **Coverage funnel heatmap**: each tag x rating cell split into unseen / attempted / solved | AtCoder Problems, AtCoder Analytics | `user.status`, problems CSV |
| 6 | **Rating ladders**: per rating band, the most-solved N problems with solved/total progress | A2OJ ladders and clones, CF Stats ladder, TLE CP-31 | problems CSV + `solvedCount` |
| 7 | **Daily problem**: one pick per day from the recommender, with a done/missed calendar | Daily Codeforces, Daily CF extension | derived |
| 8 | **Contest history**: per contest rank, delta, solved in contest vs upsolved later; results by division | AtCoder Analytics series breakdown, LeetCode Contest Stats | `user.rating`, `user.status` |
| 9 | **Problem drill-down**: verdict timeline, tries and time to AC, contest vs practice | CodeChef per-problem drill-down, LeetCode Contest Stats | `user.status` |

## Tier 2: worth doing later

- Upcoming contest list with local times and `.ics` export (`contest.list`; CLIST, ContestRadar, NextContest)
- Virtual mini-contest builder: random set by rating range, timer, result log (AtCoder Problems virtual contests)
- Compare with a friend's handle (cfviz, CodEyes)
- Session timer and short reflection note per problem (Mostafa Saad sheets)
- Difficulty-weighted solve points (AtCoder rated-point sum)
- README stats card export (cf-stats, Codeforces Readme Stats)

## Not planned

Cross-platform aggregation, public portfolio pages, live FFT rating prediction (Carrot already does this well), source-code archiving, Discord/Telegram bots. These are big, need scraping or hosting, or duplicate mature tools.

## Order of work

Stack decided: a FastAPI JSON server plus a hand-written HTML/CSS/JS frontend, with pages Today, Practice, Progress, Coverage, Revision and Problem. All of Tier 0 and Tier 1 is in scope. Codex and frontend work run one after the other, never at the same time, because each needs a clean tree.

1. Backend (Codex): `analytics.py`, a pure module whose functions return JSON-ready dicts and lists, with pytest tests on the committed fixtures in `tests/fixtures/`. Tests never call Codeforces. Covers F2-F5, F7, F8 and the Tier 1 data functions (#1-#9).
   - F5: move the existing backlog, hidden and review files to the current handle so nothing is lost.
   - F7: if a refetch fails or is slow, keep using the existing CSV.
   - #7: the daily pick is seeded by date (or saved), so it does not change on every rerun.
   - #3: needs `participantType`.
2. Backend (Codex, after the endpoint list is approved): `server.py`, the JSON API plus static files, bound to 127.0.0.1. Validates the handle against a strict pattern because it becomes part of file paths. Includes server-side caching (F1) and a launcher (F6).
3. Frontend (by hand, after the mock is approved): `static/`. API strings are inserted with `textContent`, never `innerHTML`. Today first, end to end, then one page per commit. F9 goes away with the new UI.
4. `app.py` (Streamlit) keeps working until the new UI does everything it does. Deleting it needs a separate OK.
5. Screenshot every page and run the tests.
