"""
Tests for student roster and mentor dashboard API routes.

Covers:
    GET  /api/students
    POST /api/students/import
    PATCH /api/students/<username>
    DELETE /api/students/<username>
    GET  /api/annotations
    PATCH /api/annotations/<id>
    DELETE /api/annotations/<id>
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
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


MOCK_STUDENTS = [
    {
        "id": 1, "github_username": "alice", "name": "Alice",
        "avatar_url": "https://github.com/alice.png", "department": "CSE",
        "university": "CU", "created_at": "2026-01-01", "last_synced_at": "2026-07-01",
        "total_score": 50, "pr_count": 5, "issue_count": 0, "review_count": 0,
    },
    {
        "id": 2, "github_username": "bob", "name": "Bob",
        "avatar_url": "https://github.com/bob.png", "department": "ECE",
        "university": "CU", "created_at": "2026-01-02", "last_synced_at": "2026-07-02",
        "total_score": 30, "pr_count": 3, "issue_count": 0, "review_count": 0,
    },
]

MOCK_ANNOTATIONS = [
    {
        "id": 1, "mentor_username": "mentor1", "note": "Great PR",
        "verified": 1, "score_override": None, "annotated_at": "2026-07-01T10:00:00",
        "contribution_id": 10, "contribution_type": "pull_request",
        "contribution_title": "Fix login", "contribution_url": "https://github.com/t/r/pull/1",
        "student_username": "alice", "student_name": "Alice",
        "student_avatar": "https://github.com/alice.png",
    },
]


# ---------------------------------------------------------------------------
# GET /api/students
# ---------------------------------------------------------------------------

class TestListStudents:

    @patch("src.api.routes.db")
    def test_returns_200_and_student_list(self, mock_db, client):
        mock_db.get_all_students.return_value = MOCK_STUDENTS
        res = client.get("/api/students")
        assert res.status_code == 200
        data = res.get_json()
        assert data["total"] == 2
        assert len(data["students"]) == 2

    @patch("src.api.routes.db")
    def test_empty_roster_returns_zero(self, mock_db, client):
        mock_db.get_all_students.return_value = []
        res = client.get("/api/students")
        assert res.status_code == 200
        assert res.get_json()["total"] == 0

    @patch("src.api.routes.db")
    def test_response_contains_score_fields(self, mock_db, client):
        mock_db.get_all_students.return_value = MOCK_STUDENTS
        res = client.get("/api/students")
        student = res.get_json()["students"][0]
        assert "total_score" in student
        assert "pr_count" in student
        assert "department" in student


# ---------------------------------------------------------------------------
# POST /api/students/import
# ---------------------------------------------------------------------------

class TestImportStudents:

    MOCK_USER_DATA = {
        "id": 1, "login": "alice", "name": "Alice",
        "avatar_url": "https://github.com/alice.png",
    }
    MOCK_SCORE_DATA = [{"type": "pull_request", "is_merged": True, "is_first_contribution": False}]
    MOCK_SCORED = {"total_score": 10, "merged_prs": 1, "issues_closed": 0, "reviews": 0}

    @patch("src.api.routes.db")
    @patch("src.api.routes.scorer")
    @patch("src.api.routes.github")
    def test_valid_import_returns_200(self, mock_gh, mock_scorer, mock_db, client):
        mock_gh.get_user.return_value = self.MOCK_USER_DATA
        mock_gh.get_user_contributions.return_value = self.MOCK_SCORE_DATA
        mock_scorer.score_contributions.return_value = self.MOCK_SCORED
        mock_db.upsert_user.return_value = 1
        res = client.post("/api/students/import",
                          json={"usernames": ["alice"]},
                          content_type="application/json")
        assert res.status_code == 200
        data = res.get_json()
        assert data["imported"] == 1
        assert data["failed"] == 0

    def test_missing_usernames_returns_400(self, client):
        res = client.post("/api/students/import", json={},
                          content_type="application/json")
        assert res.status_code == 400

    def test_empty_list_returns_400(self, client):
        res = client.post("/api/students/import", json={"usernames": []},
                          content_type="application/json")
        assert res.status_code == 400

    @patch("src.api.routes.db")
    @patch("src.api.routes.scorer")
    @patch("src.api.routes.github")
    def test_github_error_reported_in_results(self, mock_gh, mock_scorer, mock_db, client):
        from src.api.github_api import GitHubAPIError
        mock_gh.get_user.side_effect = GitHubAPIError("not found")
        res = client.post("/api/students/import",
                          json={"usernames": ["nonexistent_xyz_999"]},
                          content_type="application/json")
        assert res.status_code == 200
        data = res.get_json()
        assert data["failed"] == 1
        assert data["results"][0]["status"] == "error"

    @patch("src.api.routes.db")
    @patch("src.api.routes.scorer")
    @patch("src.api.routes.github")
    def test_whitespace_usernames_stripped(self, mock_gh, mock_scorer, mock_db, client):
        mock_gh.get_user.return_value = self.MOCK_USER_DATA
        mock_gh.get_user_contributions.return_value = self.MOCK_SCORE_DATA
        mock_scorer.score_contributions.return_value = self.MOCK_SCORED
        mock_db.upsert_user.return_value = 1
        res = client.post("/api/students/import",
                          json={"usernames": ["  alice  "]},
                          content_type="application/json")
        assert res.status_code == 200
        # Verify the username passed to get_user was stripped
        mock_gh.get_user.assert_called_with("alice")


# ---------------------------------------------------------------------------
# PATCH /api/students/<username>
# ---------------------------------------------------------------------------

class TestUpdateStudent:

    @patch("src.api.routes.db")
    def test_update_department_returns_200(self, mock_db, client):
        mock_db.update_student_meta.return_value = True
        res = client.patch("/api/students/alice",
                           json={"department": "CSE"},
                           content_type="application/json")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"

    @patch("src.api.routes.db")
    def test_update_nonexistent_student_returns_404(self, mock_db, client):
        mock_db.update_student_meta.return_value = False
        res = client.patch("/api/students/ghost",
                           json={"department": "ECE"},
                           content_type="application/json")
        assert res.status_code == 404

    def test_no_fields_returns_400(self, client):
        res = client.patch("/api/students/alice", json={},
                           content_type="application/json")
        assert res.status_code == 400

    @patch("src.api.routes.db")
    def test_update_both_fields(self, mock_db, client):
        mock_db.update_student_meta.return_value = True
        res = client.patch("/api/students/alice",
                           json={"department": "CSE", "university": "CU"},
                           content_type="application/json")
        assert res.status_code == 200
        mock_db.update_student_meta.assert_called_once_with(
            "alice", department="CSE", university="CU"
        )


# ---------------------------------------------------------------------------
# DELETE /api/students/<username>
# ---------------------------------------------------------------------------

class TestDeleteStudent:

    @patch("src.api.routes.db")
    def test_delete_existing_returns_200(self, mock_db, client):
        mock_db.delete_student.return_value = True
        res = client.delete("/api/students/alice")
        assert res.status_code == 200
        assert res.get_json()["deleted"] is True

    @patch("src.api.routes.db")
    def test_delete_nonexistent_returns_404(self, mock_db, client):
        mock_db.delete_student.return_value = False
        res = client.delete("/api/students/ghost")
        assert res.status_code == 404
        assert res.get_json()["error"] == "not_found"

    @patch("src.api.routes.db")
    def test_delete_returns_username_in_response(self, mock_db, client):
        mock_db.delete_student.return_value = True
        res = client.delete("/api/students/alice")
        assert res.get_json()["username"] == "alice"


# ---------------------------------------------------------------------------
# GET /api/annotations
# ---------------------------------------------------------------------------

class TestListAnnotations:

    @patch("src.api.routes.db")
    def test_returns_all_annotations(self, mock_db, client):
        mock_db.get_all_annotations.return_value = MOCK_ANNOTATIONS
        res = client.get("/api/annotations")
        assert res.status_code == 200
        data = res.get_json()
        assert data["total"] == 1
        assert data["annotations"][0]["mentor_username"] == "mentor1"

    @patch("src.api.routes.db")
    def test_filter_by_mentor(self, mock_db, client):
        mock_db.get_all_annotations.return_value = MOCK_ANNOTATIONS
        res = client.get("/api/annotations?mentor=mentor1")
        assert res.status_code == 200
        mock_db.get_all_annotations.assert_called_once_with(
            mentor_username="mentor1", verified=None, student_username=None
        )

    @patch("src.api.routes.db")
    def test_filter_by_verified(self, mock_db, client):
        mock_db.get_all_annotations.return_value = []
        res = client.get("/api/annotations?verified=1")
        assert res.status_code == 200
        mock_db.get_all_annotations.assert_called_once_with(
            mentor_username=None, verified=1, student_username=None
        )

    def test_invalid_verified_param_returns_400(self, client):
        res = client.get("/api/annotations?verified=maybe")
        assert res.status_code == 400

    @patch("src.api.routes.db")
    def test_filter_by_student(self, mock_db, client):
        mock_db.get_all_annotations.return_value = MOCK_ANNOTATIONS
        res = client.get("/api/annotations?student=alice")
        assert res.status_code == 200
        mock_db.get_all_annotations.assert_called_once_with(
            mentor_username=None, verified=None, student_username="alice"
        )


# ---------------------------------------------------------------------------
# PATCH /api/annotations/<id>
# ---------------------------------------------------------------------------

class TestUpdateAnnotation:

    @patch("src.api.routes.db")
    def test_update_verified_returns_200(self, mock_db, client):
        mock_db.update_annotation.return_value = True
        res = client.patch("/api/annotations/1",
                           json={"verified": 1},
                           content_type="application/json")
        assert res.status_code == 200
        assert res.get_json()["annotation_id"] == 1

    @patch("src.api.routes.db")
    def test_update_nonexistent_returns_404(self, mock_db, client):
        mock_db.update_annotation.return_value = False
        res = client.patch("/api/annotations/999",
                           json={"verified": 0},
                           content_type="application/json")
        assert res.status_code == 404

    def test_no_fields_returns_400(self, client):
        res = client.patch("/api/annotations/1", json={},
                           content_type="application/json")
        assert res.status_code == 400

    @patch("src.api.routes.db")
    def test_update_note_and_override(self, mock_db, client):
        mock_db.update_annotation.return_value = True
        res = client.patch("/api/annotations/1",
                           json={"note": "updated note", "score_override": 8},
                           content_type="application/json")
        assert res.status_code == 200
        mock_db.update_annotation.assert_called_once_with(
            1, note="updated note", verified=None, score_override=8
        )


# ---------------------------------------------------------------------------
# DELETE /api/annotations/<id>
# ---------------------------------------------------------------------------

class TestDeleteAnnotation:

    @patch("src.api.routes.db")
    def test_delete_existing_returns_200(self, mock_db, client):
        mock_db.delete_annotation.return_value = True
        res = client.delete("/api/annotations/1")
        assert res.status_code == 200
        assert res.get_json()["deleted"] is True

    @patch("src.api.routes.db")
    def test_delete_nonexistent_returns_404(self, mock_db, client):
        mock_db.delete_annotation.return_value = False
        res = client.delete("/api/annotations/999")
        assert res.status_code == 404
        assert res.get_json()["error"] == "not_found"
