# System Architecture

> **Status:** Week 3 — Current Implementation  
> **Last Updated:** July 2026  
> **Project:** Open Source Contribution Tracker (CUSoC 2026)

---

## Overview

The Open Source Contribution Tracker is a web application that:
- Fetches GitHub contribution data via the GitHub REST API v3
- Computes weighted scores and stores them in SQLite
- Displays ranked leaderboards and individual contributor profiles
- Allows mentors to annotate and verify contributions
- Exports leaderboard data as CSV or JSON

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────┐
│                      FRONTEND                          │
│         static/index.html + style.css + script.js      │
│         (HTML / CSS / Vanilla JavaScript)               │
└─────────────────────────┬──────────────────────────────┘
                          │ HTTP Requests
┌─────────────────────────▼──────────────────────────────┐
│                    BACKEND (Flask 3.0)                  │
│                    src/main.py                          │
│  ┌─────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │  routes.py  │  │ github_api.py │  │  cache.py   │  │
│  │ (Endpoints) │  │ (API wrapper) │  │ (TTL Cache) │  │
│  └──────┬──────┘  └──────┬────────┘  └─────────────┘  │
│         │                │                              │
│  ┌──────▼──────┐         │ HTTPS Requests               │
│  │ database.py │         │                              │
│  │  (SQLite /  │         ▼                              │
│  │ PostgreSQL) │  ┌──────────────┐                      │
│  └─────────────┘  │  GitHub API  │                      │
│                   │ api.github   │                      │
│  ┌─────────────┐  │    .com      │                      │
│  │ scoring.py  │  └──────────────┘                      │
│  │  (Scoring   │                                        │
│  │   Engine)   │                                        │
│  └─────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Frontend (`static/`)

| File | Responsibility |
|------|----------------|
| `index.html` | Two-view SPA — leaderboard and user profile |
| `style.css` | Dark-mode UI with Inter font, responsive grid |
| `script.js` | Fetch-based API calls, dynamic DOM rendering, sorting, filtering |

**Features:**
- Leaderboard view: stats bar, period filter (all-time / this month / this week), username search, sortable table
- Profile view: avatar, score breakdown, per-contribution table, repository grid
- API health indicator in navigation bar
- Skeleton loaders, empty states, error states

---

### 2. Backend (`src/`)

| File | Responsibility |
|------|----------------|
| `main.py` | Flask app entry point, registers blueprints, serves `static/index.html` |
| `api/routes.py` | All 10 HTTP endpoints under `/api/` |
| `api/github_api.py` | Wrapper around GitHub REST API v3 with error handling |
| `models/database.py` | SQLite schema, CRUD operations, leaderboard queries |
| `utils/scoring.py` | Weighted scoring engine |
| `utils/cache.py` | In-memory TTL cache (default 5 min) |

**Technology:** Python 3.9+, Flask 3.0, Werkzeug 3.1, requests 2.31

---

### 3. Database

| Environment | Database |
|-------------|----------|
| Development | SQLite (`tracker.db`) |
| Production | PostgreSQL (via `DATABASE_URL` env var) |

**Schema:**

| Table | Description |
|-------|-------------|
| `users` | GitHub usernames, IDs, names, avatars, department, university |
| `repositories` | Repos associated with tracked users |
| `contributions` | Individual contribution records (PR, issue, review, commit) |
| `scores` | Computed scores per user per time period |
| `mentor_annotations` | Mentor notes, verification flags, score overrides |

---

### 4. GitHub API Integration

- **API Version:** GitHub REST API v3
- **Auth:** Personal Access Token (PAT) via `GITHUB_TOKEN` env var
- **Rate Limits:** 5,000 requests/hour with token · 60/hour unauthenticated
- **Key Endpoints Used:**
  - `GET /users/{username}` — user profile
  - `GET /users/{username}/repos` — public repositories
  - `GET /search/issues?q=author:{u}+type:pr+is:merged` — merged PRs
  - `GET /search/issues?q=author:{u}+type:issue+state:closed` — closed issues
  - `GET /rate_limit` — quota status

---

### 5. Scoring Engine

Contributions are scored with a configurable weighted formula:

| Type | Points | Condition |
|------|--------|-----------|
| Merged Pull Request | 10 | `is_merged = True` |
| Code Review | 5 | always |
| Closed Issue | 3 | always |
| Commit | 1 | always |
| First-contributor Bonus | +5 | `is_first_contribution = True` |

Weights and bonus are overridable at instantiation (`ScoringEngine(weights={...})`).

---

### 6. Cache Layer

Simple in-memory TTL cache (default 5 minutes). Caches:
- `user:{username}` — user score response
- `contributions:{username}` — detailed contributions list
- `repos:{username}` — repository list
- `leaderboard:{period}:{limit}` — leaderboard response

Export endpoint bypasses cache to always return fresh data.

---

## Data Flow

```
GitHub API
    │
    ▼ (on user fetch or manual trigger)
github_api.py  ──── scoring.py ──────► database.py (store user + score)
                                               │
                              cache.py ◄───────┘
                                               │
                              routes.py ────────► script.js (render UI)
```

---

## Environment Configuration

All secrets and config are stored in `.env` (never committed to Git):

```
GITHUB_TOKEN=ghp_...
FLASK_ENV=development
DATABASE_PATH=tracker.db
PORT=5000
```

---

## Test Suite

| File | Coverage |
|------|----------|
| `test_database.py` | Schema, users, contributions, scores, annotations |
| `test_scoring.py` | Scoring engine unit tests |
| `test_cache.py` | TTL cache expiry, hits, misses |
| `test_github_api.py` | GitHub API wrapper (mocked HTTP) |
| `test_routes.py` | All 10 Flask endpoints (mocked DB + GitHub) |
| `test_integration.py` | End-to-end pipeline tests |

**Total:** 112+ tests · Run with: `PYTHONPATH=. python3 -m pytest tests/ -v`

---

## Deployment (Week 4)

| Component | Platform (Planned) |
|-----------|-------------------|
| Backend | Render / Railway / Fly.io |
| Database | PostgreSQL (managed) |
| Frontend | Served by Flask (same process) |
| CI/CD | GitHub Actions (`.github/workflows/ci.yml`) |
