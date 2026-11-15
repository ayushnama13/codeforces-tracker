# Problem Training Sites, Ladders, and Sheets

Survey of curated practice paths, recommendation tools, daily problems, and training plans. Features below reflect the cited search result or page; availability and content can change.

## Site and tool survey

| Site | URL | Notable features (short, concrete) | Evidence URL | Verified |
| :--- | :--- | :--- | :--- | :--- |
| A2OJ Refreshed | https://a2oj.online/ | Recreated rating and division ladders; extra ladders; handle-based progress | https://a2oj.online/ | yes |
| Codeforces Ladders (LaddersCF) | https://codeforcesladders.firebaseapp.com/ | 85 A2OJ, rating, and topic ladders; progress, upsolve queue, weekly stretch goal | https://codeforcesladders.firebaseapp.com/ | yes |
| A2OJ Ladders clone | https://cfladder.vercel.app/ | Rating-range extra ladders and division/problem-letter sets | https://cfladder.vercel.app/ | yes |
| A2OJ client-side clone | https://earthshakira.github.io/a2oj-clientside/server/Ladders.html | Static ladder/category content with handle-based solved status | https://codeforces.com/topic/73693/en5 | yes |
| Original A2OJ ladders | https://a2oj.com/Ladders.html | Classic rating and division ladders; automatic solved-state tracking for linked handles | https://codeforces.com/blog/entry/56795 | yes |
| C2Ladders | https://www.youtube.com/watch?v=xQuNwSFi4Ag | A2OJ recreation with an updated problem collection and selection algorithm | https://www.youtube.com/watch?v=xQuNwSFi4Ag | yes |
| TLE Eliminators CP-31 | https://www.tle-eliminators.com/cp-sheet | 31 curated Codeforces problems per rating band from 800 to 1900; hints and video solutions | https://www.tle-eliminators.com/ | yes |
| CF Stats problem ladder | https://cfstats.vercel.app/problems | Rating rungs show solved/total coverage; recommends unsolved problems in weak tags | https://cfstats.vercel.app/problems | yes |
| RunTimeFix topic practice | https://runtimefix.vercel.app/practice | 400+ topic-wise Codeforces problems, split into subtopics and ordered for practice | https://runtimefix.vercel.app/practice | yes |
| ICPC U problem practice | https://u.icpc.global/problems/ | Maps CSES starter tasks into a finishable sequence with course bands, topics, and local progress; links other judges | https://u.icpc.global/problems/ | yes |
| CSES Problem Set | https://cses.fi/problemset/ | Structured collections by algorithmic area, from introductory tasks to advanced topics | https://codeforces.com/topic/88457/?locale=en | yes |
| CodeChef 5-star roadmap | https://www.codechef.com/roadmap/become-5-star | Seven courses and 761 curated problems, staged by star level and difficulty | https://www.codechef.com/roadmap/become-5-star | yes |
| CodeChef Practice | https://www.codechef.com/practice | Problem collections by topic and difficulty; rating-aware practice paths and to-do list | https://www.codechef.com/practice | yes |
| A Code Daily (ACD) | https://acodedaily.com/v2/about/ | Competitive-programming learning community with educational resources, mentorship, and events | https://acodedaily.com/v2/about/ | yes |
| Daily Codeforces | https://www.dailycodeforces.com/ | Sends a Codeforces practice problem by email each day | https://www.dailycodeforces.com/ | yes |
| Daily CF browser extension | https://codeforces.com/blog/OneShhhhhh?locale=en | Displays a couple of daily problem suggestions on the Codeforces problemset page | https://codeforces.com/blog/OneShhhhhh?locale=en | yes |
| Codeforces Daily Question extension | https://codeforces.com/blog/entry/139162?locale=en | Seven-day problem set based on user rating and selected topic | https://codeforces.com/blog/entry/139162?locale=en | yes |
| Daily_CF_Problems | https://github.com/Yawn-Sean/Daily_CF_Problems | Automates daily Codeforces problem selection and includes solutions | https://numfer.com/Yawn-Sean/Daily_CF_Problems | yes |
| AlgoRadar | https://codeforces.com/blog/entry/154929?locale=en | Explainable practice recommendations using submission history, tags, ratings, and profile features | https://codeforces.com/blog/entry/154929?locale=en | yes |
| Codeforces Problem Recommender (tannadevp) | https://github.com/tannadevp/codeforces-problem-recommender | Predicts ratings for unrated problems and recommends unsolved problems using a user's solved set | https://github.com/tannadevp/codeforces-problem-recommender/blob/main/README.md | yes |
| CF Recommender | https://cfrecommender.vercel.app/ | Personalized Codeforces practice recommendations and training-plan positioning | https://cfrecommender.vercel.app/ | yes |
| Codeforces Problem Recommender (Vaibhav-kesarwani) | https://codeforces-problem-recommender.vercel.app/ | Suggests unsolved easy, medium, and hard problems based on current rating | https://github.com/Vaibhav-kesarwani/Codeforces-Problem-Recommender | yes |
| Mostafa Saad Junior/Senior training sheets | https://codeforces.me/blog/mostafa.saad.fci?locale=en | Sequenced newcomer and advanced sheets designed as roadmaps that avoid redundant practice | https://codeforces.me/blog/mostafa.saad.fci?locale=en | yes |
| Assiut University Training sheets | https://github.com/EpitomeZied/Assiut-University-Training-Newcomers | Topic-sequenced newcomer sheets with 300+ practice problems across training sessions | https://github.com/EpitomeZied/Assiut-University-Training-Newcomers/blob/master/README.md | yes |
| AtCoder Educational DP Contest | https://atcoder.jp/contests/dp | Focused set of 26 progressively challenging dynamic-programming tasks | https://www3.dcc.fc.up.pt/~pribeiro/aulas/pc2526/material/dp2_2425/slides.pdf | yes |
| Codeforces rating ladder by contest success odds | https://codeforces.com/blog/entry/131565 | Curates problems from users who advanced through rating bands, using similarity to candidate profiles | https://codeforces.com/blog/entry/131565 | yes |

## Feature ideas for our tracker

1. **Import a curated sheet and sync its checklist.** Let users load a named sheet, preserve its order, and show solved, skipped, and deferred states against each item. Inspired by A2OJ Refreshed, CP-31, and Mostafa Saad sheets. Data: `problemset.problems`, `user.status`; sheet definitions and custom states: external/local.
2. **Build ordered topic curricula with prerequisites.** Present a topic path such as fundamentals → graphs → shortest paths, and unlock or recommend the next unit when prerequisites are marked complete. Inspired by CSES and Assiut sheets. Data: external curriculum metadata; `user.status` for Codeforces task completion.
3. **Personal stretch-band estimate.** Show a suggested next rating band based on historical acceptance probability, and tune it as the user's recent solves change. Inspired by Codeforces Ladders and CF Stats. Data: `user.status`, `user.info`, `problemset.problems`.
4. **Explain every recommendation.** Include a short reason such as “covers two low-accuracy tags,” “one band above your recent practice,” or “matches this sheet's next subtopic.” Inspired by AlgoRadar and Codeforces recommenders. Data: `user.status`, `user.info`, `problemset.problems`.
5. **Daily challenge with a configurable cadence.** Offer one unseen task per day, allow rating/topic constraints, and keep a calendar of completed or missed prompts. Inspired by Daily Codeforces and Codeforces Daily Question. Data: `problemset.problems`, `user.status`; prompt history: local.
6. **Session timer and reflection log per problem.** Capture time-to-first-idea, time-to-solve, hint/editorial use, and a short takeaway, then summarize patterns by topic and difficulty. Inspired by Mostafa Saad's sheets. Data: external/local; associate entries with `problemset.problems` and `user.status`.
7. **Unrated problem difficulty estimates.** Predict a likely difficulty band for unrated tasks and show uncertainty so users can include them in a suitable ladder. Inspired by the tannadevp recommender. Data: `problemset.problems`, `user.status`; model inputs may be external.
8. **Contest-style mini ladders.** Assemble a short timed set with a deliberate range of difficulty and topic coverage, then record completion time and score separately from normal practice. Inspired by CodeChef roadmap courses and curated ladders. Data: `problemset.problems`, `contest.list`; session results: local.
9. **Sheet-to-plan weekly targets.** Turn a selected curriculum into a realistic weekly quota, adapting the number of tasks to the user's completed volume and available days. Inspired by CP-31, USACO Guide, and Codeforces Ladders. Data: `user.status`, `problemset.problems`; schedule preferences: external/local.
10. **Problem selection by learning mode.** Offer deliberate choices such as rating ladder, single-topic drill, mixed-topic review, or contest upsolve, retaining the user's preferred mode. Inspired by A2OJ, RunTimeFix, and CF Stats. Data: `problemset.problems`, `user.status`, `contest.list`.
11. **Age-aware curation quality signal.** Add context to popularity by comparing a task's solve count with similarly rated problems from the same publication period, helping avoid a ladder dominated by old classics. Inspired by Codeforces Ladders. Data: `problemset.problems`; solve/popularity aggregates: external.
12. **Cross-platform curriculum links.** Allow a curriculum unit to pair Codeforces tasks with CSES or AtCoder alternatives, showing one shared topic checklist across judges. Inspired by ICPC U and CSES. Data: external curriculum and judge identifiers; Codeforces completion: `user.status`.

