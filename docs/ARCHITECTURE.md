# System Architecture

> **Status:** Draft — Week 1  
> **Last Updated:** July 2026  
> **Project:** Open Source Contribution Tracker (CUSoC 2026)

---

## Overview

The Open Source Contribution Tracker is a web application that:
- Fetches GitHub contribution data via the GitHub REST API v3
- Stores and aggregates that data in a database
- Displays it through a leaderboard and individual profile pages
- Allows mentors to review and annotate contributions

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
│                    BACKEND (Flask)                      │
│                    src/main.py                          │
│  ┌─────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │  routes.py  │  │ github_api.py │  │  cache.py   │  │
│  │ (Endpoints) │  │ (API wrapper) │  │  (Caching)  │  │
│  └──────┬──────┘  └──────┬────────┘  └─────────────┘  │
│         │                │                              │
│  ┌──────▼──────┐         │ HTTPS Requests               │
│  │ database.py │         │                              │
│  │  (SQLite /  │         ▼                              │
│  │ PostgreSQL) │  ┌──────────────┐                      │
│  └─────────────┘  │  GitHub API  │                      │
│                   │  (api.github │                      │
│                   │    .com)     │                      │
└───────────────────└──────────────┘──────────────────────┘
```

---

## Component Breakdown

### 1. Frontend (`static/`)

| File | Responsibility |
|------|---------------|
| `index.html` | Main UI — leaderboard, search bar, user profiles |
| `style.css` | Styling |
| `script.js` | Fetches data from backend API, renders UI |

**Technology:** Vanilla HTML/CSS/JavaScript (no framework for MVP)

---

### 2. Backend (`src/`)

| File | Responsibility |
|------|---------------|
| `main.py` | Flask app entry point, starts the server |
| `api/routes.py` | Defines all HTTP endpoints (`/api/...`) |
| `api/github_api.py` | Wrapper around GitHub REST API v3 |
| `models/database.py` | Database models and queries |
| `utils/cache.py` | Simple in-memory or file-based caching |

**Technology:** Python 3.8+, Flask 2.x

---

### 3. Database

| Environment | Database |
|------------|---------|
| Development | SQLite (`tracker.db`) |
| Production | PostgreSQL |

**Planned Tables:**

| Table | Description |
|-------|-------------|
| `users` | GitHub usernames being tracked |
| `repositories` | Repos associated with tracked users |
| `contributions` | Individual contribution records (PR, commit, issue, review) |
| `scores` | Computed scores per user per period |

> ⚠️ Schema not yet implemented. Coming in Week 2.

---

### 4. GitHub API Integration

- **API Version:** GitHub REST API v3
- **Auth:** Personal Access Token (PAT) via `GITHUB_TOKEN` env var
- **Rate Limits:** 5000 requests/hour with token
- **Polling Strategy:** Cron job every 24 hours (no real-time webhooks in MVP)
- **Key Endpoints Used:**
  - `GET /users/{username}/repos` — list repositories
  - `GET /search/commits` — fetch commits
  - `GET /search/issues` — fetch PRs and issues

---

## Data Flow

```
GitHub API
    │
    ▼ (every 24h via cron / manual trigger)
github_api.py  ──────► database.py (store raw data)
                                │
                                ▼
                        routes.py (aggregate + serve)
                                │
                                ▼
                        script.js (render leaderboard)
```

---

## Environment Configuration

All secrets and config are stored in `.env` (not committed to Git):

```
GITHUB_TOKEN=...
FLASK_ENV=development
DATABASE_URL=sqlite:///tracker.db
PORT=5000
```

---

## Deployment (Planned — Week 4)

| Component | Platform |
|-----------|---------|
| Backend | Render / Railway / Heroku |
| Database | PostgreSQL (managed) |
| Frontend | Served by Flask or Vercel |

---

*This document will be updated as implementation progresses in Week 2 and beyond.*
