<div align="center">

# Open Source Contribution Tracker

**CUSoC 2026 — Project T-05**

A full-stack web application that aggregates, scores, and visualizes open-source contributions from GitHub for university students.  
Built with Python · Flask · SQLite · GitHub REST API · Vanilla JS

---

![Python](https://img.shields.io/badge/Python-3.9%2B-3572A5?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-131%20passing-34d399?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-f0b429?style=flat-square)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

</div>

---

## Overview

Universities and student communities lack a structured way to track open-source contributions, recognize high-impact contributors, and verify contribution quality at scale. This project solves that by building a centralized platform that:

- Pulls live contribution data from the GitHub REST API
- Applies a weighted scoring algorithm based on contribution type and impact
- Displays ranked leaderboards filterable by period and department
- Lets mentors annotate and verify individual contributions with a built-in UI
- Exports leaderboard data as CSV or JSON for offline reporting

**Maintainer:** Manas Chhabra  
**Repository:** [github.com/bytebymanas/open-source-tracker](https://github.com/bytebymanas/open-source-tracker)  
**License:** MIT

---


## Tech Stack

| Layer | Technology |
| :--- | :--- |
| Backend | Python 3.9+, Flask 3.0 |
| Database | SQLite (dev) · PostgreSQL-ready (prod) |
| Frontend | HTML5, Vanilla CSS, Vanilla JavaScript |
| API | GitHub REST API v3 |
| Testing | pytest, unittest.mock |
| CI | GitHub Actions |
| Auth | GitHub Personal Access Token (env var) |

---

## Project Structure

```
open-source-contribution-tracker/
├── .env.example               # Environment variable template
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI pipeline
├── requirements.txt
├── src/
│   ├── main.py                # Flask app entry point, .env loader
│   ├── api/
│   │   ├── github_api.py      # GitHubAPI class — auth, rate limits, fetchers
│   │   └── routes.py          # All HTTP endpoints (Blueprint)
│   ├── models/
│   │   └── database.py        # Database class — schema, CRUD, leaderboard
│   └── utils/
│       ├── scoring.py         # ScoringEngine — weighted contribution scoring
│       └── cache.py           # TTLCache — in-memory key/value with expiry
├── static/
│   ├── index.html             # Single-page frontend
│   ├── style.css              # Dark-theme design system
│   └── script.js              # Leaderboard, profiles, annotations logic
├── tests/
│   ├── test_routes.py         # 45+ route tests (all endpoints)
│   ├── test_database.py       # 29+ database layer tests
│   ├── test_integration.py    # 15 full-pipeline integration tests
│   ├── test_scoring.py        # 16 scoring engine tests
│   ├── test_cache.py          # 10 cache utility tests
│   └── test_github_api.py     # GitHub API wrapper tests
└── docs/
    ├── API.md                 # Full REST API reference
    └── ARCHITECTURE.md        # System design and data model
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub Personal Access Token ([create one here](https://github.com/settings/tokens))

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/bytebymanas/open-source-tracker.git
cd open-source-tracker
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Open `.env` and set your token:

```env
GITHUB_TOKEN=ghp_your_personal_access_token_here
```

Without a token the app still works, but is limited to 60 GitHub API requests per hour.

**5. Start the development server**

```bash
PYTHONPATH=. python3 src/main.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

> **Mac users:** Use `127.0.0.1:5000` not `localhost:5000` — AirPlay reserves the `localhost` alias on port 5000.

---

## API Endpoints

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/api/health` | Server health check |
| `GET` | `/api/user/<username>` | Fetch GitHub profile, compute + persist score |
| `GET` | `/api/user/<username>/contributions` | Scored contribution list with internal DB IDs |
| `GET` | `/api/user/<username>/repos` | Public repos sorted by stars |
| `GET` | `/api/leaderboard` | Ranked leaderboard (`period`, `limit`, `department`) |
| `GET` | `/api/leaderboard/export` | Download as CSV or JSON (`format`, `period`, `limit`, `department`) |
| `GET` | `/api/departments` | List of distinct department names from active users |
| `GET` | `/api/ratelimit` | GitHub API rate limit status |
| `GET` | `/api/contributions/<id>/annotations` | Get all mentor annotations for a contribution |
| `POST` | `/api/contributions/<id>/annotations` | Add a mentor annotation to a contribution |

Full reference with request/response examples: [docs/API.md](docs/API.md)

---

## Scoring Algorithm

Contributions are scored using a fixed weighted table applied by `ScoringEngine`:

| Contribution Type | Base Points |
| :--- | :---: |
| Merged Pull Request | 10 |
| Code Review | 5 |
| Issue Closed | 3 |
| First-time Contributor Bonus | +5 |

Scores are stored per-user per-period (`all_time`, `this_month`, `this_week`) and re-computed on each profile fetch. Mentors can override the score for any specific contribution via the annotation system.

Full scoring documentation: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Running Tests

```bash
python3 -m pytest tests/ -v
```

Or for a compact summary:

```bash
python3 -m pytest tests/ -q
```

**Expected:** 131 tests passing across 6 files in under 10 seconds.

```
tests/test_routes.py         45 passed
tests/test_database.py       29 passed
tests/test_integration.py    15 passed
tests/test_scoring.py        16 passed
tests/test_cache.py          10 passed
tests/test_github_api.py     16 passed
──────────────────────────────────────
TOTAL                       131 passed
```

All GitHub API calls are mocked — tests run offline without consuming rate-limit quota.

---

## Database Schema

Five tables in SQLite (auto-migrated on startup via `init_schema()`):

```
users               — GitHub username, name, avatar, department, university
repositories        — Tracked repo metadata
contributions       — Individual PR/issue/review events linked to users
scores              — Aggregated score per user per period
mentor_annotations  — Free-text notes, verified flag, score overrides
```

Foreign keys are enforced. The `department` column on `users` powers the leaderboard filter and the `/api/departments` endpoint.

---

## Frontend

The frontend is a single-page dark-theme app (`static/index.html`) with two views:

**Leaderboard view:**
- Period filter buttons (All Time / This Month / This Week)
- Department dropdown — dynamically populated from `/api/departments`
- Active filter chip with one-click clear
- Department badge per row
- Username search (client-side)
- Leaderboard table with rank, contributor, department, score, PRs, issues, reviews
- Summary stats bar (contributors, merged PRs, issues closed, top score)

**Profile view:**
- Fetch any GitHub user by username
- Score card with breakdown (PRs × 10, issues × 3, reviews × 5)
- Contributions table with type badge, title link, repo, points, and **Annotate** button
- Annotation form (inline, per row) — mentor username, note, verified toggle, score override
- Public repository grid (top 12, sorted by stars)


## CI / CD

GitHub Actions workflow at [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push to `main`:

1. Sets up Python 3.11
2. Installs dependencies from `requirements.txt`
3. Runs the full test suite (`pytest tests/ -q`)
4. Fails the build if any test fails

---

## Contributing

This is a CUSoC 2026 project under active development. To contribute:

1. Open an issue to discuss the change
2. Fork the repo and create a branch from `main`
3. Write tests for new functionality
4. Ensure all 131+ tests pass before opening a pull request

---

## License

This project is licensed under the [MIT License](LICENSE).
