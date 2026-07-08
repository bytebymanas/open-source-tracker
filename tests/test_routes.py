"""
Unit tests for Flask API routes.

Tests all HTTP endpoints defined in src/api/routes.py.
Run with: python3 -m pytest tests/ -v
"""

import pytest
import sys
import os

# Allow imports from project root
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
    """Tests for GET /api/user/<username> — placeholder tests for Week 2."""

    def test_user_endpoint_returns_200(self, client):
        """User endpoint should return HTTP 200."""
        response = client.get('/api/user/bytebymanas')
        assert response.status_code == 200

    def test_user_endpoint_returns_username(self, client):
        """User endpoint should echo back the username."""
        response = client.get('/api/user/bytebymanas')
        data = response.get_json()
        assert data['username'] == 'bytebymanas'


class TestLeaderboardEndpoint:
    """Tests for GET /api/leaderboard — placeholder tests for Week 3."""

    def test_leaderboard_returns_200(self, client):
        """Leaderboard endpoint should return HTTP 200."""
        response = client.get('/api/leaderboard')
        assert response.status_code == 200

    def test_leaderboard_returns_list(self, client):
        """Leaderboard endpoint should return a leaderboard key."""
        response = client.get('/api/leaderboard')
        data = response.get_json()
        assert 'leaderboard' in data
        assert isinstance(data['leaderboard'], list)
