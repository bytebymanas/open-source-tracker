"""
Tests for Settings — Scoring Weights API.

Covers:
    GET  /api/settings/weights
    POST /api/settings/weights
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestGetWeights:

    def test_returns_200(self, client):
        res = client.get("/api/settings/weights")
        assert res.status_code == 200

    def test_response_has_weights_key(self, client):
        res = client.get("/api/settings/weights")
        assert "weights" in res.get_json()

    def test_default_keys_present(self, client):
        weights = client.get("/api/settings/weights").get_json()["weights"]
        assert "pr_points"           in weights
        assert "issue_points"        in weights
        assert "review_points"       in weights
        assert "first_contrib_bonus" in weights


class TestUpdateWeights:

    def test_update_single_field_returns_200(self, client):
        res = client.post("/api/settings/weights",
                          json={"pr_points": 15},
                          content_type="application/json")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "ok"
        assert data["updated"]["pr_points"] == 15

    def test_updated_value_reflects_in_get(self, client):
        client.post("/api/settings/weights",
                    json={"issue_points": 7},
                    content_type="application/json")
        weights = client.get("/api/settings/weights").get_json()["weights"]
        assert weights["issue_points"] == 7

    def test_update_all_fields(self, client):
        payload = {
            "pr_points": 12,
            "issue_points": 4,
            "review_points": 6,
            "first_contrib_bonus": 8,
        }
        res = client.post("/api/settings/weights",
                          json=payload,
                          content_type="application/json")
        assert res.status_code == 200
        weights = res.get_json()["weights"]
        assert weights["pr_points"] == 12
        assert weights["issue_points"] == 4
        assert weights["review_points"] == 6
        assert weights["first_contrib_bonus"] == 8

    def test_unknown_field_returns_400_if_only_bad_fields(self, client):
        res = client.post("/api/settings/weights",
                          json={"bad_field": 99},
                          content_type="application/json")
        assert res.status_code == 400
        assert res.get_json()["error"] == "invalid_payload"

    def test_negative_value_returns_400(self, client):
        res = client.post("/api/settings/weights",
                          json={"pr_points": -5},
                          content_type="application/json")
        assert res.status_code == 400

    def test_mixed_valid_invalid_still_saves_valid(self, client):
        res = client.post("/api/settings/weights",
                          json={"review_points": 10, "bad_key": 5},
                          content_type="application/json")
        # Should succeed for valid keys, report errors for unknown
        assert res.status_code == 200
        data = res.get_json()
        assert "review_points" in data["updated"]
        assert data["errors"] is not None

    def test_empty_body_returns_400(self, client):
        res = client.post("/api/settings/weights",
                          json={},
                          content_type="application/json")
        # Empty body — no valid, no invalid fields updated
        assert res.status_code == 400

    def test_zero_value_is_valid(self, client):
        res = client.post("/api/settings/weights",
                          json={"first_contrib_bonus": 0},
                          content_type="application/json")
        assert res.status_code == 200
        assert res.get_json()["weights"]["first_contrib_bonus"] == 0
