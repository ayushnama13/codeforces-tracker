# Codeforces Analytics & Tools Research

This document surveys existing Codeforces-specific profile analyzers, visualizers, browser extensions, Discord/Telegram bots, CLI tools, and rating predictors to identify high-value features for our personal training dashboard.

## 1. Tool & Site Survey

| Site | URL | Notable features (short, concrete) | Evidence URL | Verified |
| :--- | :--- | :--- | :--- | :--- |
| Codeforces | https://codeforces.com | Official competitive programming platform hosting contests, problemsets, and API | https://github.com/topics/codeforces | yes |
| Codeforces API | https://codeforces.com/apiHelp | Official REST API for fetching user info, rating history, problemsets, status, and contest standings | https://github.com/topics/codeforces-api | yes |
| Codeforces Visualizer (cfviz) | https://cfviz.netlify.app/ | Visualizes user data: tags chart, rating graphs, verdict breakdown, submission heatmaps, comparison | https://github.com/sjsakib/cfviz | yes |
| Carrot | https://github.com/meooow25/carrot | Browser extension for real-time rating change prediction and performance calculation using FFT | https://github.com/meooow25/carrot | yes |
| TLE Discord Bot | https://github.com/cheran-senthil/TLE | Discord bot for CP: problem recommendation, stats graphs, rating distributions, duels, contest reminders | https://github.com/cheran-senthil/TLE | yes |
| Clist.by | https://clist.by/ | Competitive programming contest aggregator across multiple platforms with rating changes and calendar | https://clist.by/ | fetch failed |
| cf-tool | https://github.com/xalanq/cf-tool | CLI tool for Codeforces: submit, parse samples, test locally, watch submissions, race contests | https://github.com/xalanq/cf-tool | yes |
| Competitive Companion | https://github.com/jmerle/competitive-companion | Browser extension parsing competitive programming problems and test cases across multiple judges | https://github.com/jmerle/competitive-companion | yes |
| USACO Guide | https://github.com/cpinitiative/usaco-guide | Free curated collection of high-quality competitive programming learning resources from Bronze to Platinum | https://github.com/cpinitiative/usaco-guide | yes |
| Testlib | https://github.com/MikeMirzayanov/testlib | C++ library to develop competitive programming problems, generators, validators, and interactors | https://github.com/MikeMirzayanov/testlib | yes |
| CP Editor | https://github.com/cpeditor/cpeditor | IDE for competitive programming: fetch, code, compile, run test cases, check, and submit | https://github.com/cpeditor/cpeditor | yes |
| Online Judge Tools (oj) | https://github.com/online-judge-tools/oj | Tools for downloading sample cases, generating additional test cases, testing code, and submitting | https://github.com/online-judge-tools/oj | yes |
| CPH (Competitive Programming Helper) | https://github.com/agrawal-d/cph | VS Code extension making judging, compiling, and downloading test cases easy | https://github.com/agrawal-d/cph | yes |
| cf-stats | https://github.com/sudiptob2/cf-stats | GitHub Action generating real-time Codeforces activity statistics cards and badges for GitHub READMEs | https://github.com/sudiptob2/cf-stats | yes |
| Competitive Programming Score API | https://github.com/abhijeet-reddy/Competitive_Programming_Score_API | Flask API to fetch user details and stats across Codeforces, Codechef, SPOJ, Interviewbit | https://github.com/abhijeet-reddy/Competitive_Programming_Score_API | yes |
| ACM Statistics (ojhunt) | https://github.com/Liu233w/acm-statistics | Crawler and website aggregating competitive programming statistics across multiple online judges | https://github.com/Liu233w/acm-statistics | yes |
| cp-tool | https://github.com/jspw/cp-tool | Python package and auto-generator for solved problems across different online judges | https://github.com/jspw/cp-tool | yes |
| CodeforcesApiPy | https://github.com/VadVergasov/CodeforcesApiPy | Python wrapper implementation for the official Codeforces API with Github Actions support | https://github.com/VadVergasov/CodeforcesApiPy | yes |
| arugo | https://github.com/phattd15/arugo | Virtual rating system for Codeforces using the Codeforces API with Django backend | https://github.com/phattd15/arugo | yes |
| codeforces-cli | https://github.com/ahmed-dinar/codeforces-cli | Simple command-line utility for Codeforces coders to interact with problems and tags | https://github.com/ahmed-dinar/codeforces-cli | yes |
| polygon-problems-generator | https://github.com/7oSkaaa/polygon-problems-generator | AI agents producing Polygon-ready CP problems (statements, validators, checkers, solutions) | https://github.com/7oSkaaa/polygon-problems-generator | yes |
| Codeforces-Visualizer-App | https://github.com/Priyansh19077/Codeforces-Visualizer-App | Android application for viewing Codeforces user info, rating graphs, and problems by difficulty/index | https://github.com/Priyansh19077/Codeforces-Visualizer-App | yes |
| CFViewer | https://github.com/rudradesai200/CFViewer | Contest suggestor and problem suggestor tool tailored to help coders choose practice targets | https://github.com/rudradesai200/CFViewer | yes |
| Improve-Codeforces | https://github.com/vivek9patel/Improve-Codeforces | Django web application suggesting practice problems specifically from areas where the user struggles | https://github.com/vivek9patel/Improve-Codeforces | yes |
| Codedigger Backend | https://github.com/Code-dig-ger/Backend | Backend API accumulating competitive programming data from multiple platforms for recommendations | https://github.com/Code-dig-ger/Backend | yes |
| Codeforces Explorer | https://github.com/hitarth-gg/codeforces-explorer | React application to search users and problems and sort data dynamically | https://github.com/hitarth-gg/codeforces-explorer | yes |
| Unsolved CF Problems | https://github.com/Sadykhzadeh/unsolved-cf-problems | Dedicated web interface highlighting unsolved Codeforces problems for users | https://github.com/Sadykhzadeh/unsolved-cf-problems | yes |
| cfetch | https://github.com/electr1fy0/cfetch | Advanced analytics tool for Codeforces user profiles and statistics | https://github.com/electr1fy0/cfetch | yes |

## 2. Feature ideas for our tracker

1. **Real-time Contest Rating Change Predictor (FFT-based)**: Computes estimated rating deltas and performance ratings during ongoing or past contests using Mike Mirzayanov's official rating algorithm optimized with FFT.
   - *Inspired by*: Carrot, TLE, arugo
   - *Data needed*: `contest.standings`, `user.rating`

2. **Tailored Weak-Area Problem Recommender**: Suggests specific practice problems specifically targeting tags and difficulty ranges where the user has low acceptance ratios or frequent unsuccessful attempts.
   - *Inspired by*: Improve-Codeforces, CFViewer, Codedigger
   - *Data needed*: `problemset.problems`, `user.status`

3. **CLI & Browser Companion Integration**: Local tooling and browser extension hooks to instantly fetch problem sample test cases, parse statement metadata, and set up local workspace folders (`inK.txt`/`ansK.txt`).
   - *Inspired by*: `cf-tool`, Competitive Companion, CPH
   - *Data needed*: External / Codeforces problem page scraping

4. **GitHub Profile Activity Badge & Stats Generator**: Real-time exportable SVG badges and profile summary cards displaying total solved counts, current streak, and recent rating status for GitHub READMEs.
   - *Inspired by*: `cf-stats`
   - *Data needed*: `user.status`, `user.info`

5. **Multi-User Side-by-Side Comparison Dashboard**: Comparative analytics view allowing users to benchmark solved counts, rating trajectories, and tag proficiency side-by-side with friends or rivals.
   - *Inspired by*: Codeforces Visualizer (`cfviz`), ACM Statistics, CP-API
   - *Data needed*: `user.info`, `user.rating`, `user.status`

6. **Virtual Contest Simulation Hub**: Built-in virtual contest manager supporting countdowns, automatic problem opening, and simulated contest pressure tracking against historical scoreboards.
   - *Inspired by*: `cf-tool`, Codeforces Contest Helper
   - *Data needed*: `contest.list`, `problemset.problems`, `contest.standings`

7. **Dedicated Unsolved Problem Backlog Filter**: Interactive table highlighting all attempted but unresolved problems (`OK` verdict missing), filterable by contest round, tag, and rating threshold.
   - *Inspired by*: Unsolved CF Problems, Codeforces Explorer
   - *Data needed*: `user.status`, `problemset.problems`

8. **Group Study & Discord/Telegram Bot Problem Drops**: Automated command hooks or widget triggers to generate random practice problems of exact difficulty/tags for study groups.
   - *Inspired by*: TLE Discord Bot
   - *Data needed*: `problemset.problems`, `user.status`

9. **Accepted Solution Cloner & Implementation Inspector**: Tooling to fetch and archive all accepted submission source codes for a user or problem to review past implementation styles and templates.
   - *Inspired by*: `cf-tool`
   - *Data needed*: `user.status` (submission IDs) & source code extraction

10. **Tag Attempt Efficiency & Penalty Breakdown**: Granular metrics showing average submission attempts before acceptance per tag, penalty time impact, and success rate vs problem difficulty.
    - *Inspired by*: Codeforces Tags Accuracy
    - *Data needed*: `user.status`, `problemset.problems`

11. **Submission Heatmap & Streak Consistency Tracker**: GitHub-style activity contribution calendar heatmap visualizing daily submission frequency, active streaks, and resting days.
    - *Inspired by*: CP-API / TLE Profiles
    - *Data needed*: `user.status`
