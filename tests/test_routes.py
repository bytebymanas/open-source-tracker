"""
Unit tests for Flask API routes.

Tests all HTTP endpoints defined in src/api/routes.py.
Run with: python3 -m pytest tests/ -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for GET /api/health"""

    def test_health_returns_200(self, client):
        """Health endpoint should return HTTP 200."""
        response = client.get('/api/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Health endpoint should return JSON."""
        response = client.get('/api/health')
        data = response.get_json()
        assert data is not None

    def test_health_status_ok(self, client):
        """Health endpoint should return status: ok."""
        response = client.get('/api/health')
        data = response.get_json()
        assert data['status'] == 'ok'


class TestHomeEndpoint:
    """Tests for GET /"""

    def test_home_returns_200(self, client):
        """Home endpoint should return HTTP 200."""
        response = client.get('/')
        assert response.status_code == 200


class TestUserEndpoint:
    """Tests for GET /api/user/<username>"""

    def test_user_endpoint_returns_200(self, client):
        """User endpoint should return HTTP 200 for a known user."""
        response = client.get('/api/user/bytebymanas')
        assert response.status_code == 200

    def test_user_endpoint_returns_username(self, client):
        """User endpoint should return the correct username in response."""
        response = client.get('/api/user/bytebymanas')
        data = response.get_json()
        assert data['username'] == 'bytebymanas'

    def test_user_endpoint_returns_score(self, client):
        """User endpoint should return a score object."""
        response = client.get('/api/user/bytebymanas')
        data = response.get_json()
        assert 'score' in data

    def test_user_endpoint_returns_404_for_unknown_user(self, client):
        """User endpoint should return 404 for a nonexistent user."""
        response = client.get('/api/user/this_user_does_not_exist_xyz_99999')
        assert response.status_code == 404


class TestLeaderboardEndpoint:
    """Tests for GET /api/leaderboard"""

    def test_leaderboard_returns_200(self, client):
        """Leaderboard endpoint should return HTTP 200."""
        response = client.get('/api/leaderboard')
        assert response.status_code == 200

    def test_leaderboard_returns_list(self, client):
        """Leaderboard endpoint should return a leaderboard list."""
        response = client.get('/api/leaderboard')
        data = response.get_json()
        assert 'leaderboard' in data
        assert isinstance(data['leaderboard'], list)

    def test_leaderboard_accepts_period_param(self, client):
        """Leaderboard endpoint should accept a period query param."""
        response = client.get('/api/leaderboard?period=this_month')
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('period') == 'this_month'


class TestContributionsEndpoint:
    """Tests for GET /api/user/<username>/contributions"""

    def test_contributions_returns_200_for_valid_user(self, client):
        """Contributions endpoint should return HTTP 200 for a known user."""
        response = client.get('/api/user/bytebymanas/contributions')
        assert response.status_code == 200

    def test_contributions_response_has_required_keys(self, client):
        """Response must contain username, total, and contributions keys."""
        response = client.get('/api/user/bytebymanas/contributions')
        data = response.get_json()
        assert 'username' in data
        assert 'total' in data
        assert 'contributions' in data

    def test_contributions_is_a_list(self, client):
        """contributions field should be a list."""
        response = client.get('/api/user/bytebymanas/contributions')
        data = response.get_json()
        assert isinstance(data['contributions'], list)

    def test_contributions_returns_404_for_unknown_user(self, client):
        """Contributions endpoint should return 404 for a nonexistent user."""
        response = client.get('/api/user/this_user_does_not_exist_xyz_99999/contributions')
        assert response.status_code == 404

    def test_each_contribution_has_points_field(self, client):
        """Each contribution record should include a points field."""
        response = client.get('/api/user/bytebymanas/contributions')
        data = response.get_json()
        for item in data['contributions']:
            assert 'points' in item

    def test_contributions_username_matches_request(self, client):
        """Response username should match the requested username."""
        response = client.get('/api/user/bytebymanas/contributions')
        data = response.get_json()
        assert data['username'] == 'bytebymanas'


class TestReposEndpoint:
    """Tests for GET /api/user/<username>/repos"""

    def test_repos_returns_200_for_valid_user(self, client):
        """Repos endpoint should return HTTP 200 for a known user."""
        response = client.get('/api/user/bytebymanas/repos')
        assert response.status_code == 200

    def test_repos_response_has_required_keys(self, client):
        """Response must contain username, total, and repos keys."""
        response = client.get('/api/user/bytebymanas/repos')
        data = response.get_json()
        assert 'username' in data
        assert 'total' in data
        assert 'repos' in data

    def test_repos_is_a_list(self, client):
        """repos field should be a list."""
        response = client.get('/api/user/bytebymanas/repos')
        data = response.get_json()
        assert isinstance(data['repos'], list)

    def test_repos_returns_404_for_unknown_user(self, client):
        """Repos endpoint should return 404 for a nonexistent user."""
        response = client.get('/api/user/this_user_does_not_exist_xyz_99999/repos')
        assert response.status_code == 404

    def test_each_repo_has_expected_fields(self, client):
        """Each repo record should include name, url, and language."""
        response = client.get('/api/user/bytebymanas/repos')
        data = response.get_json()
        for repo in data['repos']:
            assert 'name' in repo
            assert 'url' in repo
            assert 'language' in repo
