# Codeforces Tracker & Analyzer

A Streamlit-based dashboard and analytics tool for tracking Codeforces user profiles, analyzing problem-solving performance, detecting weaknesses, and managing a spaced-repetition revision backlog.

## Overview / Purpose

Tracking competitive programming progress, identifying weak topic areas, and systematically reviewing solved or challenging problems on Codeforces can be tedious. This project provides a comprehensive local dashboard that fetches user submission history and global problemsets via the Codeforces API, caches data locally for offline usage, visualizes performance metrics (ratings, verdicts, monthly solves, focus tags), calculates acceptance ratios to detect weaknesses across problem tags and ratings, and implements a spaced-repetition revision system (7, 30, and 90-day intervals).

## Features

- **Profile Metrics & Overview**: Displays total problems solved, average rating, maximum rating, and unique contests tracked.
- **Visualizations**: Interactive Plotly charts showing rating distribution, focus tag frequency, monthly solve trends, and verdict breakdown.
- **Heatmaps**: Visual heatmaps mapping problem index letters and tags against ratings, supporting filter options by contest division and number of recent contests.
- **Spaced Repetition Revision System**: Tracks solved problems across a 3-stage spaced repetition cycle (7, 30, 90 days), with options to mark items as done or hide problems.
- **Manual Backlog**: Allows adding custom problem IDs (e.g., `1784D`) to the revision queue with tag and rating filters.
- **Weakness Detection**: Analyzes acceptance ratios for focus tags with 10+ attempts to highlight areas for improvement.
- **Offline Fallback & Caching**: Automatically caches Codeforces API responses and problemset data locally on disk, falling back to cache when offline.

## How It Works / Architecture

The application fetches data from the public Codeforces API (`user.status` and `problemset.problems`) or pre-fetched CSV datasets, processes the submission history using Pandas, and renders an interactive web interface via Streamlit. Cached data and review state are persisted as JSON files and CSV files locally.

```
+--------------------+      API Request      +------------------------+
| Codeforces API     | <-------------------> | data.py / revision_store.py|
+--------------------+                       +------------------------+
                                                         |
                                                  Local JSON / CSV
                                                  (Cache & Backlog)
                                                         |
                                                         v
                                             +------------------------+
                                             | Streamlit App (app.py) |
                                             +------------------------+
```

## Project Structure

```
codeforces-tracker/
├── app.py                      # Main Streamlit dashboard application interface
├── config.py                   # Configuration settings (handle and focus tags)
├── data.py                     # Submission data fetching, caching, and preprocessing logic
├── revision_store.py           # Problemset loader, revision backlog, and spaced repetition logic
├── fetch_all_problems.py       # Script to fetch all Codeforces problems into a CSV dataset
├── fetch_div2_contests.py      # Script to fetch recent Div 2 contests and problems (A-D)
├── codeforces_all_problems.csv # Cached dataset of Codeforces problems and metadata
├── revision_problems.json      # Persistent storage for manual revision backlog items
├── hidden_revision.json        # Persistent storage for hidden revision problems
└── cache/                      # Directory storing cached user submission JSON responses
```

## Tech Stack

- **Language**: Python 3.10+
- **Framework**: Streamlit
- **Data Manipulation & Analysis**: Pandas, NumPy
- **Visualization**: Plotly
- **HTTP Client**: Requests

## Requirements

- **Python Version**: Python 3.10 or higher
- **Network**: standard network access (for fetching Codeforces API data)
- **Accounts / Keys**: None required (uses public, unauthenticated Codeforces API endpoints)

## Installation / Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd codeforces-tracker
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install streamlit pandas plotly requests
   ```

4. **Populate problem datasets (optional, pre-cached files included)**:
   ```bash
   python fetch_all_problems.py
   python fetch_div2_contests.py
   ```

## Configuration

Configuration settings are defined in `config.py`:

| Key / Variable | Description | Default Value |
| --- | --- | --- |
| `HANDLE` | Default Codeforces user handle to analyze | `"ayushanma"` |
| `FOCUS_TAGS` | List of target algorithmic tags monitored for weakness detection and tag breakdowns | `["greedy", "dp", "graphs", "binary search", "implementation", "data structures", "sortings", "constructive algorithms", "math", "brute force", "trees", "bitmasks"]` |

Additionally, Streamlit UI theme configuration is specified in `.streamlit/config.toml`:
- `theme.base`: `"light"`
- `theme.primaryColor`: `"#1f6feb"`
- `theme.backgroundColor`: `"#f6f8fa"`
- `theme.secondaryBackgroundColor`: `"#ffffff"`
- `theme.textColor`: `"#1f2328"`
- `theme.font`: `"sans serif"`

## Usage

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

To update or fetch the full problem dataset:
```bash
python fetch_all_problems.py
```
Output:
```
Wrote <N> rows to codeforces_all_problems.csv
```

To fetch Div 2 contest problems (A-D):
```bash
python fetch_div2_contests.py
```
Output:
```
Wrote <N> rows to codeforces_div2_last200_AtoD.csv
```

## Data Model / API Endpoints

This project interacts with the public Codeforces API endpoints:
- `https://codeforces.com/api/user.status?handle={handle}`: Fetches user submission history.
- `https://codeforces.com/api/problemset.problems`: Fetches the global problemset and metadata.
- `https://codeforces.com/api/contest.list`: Fetches contest lists and metadata.
- `https://codeforces.com/api/contest.standings?contestId={cid}&from=1&count=1`: Fetches contest standings/problem metadata.

Local storage schemas:
- **`codeforces_all_problems.csv`**: Contains `contestId`, `contestName`, `division`, `phase`, `startTime`, `problemIndex`, `problemName`, `rating`, `tags`.
- **`revision_problems.json`**: List of dictionaries storing `name`, `contestId`, `index`, `rating`, `tags`, `url`, `last_solved`, `added_on`.
- **`review_log.json`**: Dictionary mapping problem IDs (`contestId` + `index`) to lists of ISO format review timestamps.

## Testing

There is no automated test suite implemented in this project. Verification is performed interactively by running the Streamlit application and execution scripts to ensure data ingestion, caching fallbacks, and UI rendering operate correctly.

## Troubleshooting / FAQ

- **Codeforces Unreachable Warning**: If the Codeforces API is unreachable or rate-limited, the application automatically loads cached submission data from `cache/{handle}.json` and displays a warning banner.
- **Missing Problem ID in Manual Backlog**: Ensure problem IDs follow the exact Codeforces format (e.g., `1784D` where numbers represent the contest ID and the trailing letter represents the problem index).

## Notes on Safety, Rate Limits, and Terms of Service

- **Rate Limits**: The Codeforces API enforces rate limits on requests. Scripts include polite delays or rely on local disk caching (`cache/` directory and `codeforces_all_problems.csv`) to prevent excessive API queries.
- **Privacy**: User handles and public submissions queried are public data available via the official Codeforces API. No private user tokens, passwords, or personal credentials are required or stored.
