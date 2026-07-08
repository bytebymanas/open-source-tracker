# Open Source Contribution Tracker

**CUSoC 2026 — Project T-05**  
A web application that aggregates, scores, and visualizes open-source contributions from GitHub for university students and communities.

---

## Overview

Universities and student communities lack a structured way to track open-source contributions, recognize high-impact contributors, and verify contribution quality at scale. This project solves that by building a centralized platform that pulls contribution data from GitHub, applies a scoring algorithm, and displays ranked leaderboards for departments and individuals.

**Status:** Week 1 — Planning & Setup  
**Maintainer:** Manas Chhabra  
**License:** MIT

---

## Features

- Aggregate GitHub contributions per user (pull requests, issues, commits, code reviews)
- Weighted scoring algorithm based on contribution type and impact
- University and department-level leaderboards with filtering
- Individual contribution portfolios
- Mentor panel for reviewing and annotating contributions
- Export functionality (JSON/CSV)

---

## Technical Stack

| Layer | Technology |
| :--- | :--- |
| Backend | Python 3.9+, Flask 3.0 |
| Database | SQLite (development), PostgreSQL (production) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| API Integration | GitHub REST API v3 |
| Testing | pytest, pytest-cov |

---

## Project Structure

```
open-source-tracker/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── src/
│   ├── main.py             # Flask application entry point
│   ├── api/
│   │   ├── github_api.py   # GitHub REST API wrapper
│   │   └── routes.py       # HTTP endpoint definitions
│   ├── models/
│   │   └── database.py     # Database models and schema
│   └── utils/
│       └── cache.py        # Caching utilities
├── tests/
│   ├── test_github_api.py  # GitHub API integration tests
│   ├── test_routes.py      # Flask endpoint tests
│   └── test_database.py    # Database model tests
├── static/
│   ├── index.html          # Frontend entry point
│   ├── style.css           # Stylesheet
│   └── script.js           # Frontend JavaScript
└── docs/
    ├── API.md              # API endpoint reference
    └── ARCHITECTURE.md     # System design documentation
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub personal access token (for API calls)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/bytebymanas/open-source-tracker.git
cd open-source-tracker
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

```bash
cp .env.example .env
# Open .env and set your GITHUB_TOKEN
```

5. Run the application:

```bash
python3 src/main.py
```

The server will start at `http://localhost:5000`.

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/` | Home page |
| GET | `/api/health` | Server health check |
| GET | `/api/user/<username>` | Fetch user contribution data *(Week 2)* |
| GET | `/api/leaderboard` | Get ranked leaderboard *(Week 3)* |

Full API reference: [docs/API.md](docs/API.md)

---

## Running Tests

```bash
python3 -m pytest tests/ -v
```

Expected output: **12 tests passing** (Week 1 skeleton).

---

## Scoring Algorithm

Contributions are scored using weighted values:

| Contribution Type | Points |
| :--- | :--- |
| Merged Pull Request | 10 |
| Code Review | 5 |
| Issue Closed | 3 |
| First-time Contributor Bonus | +5 |

*Full scoring documentation:* [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Development Timeline

| Week | Focus |
| :--- | :--- |
| Week 1 | Planning, setup, documentation, skeleton |
| Week 2 | GitHub API integration, database schema, scoring logic |
| Week 3 | Frontend (leaderboard, profiles), comprehensive testing |
| Week 4 | Deployment, rate-limit handling, final documentation |

---

## Contributing

This is a CUSoC 2026 project under active development. For questions, contact the maintainer or open an issue on the repository.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
