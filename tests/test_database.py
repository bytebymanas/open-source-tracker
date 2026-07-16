"""
Unit tests for the database layer (src/models/database.py).

Tests use an isolated in-memory SQLite database to avoid polluting
the development database. All tests are independent and idempotent.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.database import Database


@pytest.fixture
def db():
    """Provide a fresh in-memory database for each test."""
    database = Database(db_path=":memory:")
    database.init_schema()
    return database


class TestSchemaInitialization:
    """Tests for database schema setup."""

    def test_schema_initializes_without_error(self, db):
        """init_schema() should complete without raising an exception."""
        assert db is not None

    def test_schema_is_idempotent(self, db):
        """Calling init_schema() twice should not raise an error."""
        db.init_schema()
        db.init_schema()


class TestUserOperations:
    """Tests for user CRUD operations."""

    def test_upsert_user_returns_id(self, db):
        """upsert_user() should return a positive integer ID."""
        user_id = db.upsert_user("bytebymanas")
        assert isinstance(user_id, int)
        assert user_id > 0

    def test_get_user_returns_correct_username(self, db):
        """get_user() should return the user with the matching username."""
        db.upsert_user("bytebymanas", name="Manas Chhabra")
        user = db.get_user("bytebymanas")
        assert user is not None
        assert user["github_username"] == "bytebymanas"
        assert user["name"] == "Manas Chhabra"

    def test_get_user_returns_none_for_unknown(self, db):
        """get_user() should return None for a username not in the database."""
        result = db.get_user("nonexistent_user_xyz")
        assert result is None

    def test_upsert_user_is_idempotent(self, db):
        """Inserting the same username twice should not raise an error."""
        id1 = db.upsert_user("bytebymanas")
        id2 = db.upsert_user("bytebymanas", name="Updated Name")
        assert id1 == id2

    def test_upsert_user_updates_name(self, db):
        """Re-upserting a user should update their name."""
        db.upsert_user("bytebymanas", name="Old Name")
        db.upsert_user("bytebymanas", name="New Name")
        user = db.get_user("bytebymanas")
        assert user["name"] == "New Name"

    def test_get_all_users_returns_list(self, db):
        """get_all_users() should return a list."""
        db.upsert_user("user_a")
        db.upsert_user("user_b")
        users = db.get_all_users()
        assert isinstance(users, list)
        assert len(users) == 2


class TestContributionOperations:
    """Tests for contribution CRUD operations."""

    def test_upsert_contribution_returns_id(self, db):
        """upsert_contribution() should return a positive integer ID."""
        user_id = db.upsert_user("bytebymanas")
        cid = db.upsert_contribution(
            user_id=user_id,
            github_id="pr_001",
            contribution_type="pull_request",
            title="Fix bug in login flow",
            is_merged=True
        )
        assert isinstance(cid, int)
        assert cid > 0

    def test_upsert_contribution_is_idempotent(self, db):
        """Inserting the same github_id twice should not create a duplicate."""
        user_id = db.upsert_user("bytebymanas")
        id1 = db.upsert_contribution(user_id, "pr_001", "pull_request")
        id2 = db.upsert_contribution(user_id, "pr_001", "pull_request")
        assert id1 == id2

    def test_get_contributions_for_user_returns_list(self, db):
        """get_contributions_for_user() should return a list of contributions."""
        user_id = db.upsert_user("bytebymanas")
        db.upsert_contribution(user_id, "pr_001", "pull_request", is_merged=True)
        db.upsert_contribution(user_id, "issue_001", "issue")
        contribs = db.get_contributions_for_user(user_id)
        assert isinstance(contribs, list)
        assert len(contribs) == 2


class TestScoreOperations:
    """Tests for score storage and leaderboard."""

    def test_upsert_score_does_not_raise(self, db):
        """upsert_score() should store a score without raising an error."""
        user_id = db.upsert_user("bytebymanas")
        db.upsert_score(user_id, total_score=23, pr_count=2, issue_count=1)

    def test_get_leaderboard_returns_list(self, db):
        """get_leaderboard() should return a list."""
        result = db.get_leaderboard()
        assert isinstance(result, list)

    def test_leaderboard_is_sorted_by_score(self, db):
        """Leaderboard should rank higher scores first."""
        uid1 = db.upsert_user("user_low")
        uid2 = db.upsert_user("user_high")
        db.upsert_score(uid1, total_score=5)
        db.upsert_score(uid2, total_score=50)
        board = db.get_leaderboard()
        assert board[0]["github_username"] == "user_high"
        assert board[1]["github_username"] == "user_low"

class TestMentorAnnotations:
    """Tests for mentor annotation operations."""

    def test_add_annotation_returns_id(self, db):
        """add_annotation() should insert a record and return its ID."""
        user_id = db.upsert_user("testuser")
        contrib_id = db.upsert_contribution(user_id, "pr_123", "pull_request")
        ann_id = db.add_annotation(contrib_id, "mentor_alice", note="Great work!", verified=1)
        assert isinstance(ann_id, int)
        assert ann_id > 0

    def test_get_annotations_for_contribution(self, db):
        """get_annotations_for_contribution() should retrieve annotations correctly."""
        user_id = db.upsert_user("testuser")
        contrib_id = db.upsert_contribution(user_id, "pr_456", "issue")
        db.add_annotation(contrib_id, "mentor_bob", note="Needs tests", verified=0, score_override=2)
        
        annotations = db.get_annotations_for_contribution(contrib_id)
        assert len(annotations) == 1
        assert annotations[0]["mentor_username"] == "mentor_bob"
        assert annotations[0]["note"] == "Needs tests"
        assert annotations[0]["verified"] == 0
        assert annotations[0]["score_override"] == 2
