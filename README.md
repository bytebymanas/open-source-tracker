<div align="center">

# Open Source Contribution Tracker

A full-stack web application that aggregates, scores, and visualizes open-source contributions from GitHub for university students and communities.

Built with Python · Flask · SQLite · GitHub REST API · Vanilla JS

---

![Python](https://img.shields.io/badge/Python-3.9%2B-3572A5?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-passing-34d399?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-f0b429?style=flat-square)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

</div>

---

## Overview

Universities and student communities often lack a structured way to track open-source contributions, recognize high-impact contributors, and verify contribution quality at scale. This project provides a centralized platform that pulls live data from GitHub, applies a scoring algorithm, and surfaces ranked leaderboards for individuals and departments — with a built-in mentor review workflow.

**Maintainer:** Manas Chhabra  
**Repository:** [github.com/bytebymanas/open-source-tracker](https://github.com/bytebymanas/open-source-tracker)  
**License:** MIT

---

## Features

- **GitHub Integration** — Live data fetching for pull requests, issues, and repositories via the GitHub REST API
- **Contribution Scoring** — Weighted scoring engine that evaluates contributions by type and impact
- **Ranked Leaderboards** — Filterable by time period (all time, this month, this week) and department
- **Department Filtering** — Dropdown filter with an active chip indicator and one-click clear
- **Contributor Profiles** — Per-user score cards with a full contribution breakdown
- **Mentor Annotations** — Inline annotation form per contribution: notes, verification status, and score override
- **Leaderboard Export** — Download leaderboard data as CSV or JSON
- **Caching** — In-memory response caching for fast, repeated lookups
- **CI Pipeline** — Automated test suite on every push via GitHub Actions

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| Backend | Python 3.9+, Flask 3.0 |
| Database | SQLite (development) · PostgreSQL-ready (production) |
| Frontend | HTML5, Vanilla CSS, Vanilla JavaScript |
| API | GitHub REST API v3 |
| Testing | pytest |
| CI | GitHub Actions |

---

## Architecture

```
GitHub REST API
       ↓
 Flask Backend
       ↓
 Scoring Engine
       ↓
 SQLite Database
       ↓
   REST API
       ↓
  Frontend (SPA)
```

---

## Project Structure

```
open-source-contribution-tracker/
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
├── src/
│   ├── main.py
│   ├── api/
│   │   ├── github_api.py
│   │   └── routes.py
│   ├── models/
│   │   └── database.py
│   └── utils/
│       ├── scoring.py
│       └── cache.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── tests/
│   ├── test_routes.py
│   ├── test_database.py
│   ├── test_integration.py
│   ├── test_scoring.py
│   ├── test_cache.py
│   └── test_github_api.py
└── docs/
    ├── API.md
    └── ARCHITECTURE.md
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

> Without a token the app works but is limited to 60 GitHub API requests per hour.

**5. Start the development server**

```bash
PYTHONPATH=. python3 src/main.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

> **macOS users:** Use `127.0.0.1:5000` instead of `localhost:5000` — AirPlay can occupy port 5000 on the `localhost` alias.

---

## API Endpoints

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/api/health` | Server health check |
| `GET` | `/api/user/<username>` | Fetch GitHub profile and computed score |
| `GET` | `/api/user/<username>/contributions` | Scored list of contributions for a user |
| `GET` | `/api/user/<username>/repos` | Public repositories sorted by stars |
| `GET` | `/api/leaderboard` | Ranked leaderboard (`period`, `limit`, `department`) |
| `GET` | `/api/leaderboard/export` | Download leaderboard as CSV or JSON |
| `GET` | `/api/departments` | List of available department names |
| `GET` | `/api/ratelimit` | GitHub API rate limit status |
| `GET` | `/api/contributions/<id>/annotations` | Retrieve mentor annotations for a contribution |
| `POST` | `/api/contributions/<id>/annotations` | Add a mentor annotation to a contribution |

Full reference: [docs/API.md](docs/API.md)

---

## Scoring

Contributions are evaluated using a weighted scoring algorithm based on contribution type and overall impact. Mentors can review and override scores for individual contributions through the annotation system.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full scoring model.

---

## Database

The application persists data across five tables: users, repositories, contributions, scores, and mentor annotations. The schema is created automatically on first run.

---

## Testing

```bash
python3 -m pytest tests/ -q
```

Comprehensive automated tests cover the API, database layer, scoring engine, cache utilities, and integration workflows. All GitHub API calls are mocked — tests run fully offline.

---

## CI / CD

GitHub Actions automatically runs the full test suite on every push and pull request. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Documentation

- [API Reference](docs/API.md) — All endpoints with request/response examples
- [Architecture](docs/ARCHITECTURE.md) — System design, data model, and scoring algorithm

---

## Roadmap

- [ ] OAuth Authentication
- [ ] PostgreSQL Support
- [ ] Docker Deployment
- [ ] Admin Dashboard
- [ ] Contribution Trends & Analytics
- [ ] Organization-level Leaderboards
- [ ] PDF Portfolio Export
- [ ] Dark / Light Theme Toggle

---

## Contributing

Contributions are welcome. To get started:

1. Open an issue to discuss the proposed change
2. Fork the repository and create a branch from `main`
3. Write tests for any new functionality
4. Ensure all tests pass before opening a pull request

---

## Acknowledgements

- [GitHub REST API](https://docs.github.com/en/rest)
- [Flask](https://flask.palletsprojects.com)
- [Python](https://python.org)
- The open-source community

---

## License

This project is licensed under the [MIT License](LICENSE).
