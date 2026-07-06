# Open Source Contribution Tracker

A web application that aggregates and visualizes open-source contributions from GitHub for university students and communities.

## Features

- 🔍 Search contributions across all GitHub repositories
- 📊 View contribution statistics (commits, PRs, issues, code reviews)
- 🏆 University/department-level leaderboard
- 📅 Filter by date range and programming language
- 👨‍🏫 Mentor review and annotation system
- 📈 Track open-source impact over time

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- GitHub Account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/bytebymanas/open-source-tracker.git
cd open-source-tracker
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GitHub token
```

5. Run the application:
```bash
python3 src/main.py
```

6. Open your browser and go to `http://localhost:5000`

## Usage

Enter your GitHub username and click "Search" to view your contributions.

## Project Structure

```
open-source-tracker/
├── README.md               # Project overview
├── .gitignore              # Git ignored files
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
├── src/
│   ├── main.py             # Flask app entry point
│   ├── api/
│   │   ├── github_api.py   # GitHub API integration
│   │   └── routes.py       # Flask routes / endpoints
│   ├── models/
│   │   └── database.py     # Database models (SQLite/PostgreSQL)
│   └── utils/
│       └── cache.py        # Caching utilities
├── tests/
│   ├── test_github_api.py  # Tests for GitHub API module
│   ├── test_routes.py      # Tests for Flask routes
│   └── test_database.py    # Tests for database models
├── static/
│   ├── index.html          # Frontend entry point
│   ├── style.css           # Styles
│   └── script.js           # Frontend logic
└── docs/
    ├── API.md              # API documentation
    └── ARCHITECTURE.md     # System architecture documentation
```

## Development

### Running Tests

```bash
python3 -m pytest tests/ -v
```

### Running the App (Development Mode)

```bash
export FLASK_ENV=development
python3 src/main.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page |
| GET | `/api/health` | Server health check |
| GET | `/api/user/<username>` | Get user contributions *(coming soon)* |

## Contributing

This is a CUSoC 2026 project. For contributions, please contact the project maintainer.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technical Stack

- **Backend:** Python Flask
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Frontend:** HTML, CSS, JavaScript
- **API:** GitHub REST API v3

## Timeline

| Week | Focus |
|------|-------|
| Week 1 | Planning & Setup |
| Week 2 | Core Backend (GitHub API integration) |
| Week 3 | Frontend & Testing |
| Week 4 | Deployment & Final Polish |

## Status

🚀 **In Development** — Week 1 (CUSoC 2026)

---

**Maintainer:** Manas Chhabra
**Created:** July 2026
**Last Updated:** July 2026
