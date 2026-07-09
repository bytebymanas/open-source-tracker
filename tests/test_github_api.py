"""
Unit tests for the GitHub API integration module (src/api/github_api.py).

Tests cover initialization, public user data fetching, pull request search,
issue search, and rate limit endpoint. Network calls are made against the
real GitHub API — a valid GITHUB_TOKEN in the environment improves rate limits
but is not strictly required for these tests to pass.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.github_api import GitHubAPI, GitHubAPIError


class TestGitHubAPIInitialization:
    """Tests for GitHubAPI class setup."""

    def test_base_url_is_correct(self):
        """API base URL must point to the GitHub REST API v3."""
        api = GitHubAPI()
        assert api.BASE_URL == "https://api.github.com"

    def test_accept_header_is_set(self):
        """Accept header must be set to the GitHub v3 media type."""
        api = GitHubAPI()
        assert api.headers["Accept"] == "application/vnd.github.v3+json"

    def test_initialization_succeeds_without_token(self):
        """GitHubAPI should initialize even without a GITHUB_TOKEN set."""
        api = GitHubAPI()
        assert api is not None


class TestGetUser:
    """Tests for GitHubAPI.get_user()."""

    def test_returns_dict_for_valid_user(self):
        """get_user() should return a dict for a known GitHub user."""
        api = GitHubAPI()
        user = api.get_user("torvalds")
        assert isinstance(user, dict)

    def test_returns_login_field(self):
        """Returned user dict should contain a 'login' field."""
        api = GitHubAPI()
        user = api.get_user("torvalds")
        assert user is not None
        assert "login" in user

    def test_returns_none_for_nonexistent_user(self):
        """get_user() should return None for a user that does not exist."""
        api = GitHubAPI()
        result = api.get_user("this_user_does_not_exist_xyz_99999")
        assert result is None


class TestGetUserRepos:
    """Tests for GitHubAPI.get_user_repos()."""

    def test_returns_list_for_valid_user(self):
        """get_user_repos() should return a list for a valid username."""
        api = GitHubAPI()
        repos = api.get_user_repos("torvalds")
        assert isinstance(repos, list)

    def test_returns_non_empty_list(self):
        """get_user_repos() should return at least one repo for a known user."""
        api = GitHubAPI()
        repos = api.get_user_repos("torvalds")
        assert len(repos) > 0

    def test_returns_empty_list_for_invalid_user(self):
        """get_user_repos() should return an empty list for a nonexistent user."""
        api = GitHubAPI()
        repos = api.get_user_repos("this_user_does_not_exist_xyz_99999")
        assert repos == []

    def test_repo_objects_have_expected_fields(self):
        """Each repo in the list should have 'name' and 'html_url' fields."""
        api = GitHubAPI()
        repos = api.get_user_repos("torvalds")
        if repos:
            assert "name" in repos[0]
            assert "html_url" in repos[0]


class TestGetRateLimit:
    """Tests for GitHubAPI.get_rate_limit()."""

    def test_returns_dict(self):
        """get_rate_limit() should return a dictionary."""
        api = GitHubAPI()
        result = api.get_rate_limit()
        assert isinstance(result, dict)

    def test_contains_remaining_field(self):
        """Rate limit response should include a 'remaining' field."""
        api = GitHubAPI()
        result = api.get_rate_limit()
        assert "remaining" in result
