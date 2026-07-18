"""
Unit tests for Flask API routes (src/api/routes.py).

All GitHub API calls are mocked using unittest.mock so tests run
offline, instantly, and without consuming rate-limit quota.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Flask test client with testing mode enabled."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


MOCK_GITHUB_USER = {
    "id": 12345,
    "login": "bytebymanas",
    "name": "Manas Chhabra",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
    "public_repos": 10,
}

MOCK_PRS = [
    {
        "id": 1001,
        "title": "Fix login bug",
        "html_url": "https://github.com/test/repo/pull/1",
        "repository_url": "https://api.github.com/repos/test/repo",
    }
]

MOCK_ISSUES = [
    {
        "id": 2001,
        "title": "Add dark mode",
        "html_url": "https://github.com/test/repo/issues/1",
        "repository_url": "https://api.github.com/repos/test/repo",
        "state": "closed",
    }
]

MOCK_REPOS = [
    {
        "name": "open-source-tracker",
        "full_name": "bytebymanas/open-source-tracker",
        "description": "OS contribution tracker",
        "language": "Python",
        "html_url": "https://github.com/bytebymanas/open-source-tracker",
        "stargazers_count": 5,
        "forks_count": 1,
        "fork": False,
    }
]


# ---------------------------------------------------------------------------
# Helper: patch GitHubAPI methods for a single test
# ---------------------------------------------------------------------------

def _github_patches(user=MOCK_GITHUB_USER, prs=None, issues=None, repos=None):
    """Return a dict of patches to apply for a typical mocked GitHub call."""
    return {
        "get_user":                 MagicMock(return_value=user),
        "get_merged_pull_requests": MagicMock(return_value=prs or MOCK_PRS),
        "get_user_issues":          MagicMock(return_value=issues or MOCK_ISSUES),
        "get_user_repos":           MagicMock(return_value=repos or MOCK_REPOS),
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_returns_200(self, client):
        assert client.get("/api/health").status_code == 200

    def test_returns_status_ok(self, client):
        data = client.get("/api/health").get_json()
        assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# Home (serves index.html)
# ---------------------------------------------------------------------------

class TestHomeEndpoint:

    def test_returns_200(self, client):
        assert client.get("/").status_code == 200


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

class TestUserEndpoint:

    @patch("src.api.routes.github")
    def test_returns_200_for_known_user(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        res = client.get("/api/user/bytebymanas")
        assert res.status_code == 200

    @patch("src.api.routes.github")
    def test_response_contains_username(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas").get_json()
        assert data["username"] == "bytebymanas"

    @patch("src.api.routes.github")
    def test_response_contains_score(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas").get_json()
        assert "score" in data
        assert "total" in data["score"]

    @patch("src.api.routes.github")
    def test_score_is_calculated_correctly(self, mock_gh, client):
        """1 merged PR = 10pts, 1 closed issue = 3pts → total 13."""
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas").get_json()
        assert data["score"]["total"] == 13

    @patch("src.api.routes.github")
    def test_returns_404_for_unknown_user(self, mock_gh, client):
        mock_gh.get_user.return_value = None
        res = client.get("/api/user/nonexistent_user_xyz")
        assert res.status_code == 404

    @patch("src.api.routes.github")
    def test_404_response_contains_error_key(self, mock_gh, client):
        mock_gh.get_user.return_value = None
        data = client.get("/api/user/nonexistent_user_xyz").get_json()
        assert "error" in data


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

class TestLeaderboardEndpoint:

    def test_returns_200(self, client):
        assert client.get("/api/leaderboard").status_code == 200

    def test_returns_leaderboard_list(self, client):
        data = client.get("/api/leaderboard").get_json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)

    def test_accepts_period_param(self, client):
        data = client.get("/api/leaderboard?period=this_month").get_json()
        assert data.get("period") == "this_month"

    def test_accepts_limit_param(self, client):
        res = client.get("/api/leaderboard?limit=5")
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# Contributions
# ---------------------------------------------------------------------------

class TestContributionsEndpoint:

    @patch("src.api.routes.github")
    def test_returns_200_for_valid_user(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        res = client.get("/api/user/bytebymanas/contributions")
        assert res.status_code == 200

    @patch("src.api.routes.github")
    def test_response_has_required_keys(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas/contributions").get_json()
        assert "username" in data
        assert "total" in data
        assert "contributions" in data

    @patch("src.api.routes.github")
    def test_contributions_is_list(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas/contributions").get_json()
        assert isinstance(data["contributions"], list)

    @patch("src.api.routes.github")
    def test_each_item_has_points(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas/contributions").get_json()
        for item in data["contributions"]:
            assert "points" in item

    @patch("src.api.routes.github")
    def test_pr_earns_10_points(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = []
        data = client.get("/api/user/bytebymanas/contributions").get_json()
        pr_items = [c for c in data["contributions"] if c["type"] == "pull_request"]
        assert all(item["points"] == 10 for item in pr_items)

    @patch("src.api.routes.github")
    def test_issue_earns_3_points(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = []
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas/contributions").get_json()
        issue_items = [c for c in data["contributions"] if c["type"] == "issue"]
        assert all(item["points"] == 3 for item in issue_items)

    @patch("src.api.routes.github")
    def test_returns_404_for_unknown_user(self, mock_gh, client):
        mock_gh.get_user.return_value = None
        res = client.get("/api/user/nonexistent_xyz/contributions")
        assert res.status_code == 404

    @patch("src.api.routes.github")
    def test_total_matches_list_length(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = MOCK_PRS
        mock_gh.get_user_issues.return_value = MOCK_ISSUES
        data = client.get("/api/user/bytebymanas/contributions").get_json()
        assert data["total"] == len(data["contributions"])


# ---------------------------------------------------------------------------
# Repos
# ---------------------------------------------------------------------------

class TestReposEndpoint:

    @patch("src.api.routes.github")
    def test_returns_200_for_valid_user(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_user_repos.return_value = MOCK_REPOS
        res = client.get("/api/user/bytebymanas/repos")
        assert res.status_code == 200

    @patch("src.api.routes.github")
    def test_response_has_required_keys(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_user_repos.return_value = MOCK_REPOS
        data = client.get("/api/user/bytebymanas/repos").get_json()
        assert "username" in data
        assert "total" in data
        assert "repos" in data

    @patch("src.api.routes.github")
    def test_repos_is_list(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_user_repos.return_value = MOCK_REPOS
        data = client.get("/api/user/bytebymanas/repos").get_json()
        assert isinstance(data["repos"], list)

    @patch("src.api.routes.github")
    def test_each_repo_has_expected_fields(self, mock_gh, client):
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_user_repos.return_value = MOCK_REPOS
        data = client.get("/api/user/bytebymanas/repos").get_json()
        for repo in data["repos"]:
            assert "name" in repo
            assert "url" in repo
            assert "language" in repo

    @patch("src.api.routes.github")
    def test_repos_sorted_by_stars(self, mock_gh, client):
        from src.utils.cache import default_cache
        default_cache.delete("repos:bytebymanas")

        repos = [
            {**MOCK_REPOS[0], "name": "low-stars",  "stargazers_count": 1, "full_name": "u/low"},
            {**MOCK_REPOS[0], "name": "high-stars", "stargazers_count": 50, "full_name": "u/high"},
        ]
        mock_gh.get_user.return_value = MOCK_GITHUB_USER
        mock_gh.get_user_repos.return_value = repos
        data = client.get("/api/user/bytebymanas/repos").get_json()
        assert data["repos"][0]["name"] == "high-stars"


    @patch("src.api.routes.github")
    def test_returns_404_for_unknown_user(self, mock_gh, client):
        mock_gh.get_user.return_value = None
        res = client.get("/api/user/nonexistent_xyz/repos")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# Rate limit
# ---------------------------------------------------------------------------

class TestRateLimitEndpoint:

    @patch("src.api.routes.github")
    def test_returns_200(self, mock_gh, client):
        mock_gh.get_rate_limit.return_value = {"remaining": 55, "limit": 60}
        res = client.get("/api/ratelimit")
        assert res.status_code == 200

    @patch("src.api.routes.github")
    def test_response_has_github_rate_limit_key(self, mock_gh, client):
        mock_gh.get_rate_limit.return_value = {"remaining": 55, "limit": 60}
        data = client.get("/api/ratelimit").get_json()
        assert "github_rate_limit" in data

# ---------------------------------------------------------------------------
# Mentor Annotations
# ---------------------------------------------------------------------------

class TestMentorAnnotationsEndpoint:
    
    @patch("src.api.routes.db")
    def test_get_annotations(self, mock_db, client):
        mock_db.get_annotations_for_contribution.return_value = [
            {"id": 1, "mentor_username": "test_mentor", "note": "good job"}
        ]
        res = client.get("/api/contributions/1/annotations")
        assert res.status_code == 200
        data = res.get_json()
        assert "annotations" in data
        assert len(data["annotations"]) == 1
        assert data["annotations"][0]["mentor_username"] == "test_mentor"

    @patch("src.api.routes.db")
    def test_add_annotation_success(self, mock_db, client):
        mock_db.add_annotation.return_value = 1
        payload = {
            "mentor_username": "mentor1",
            "note": "Needs review",
            "verified": 0
        }
        res = client.post("/api/contributions/100/annotations", json=payload)
        assert res.status_code == 201
        assert res.get_json()["annotation_id"] == 1

    def test_add_annotation_missing_username(self, client):
        payload = {"note": "missing mentor name"}
        res = client.post("/api/contributions/100/annotations", json=payload)
        assert res.status_code == 400
        assert res.get_json()["error"] == "invalid_payload"


class TestExportEndpoint:
    """Tests for GET /api/leaderboard/export."""

    @patch("src.api.routes.db")
    def test_csv_export_returns_200(self, mock_db, client):
        """Export with default (CSV) format should return 200."""
        mock_db.get_leaderboard.return_value = []
        res = client.get("/api/leaderboard/export")
        assert res.status_code == 200

    @patch("src.api.routes.db")
    def test_csv_export_content_type(self, mock_db, client):
        """CSV export should return text/csv content type."""
        mock_db.get_leaderboard.return_value = []
        res = client.get("/api/leaderboard/export?format=csv")
        assert "text/csv" in res.content_type

    @patch("src.api.routes.db")
    def test_csv_export_has_header_row(self, mock_db, client):
        """CSV response should contain expected column headers."""
        mock_db.get_leaderboard.return_value = []
        res = client.get("/api/leaderboard/export?format=csv")
        text = res.data.decode("utf-8")
        assert "rank" in text
        assert "username" in text
        assert "total_score" in text

    @patch("src.api.routes.db")
    def test_csv_export_contains_data_rows(self, mock_db, client):
        """CSV export should include one row per leaderboard entry."""
        mock_db.get_leaderboard.return_value = [
            {
                "github_username": "user_a",
                "name": "User A",
                "department": "CS",
                "total_score": 30,
                "pr_count": 3,
                "issue_count": 0,
                "review_count": 0,
            }
        ]
        res = client.get("/api/leaderboard/export?format=csv")
        text = res.data.decode("utf-8")
        assert "user_a" in text
        assert "30" in text

    @patch("src.api.routes.db")
    def test_csv_export_content_disposition(self, mock_db, client):
        """CSV export should set a Content-Disposition attachment header."""
        mock_db.get_leaderboard.return_value = []
        res = client.get("/api/leaderboard/export?format=csv")
        assert "attachment" in res.headers.get("Content-Disposition", "")
        assert ".csv" in res.headers.get("Content-Disposition", "")

    @patch("src.api.routes.db")
    def test_json_export_returns_200(self, mock_db, client):
        """JSON export should return 200."""
        mock_db.get_leaderboard.return_value = []
        res = client.get("/api/leaderboard/export?format=json")
        assert res.status_code == 200

    @patch("src.api.routes.db")
    def test_json_export_content_disposition(self, mock_db, client):
        """JSON export should set a Content-Disposition attachment header with .json."""
        mock_db.get_leaderboard.return_value = []
        res = client.get("/api/leaderboard/export?format=json")
        disp = res.headers.get("Content-Disposition", "")
        assert "attachment" in disp
        assert ".json" in disp

    @patch("src.api.routes.db")
    def test_json_export_leaderboard_key(self, mock_db, client):
        """JSON export body should contain a 'leaderboard' key."""
        mock_db.get_leaderboard.return_value = []
        res = client.get("/api/leaderboard/export?format=json")
        import json
        body = json.loads(res.data.decode("utf-8"))
        assert "leaderboard" in body

    def test_export_invalid_format(self, client):
        """Unsupported format should return 400."""
        res = client.get("/api/leaderboard/export?format=xml")
        assert res.status_code == 400
        assert res.get_json()["error"] == "invalid_param"

    def test_export_invalid_period(self, client):
        """Invalid period should return 400."""
        res = client.get("/api/leaderboard/export?period=last_year")
        assert res.status_code == 400
        assert res.get_json()["error"] == "invalid_param"

    def test_export_invalid_limit(self, client):
        """Non-integer limit should return 400."""
        res = client.get("/api/leaderboard/export?limit=abc")
        assert res.status_code == 400
        assert res.get_json()["error"] == "invalid_param"

