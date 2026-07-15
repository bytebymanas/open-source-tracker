"""
Integration tests for the full contribution pipeline.

These tests verify that the complete data flow works correctly:
    GitHub API (mocked) → Scoring Engine → Database → API Response

All external calls are mocked so tests run offline and consistently.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.models.database import Database
from src.utils.scoring import ScoringEngine
from src.utils.cache import Cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def db():
    """Isolated in-memory database for each test."""
    database = Database(db_path=":memory:")
    database.init_schema()
    return database


@pytest.fixture
def scorer():
    return ScoringEngine()


@pytest.fixture
def cache():
    return Cache(ttl=60)


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

GITHUB_USER = {
    "id": 99001,
    "login": "testcontributor",
    "name": "Test Contributor",
    "avatar_url": "https://avatars.github.com/u/99001",
    "public_repos": 8,
}

GITHUB_PRS = [
    {"id": 101, "title": "Add feature A", "html_url": "https://github.com/org/repo/pull/1", "repository_url": "https://api.github.com/repos/org/repo"},
    {"id": 102, "title": "Fix critical bug",  "html_url": "https://github.com/org/repo/pull/2", "repository_url": "https://api.github.com/repos/org/repo"},
    {"id": 103, "title": "Improve docs",      "html_url": "https://github.com/org/repo/pull/3", "repository_url": "https://api.github.com/repos/org/repo"},
]

GITHUB_ISSUES = [
    {"id": 201, "title": "Bug report #1", "html_url": "https://github.com/org/repo/issues/1", "repository_url": "https://api.github.com/repos/org/repo", "state": "closed"},
    {"id": 202, "title": "Feature request", "html_url": "https://github.com/org/repo/issues/2", "repository_url": "https://api.github.com/repos/org/repo", "state": "closed"},
]


# ---------------------------------------------------------------------------
# Scoring pipeline tests
# ---------------------------------------------------------------------------

class TestScoringPipeline:
    """Verify scoring engine computes correct totals for combined inputs."""

    def test_three_prs_and_two_issues(self, scorer):
        """3 merged PRs (30pts) + 2 issues (6pts) = 36pts total."""
        contributions = (
            [{"type": "pull_request", "is_merged": True,  "is_first_contribution": False}] * 3 +
            [{"type": "issue",        "is_merged": False, "is_first_contribution": False}] * 2
        )
        result = scorer.compute_score(contributions)
        assert result["total_score"] == 36
        assert result["pr_count"]    == 3
        assert result["issue_count"] == 2

    def test_unmerged_prs_score_zero(self, scorer):
        """Unmerged PRs should not add to the score."""
        contributions = [
            {"type": "pull_request", "is_merged": False, "is_first_contribution": False},
            {"type": "pull_request", "is_merged": False, "is_first_contribution": False},
        ]
        result = scorer.compute_score(contributions)
        assert result["total_score"] == 0
        assert result["pr_count"]    == 0

    def test_first_contributor_bonus_applied_once(self, scorer):
        """First-contributor bonus applies per contribution, not per user."""
        contributions = [
            {"type": "pull_request", "is_merged": True, "is_first_contribution": True},
            {"type": "issue", "is_merged": False, "is_first_contribution": True},
        ]
        result = scorer.compute_score(contributions)
        # 10 + 5(bonus) + 3 + 5(bonus) = 23
        assert result["total_score"] == 23

    def test_only_issues_no_prs(self, scorer):
        """Score should work with issues only."""
        contributions = [
            {"type": "issue", "is_merged": False, "is_first_contribution": False}
        ] * 5
        result = scorer.compute_score(contributions)
        assert result["total_score"] == 15
        assert result["issue_count"] == 5


# ---------------------------------------------------------------------------
# DB + Scoring integration
# ---------------------------------------------------------------------------

class TestDatabaseScoringIntegration:
    """Test that computed scores are correctly persisted to the database."""

    def test_score_persisted_after_compute(self, db, scorer):
        """Score computed by engine should be stored and retrievable from DB."""
        user_id = db.upsert_user("testcontributor", github_id=99001, name="Test")
        contributions = [
            {"type": "pull_request", "is_merged": True,  "is_first_contribution": False},
            {"type": "issue",        "is_merged": False, "is_first_contribution": False},
        ]
        result = scorer.compute_score(contributions)
        db.upsert_score(
            user_id=user_id,
            total_score=result["total_score"],
            pr_count=result["pr_count"],
            issue_count=result["issue_count"],
        )
        board = db.get_leaderboard()
        assert len(board) == 1
        assert board[0]["total_score"] == 13  # 10 + 3

    def test_leaderboard_ranking_with_multiple_users(self, db, scorer):
        """Leaderboard should rank users by descending score."""
        users = [
            ("alice", [{"type": "pull_request", "is_merged": True,  "is_first_contribution": False}] * 5),  # 50
            ("bob",   [{"type": "issue",        "is_merged": False, "is_first_contribution": False}] * 4),  # 12
            ("carol", [{"type": "pull_request", "is_merged": True,  "is_first_contribution": False}] * 2),  # 20
        ]
        for uname, contribs in users:
            uid = db.upsert_user(uname)
            res = scorer.compute_score(contribs)
            db.upsert_score(uid, res["total_score"], res["pr_count"], res["issue_count"])

        board = db.get_leaderboard()
        names = [r["github_username"] for r in board]
        assert names == ["alice", "carol", "bob"]

    def test_score_update_replaces_old_value(self, db, scorer):
        """Re-upserting a score should replace the previous value, not add to it."""
        uid = db.upsert_user("updateuser")
        db.upsert_score(uid, total_score=10)
        db.upsert_score(uid, total_score=50)
        board = db.get_leaderboard()
        assert board[0]["total_score"] == 50


# ---------------------------------------------------------------------------
# Full API pipeline (GitHub → score → DB → response)
# ---------------------------------------------------------------------------

class TestFullAPIPipeline:
    """End-to-end test: mocked GitHub data flows through scoring and DB to API."""

    @patch("src.api.routes.github")
    def test_user_score_reflects_github_data(self, mock_gh, client):
        """Score in API response must match the expected scoring of mock PRs + issues."""
        mock_gh.get_user.return_value = GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = GITHUB_PRS    # 3 PRs → 30pts
        mock_gh.get_user_issues.return_value = GITHUB_ISSUES           # 2 issues → 6pts

        from src.utils.cache import default_cache
        default_cache.delete("user:testcontributor")

        data = client.get("/api/user/testcontributor").get_json()
        assert data["score"]["total"] == 36

    @patch("src.api.routes.github")
    def test_contributions_count_matches_github_data(self, mock_gh, client):
        """Total contributions returned must equal PRs + issues fetched from GitHub."""
        mock_gh.get_user.return_value = GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = GITHUB_PRS
        mock_gh.get_user_issues.return_value = GITHUB_ISSUES

        from src.utils.cache import default_cache
        default_cache.delete("contributions:testcontributor")

        data = client.get("/api/user/testcontributor/contributions").get_json()
        assert data["total"] == len(GITHUB_PRS) + len(GITHUB_ISSUES)  # 5

    @patch("src.api.routes.github")
    def test_contributions_ordered_by_points_desc(self, mock_gh, client):
        """Contributions list should be sorted highest points first."""
        mock_gh.get_user.return_value = GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = GITHUB_PRS
        mock_gh.get_user_issues.return_value = GITHUB_ISSUES

        from src.utils.cache import default_cache
        default_cache.delete("contributions:testcontributor")

        data = client.get("/api/user/testcontributor/contributions").get_json()
        points = [c["points"] for c in data["contributions"]]
        assert points == sorted(points, reverse=True)

    @patch("src.api.routes.github")
    def test_empty_github_data_returns_zero_score(self, mock_gh, client):
        """User with no PRs or issues should have a total score of 0."""
        mock_gh.get_user.return_value = GITHUB_USER
        mock_gh.get_merged_pull_requests.return_value = []
        mock_gh.get_user_issues.return_value = []

        from src.utils.cache import default_cache
        default_cache.delete("user:testcontributor")

        data = client.get("/api/user/testcontributor").get_json()
        assert data["score"]["total"] == 0

    @patch("src.api.routes.github")
    def test_nonexistent_user_returns_404_everywhere(self, mock_gh, client):
        """All user endpoints must return 404 for an unknown GitHub user."""
        mock_gh.get_user.return_value = None
        username = "ghost_user_xyz_not_real"

        assert client.get(f"/api/user/{username}").status_code == 404
        assert client.get(f"/api/user/{username}/contributions").status_code == 404
        assert client.get(f"/api/user/{username}/repos").status_code == 404


# ---------------------------------------------------------------------------
# Cache integration
# ---------------------------------------------------------------------------

class TestCacheIntegration:
    """Verify that responses are cached and served correctly."""

    def test_cache_stores_and_returns_same_value(self, cache):
        """Value stored in cache should be returned on the next get."""
        payload = {"username": "bytebymanas", "score": {"total": 42}}
        cache.set("user:bytebymanas", payload)
        assert cache.get("user:bytebymanas") == payload

    def test_cache_returns_none_after_expiry(self, cache):
        """Expired entries should return None."""
        import time
        short_cache = Cache(ttl=1)
        short_cache.set("key", "value")
        time.sleep(1.1)
        assert short_cache.get("key") is None

    def test_cache_prevents_duplicate_api_calls(self):
        """If a cached response exists, the route should not call GitHub again."""
        from src.utils.cache import default_cache
        cache_key = "user:cached_user"
        default_cache.set(cache_key, {
            "username": "cached_user",
            "score": {"total": 99, "merged_prs": 9, "issues_closed": 3, "reviews": 0}
        })

        app.config["TESTING"] = True
        with app.test_client() as c:
            with patch("src.api.routes.github") as mock_gh:
                res = c.get("/api/user/cached_user")
                # GitHub should NOT be called — cache hit
                mock_gh.get_user.assert_not_called()
                assert res.status_code == 200

        default_cache.delete(cache_key)
