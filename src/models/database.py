"""
Database layer for the Open Source Contribution Tracker.

Manages SQLite connections, schema initialization, and CRUD operations
for all entities: users, repositories, contributions, scores, and
mentor annotations.

Usage:
    db = Database()
    db.init_schema()
    db.upsert_user("bytebymanas")
"""

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "tracker.db")


class Database:
    """
    Handles all database operations using SQLite.

    For production, swap the connection string to PostgreSQL via
    the DATABASE_URL environment variable.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        # For in-memory SQLite, all operations must share a single connection.
        # A new sqlite3.connect(":memory:") call returns an empty, separate database.
        if self.db_path == ":memory:":
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        else:
            self._conn = None

    def _connect(self):
        """Return the active SQLite connection."""
        if self._conn is not None:
            return self._conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def init_schema(self):
        """
        Create all tables if they do not already exist.
        Safe to call multiple times (idempotent).
        """
        # executescript() requires a raw connection (not context manager)
        # because it issues an implicit COMMIT before running.
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            github_username TEXT    UNIQUE NOT NULL,
            github_id       INTEGER UNIQUE,
            name            TEXT,
            avatar_url      TEXT,
            department      TEXT,
            university      TEXT,
            role            TEXT    DEFAULT 'student',
            is_active       INTEGER DEFAULT 1,
            created_at      TEXT    DEFAULT (datetime('now')),
            last_synced_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS repositories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            github_repo_id  INTEGER UNIQUE NOT NULL,
            name            TEXT    NOT NULL,
            full_name       TEXT    NOT NULL,
            description     TEXT,
            language        TEXT,
            html_url        TEXT,
            is_tracked      INTEGER DEFAULT 1,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS contributions (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                 INTEGER NOT NULL REFERENCES users(id),
            repo_id                 INTEGER REFERENCES repositories(id),
            github_id               TEXT    UNIQUE NOT NULL,
            type                    TEXT    NOT NULL,
            title                   TEXT,
            url                     TEXT,
            status                  TEXT,
            is_merged               INTEGER DEFAULT 0,
            is_first_contribution   INTEGER DEFAULT 0,
            contributed_at          TEXT,
            created_at              TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scores (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            total_score     INTEGER DEFAULT 0,
            pr_count        INTEGER DEFAULT 0,
            issue_count     INTEGER DEFAULT 0,
            review_count    INTEGER DEFAULT 0,
            commit_count    INTEGER DEFAULT 0,
            period          TEXT    DEFAULT 'all_time',
            calculated_at   TEXT    DEFAULT (datetime('now')),
            UNIQUE(user_id, period)
        );

        CREATE TABLE IF NOT EXISTS mentor_annotations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            contribution_id INTEGER NOT NULL REFERENCES contributions(id),
            mentor_username TEXT    NOT NULL,
            note            TEXT,
            verified        INTEGER DEFAULT 0,
            score_override  INTEGER,
            annotated_at    TEXT    DEFAULT (datetime('now'))
        );
        """
        conn = self._connect()
        conn.executescript(schema)
        
        # Migration: Add role column if it doesn't exist
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
            logger.info("Migrated schema: Added role column to users table")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        conn.commit()
        # Do not close in-memory connections — they would lose all data.
        if self._conn is None:
            conn.close()
        logger.info("Database schema initialized at: %s", self.db_path)


    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def upsert_user(self, github_username, github_id=None, name=None,
                    avatar_url=None, department=None, university=None, role=None):
        """
        Insert a new user or update an existing one by github_username.

        Args:
            github_username (str): GitHub username (primary key equivalent)
            github_id (int): GitHub user ID
            name (str): Display name
            avatar_url (str): Avatar image URL
            department (str): University department
            university (str): University name
            role (str): User role (student, mentor, admin, org)

        Returns:
            int: Internal user ID
        """
        # We only update role if explicitly provided, to avoid downgrading an admin to student
        sql = """
        INSERT INTO users (github_username, github_id, name, avatar_url, department, university, role, last_synced_at)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE(?, 'student'), ?)
        ON CONFLICT(github_username) DO UPDATE SET
            github_id       = excluded.github_id,
            name            = excluded.name,
            avatar_url      = excluded.avatar_url,
            role            = COALESCE(?, users.role),
            last_synced_at  = excluded.last_synced_at
        """
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(sql, (github_username, github_id, name, avatar_url, department, university, role, now, role))
            conn.commit()
            if cursor.lastrowid:
                return cursor.lastrowid
            row = conn.execute("SELECT id FROM users WHERE github_username = ?", (github_username,)).fetchone()
            return row["id"]

    def get_user(self, github_username):
        """
        Fetch a user record by GitHub username.

        Args:
            github_username (str): GitHub username

        Returns:
            dict | None: User record as a dict, or None if not found
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE github_username = ?", (github_username,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_users(self):
        """
        Fetch all active tracked users.

        Returns:
            list[dict]: List of user records
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE is_active = 1 ORDER BY github_username"
            ).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Contributions
    # ------------------------------------------------------------------

    def upsert_contribution(self, user_id, github_id, contribution_type,
                             title=None, url=None, status=None,
                             is_merged=False, is_first_contribution=False,
                             contributed_at=None, repo_id=None):
        """
        Insert a contribution or ignore if it already exists (idempotent).

        Args:
            user_id (int): Internal user ID
            github_id (str): GitHub event ID (PR number, issue number, etc.)
            contribution_type (str): 'pull_request', 'issue', 'review', 'commit'
            title (str): Contribution title
            url (str): GitHub link
            status (str): 'open', 'closed', 'merged'
            is_merged (bool): Whether the PR was merged
            is_first_contribution (bool): First-time contributor flag
            contributed_at (str): ISO timestamp of the contribution
            repo_id (int): Internal repository ID

        Returns:
            int: Internal contribution ID
        """
        sql = """
        INSERT OR IGNORE INTO contributions
            (user_id, repo_id, github_id, type, title, url, status,
             is_merged, is_first_contribution, contributed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._connect() as conn:
            cursor = conn.execute(sql, (
                user_id, repo_id, github_id, contribution_type,
                title, url, status,
                int(is_merged), int(is_first_contribution), contributed_at
            ))
            conn.commit()
            if cursor.lastrowid:
                return cursor.lastrowid
            row = conn.execute(
                "SELECT id FROM contributions WHERE github_id = ?", (github_id,)
            ).fetchone()
            return row["id"]

    def get_contributions_for_user(self, user_id):
        """
        Fetch all contributions for a given internal user ID.

        Args:
            user_id (int): Internal user ID

        Returns:
            list[dict]: List of contribution records
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM contributions WHERE user_id = ? ORDER BY contributed_at DESC",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Scores
    # ------------------------------------------------------------------

    def upsert_score(self, user_id, total_score, pr_count=0,
                     issue_count=0, review_count=0, commit_count=0, period="all_time"):
        """
        Insert or update the computed score for a user.

        Args:
            user_id (int): Internal user ID
            total_score (int): Computed total score
            pr_count (int): Number of merged PRs
            issue_count (int): Number of closed issues
            review_count (int): Number of code reviews
            commit_count (int): Number of commits
            period (str): Score period ('all_time', 'this_month', 'this_week')
        """
        sql = """
        INSERT INTO scores (user_id, total_score, pr_count, issue_count, review_count, commit_count, period, calculated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, period) DO UPDATE SET
            total_score   = excluded.total_score,
            pr_count      = excluded.pr_count,
            issue_count   = excluded.issue_count,
            review_count  = excluded.review_count,
            commit_count  = excluded.commit_count,
            calculated_at = excluded.calculated_at
        """
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(sql, (user_id, total_score, pr_count, issue_count, review_count, commit_count, period, now))
            conn.commit()

    def get_leaderboard(self, period="all_time", limit=50, department=None):
        """
        Fetch the ranked leaderboard for a given period.

        Args:
            period (str): 'all_time', 'this_month', or 'this_week'
            limit (int): Maximum number of results to return
            department (str | None): If provided, restrict results to users
                whose department matches this value (case-insensitive).

        Returns:
            list[dict]: Ranked list of users with scores
        """
        params = [period]
        dept_clause = ""
        if department:
            dept_clause = "AND lower(u.department) = lower(?)"
            params.append(department)
        params.append(limit)

        sql = f"""
        SELECT
            u.github_username,
            u.name,
            u.avatar_url,
            u.department,
            s.total_score,
            s.pr_count,
            s.issue_count,
            s.review_count,
            s.calculated_at
        FROM scores s
        JOIN users u ON u.id = s.user_id
        WHERE s.period = ? AND u.is_active = 1 {dept_clause}
        ORDER BY s.total_score DESC
        LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def get_departments(self):
        """
        Return a sorted list of distinct department names from active users.

        Null or blank department values are excluded.

        Returns:
            list[str]: Sorted list of department names
        """
        sql = """
        SELECT DISTINCT department
        FROM users
        WHERE is_active = 1
          AND department IS NOT NULL
          AND trim(department) != ''
        ORDER BY department
        """
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
            return [row["department"] for row in rows]

    # ------------------------------------------------------------------
    # Mentor Annotations
    # ------------------------------------------------------------------

    def add_annotation(self, contribution_id, mentor_username, note=None, verified=0, score_override=None):
        """
        Add or update a mentor annotation for a specific contribution.
        """
        sql = """
        INSERT INTO mentor_annotations (contribution_id, mentor_username, note, verified, score_override)
        VALUES (?, ?, ?, ?, ?)
        """
        conn = self._connect()
        try:
            cursor = conn.execute(sql, (contribution_id, mentor_username, note, verified, score_override))
            conn.commit()
            return cursor.lastrowid
        finally:
            if self._conn is None:
                conn.close()

    def get_annotations_for_contribution(self, contribution_id):
        """
        Get all annotations for a specific contribution.
        """
        sql = "SELECT * FROM mentor_annotations WHERE contribution_id = ? ORDER BY annotated_at DESC"
        with self._connect() as conn:
            rows = conn.execute(sql, (contribution_id,)).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Student roster
    # ------------------------------------------------------------------

    def get_all_students(self):
        """Return all tracked students joined with their all_time score."""
        sql = """
        SELECT
            u.id,
            u.github_username,
            u.name,
            u.avatar_url,
            u.department,
            u.university,
            u.role,
            u.created_at,
            u.last_synced_at,
            COALESCE(s.total_score,  0) AS total_score,
            COALESCE(s.pr_count,     0) AS pr_count,
            COALESCE(s.issue_count,  0) AS issue_count,
            COALESCE(s.review_count, 0) AS review_count
        FROM users u
        LEFT JOIN scores s ON s.user_id = u.id AND s.period = 'all_time'
        WHERE u.is_active = 1
        ORDER BY total_score DESC, u.github_username
        """
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]

    def update_student_meta(self, github_username, department=None, university=None):
        """Update department and/or university for a tracked student. Returns bool."""
        sets, params = [], []
        if department is not None:
            sets.append("department = ?")
            params.append(department)
        if university is not None:
            sets.append("university = ?")
            params.append(university)
        if not sets:
            return False
        params.append(github_username)
        sql = f"UPDATE users SET {', '.join(sets)} WHERE github_username = ? AND is_active = 1"
        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_student(self, github_username):
        """Remove a tracked student and all associated data. Returns bool."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE github_username = ?", (github_username,)
            ).fetchone()
            if not row:
                return False
            uid = row["id"]
            conn.execute("""
                DELETE FROM mentor_annotations
                WHERE contribution_id IN (SELECT id FROM contributions WHERE user_id = ?)
            """, (uid,))
            conn.execute("DELETE FROM contributions WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM scores WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM users WHERE id = ?", (uid,))
            conn.commit()
            return True

    # ------------------------------------------------------------------
    # Mentor annotations (extended)
    # ------------------------------------------------------------------

    def get_all_annotations(self, mentor_username=None, verified=None, student_username=None):
        """Return all annotations across all contributions with join data."""
        filters, params = [], []
        if mentor_username:
            filters.append("ma.mentor_username = ?")
            params.append(mentor_username)
        if verified is not None:
            filters.append("ma.verified = ?")
            params.append(int(verified))
        if student_username:
            filters.append("u.github_username = ?")
            params.append(student_username)
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        sql = f"""
        SELECT
            ma.id,
            ma.mentor_username,
            ma.note,
            ma.verified,
            ma.score_override,
            ma.annotated_at,
            c.id              AS contribution_id,
            c.type            AS contribution_type,
            c.title           AS contribution_title,
            c.url             AS contribution_url,
            u.github_username AS student_username,
            u.name            AS student_name,
            u.avatar_url      AS student_avatar
        FROM mentor_annotations ma
        JOIN contributions c ON c.id = ma.contribution_id
        JOIN users u ON u.id = c.user_id
        {where}
        ORDER BY ma.annotated_at DESC
        """
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def update_annotation(self, annotation_id, note=None, verified=None, score_override=None):
        """Partially update a mentor annotation. Returns bool."""
        sets, params = [], []
        if note is not None:
            sets.append("note = ?")
            params.append(note)
        if verified is not None:
            sets.append("verified = ?")
            params.append(int(verified))
        if score_override is not None:
            sets.append("score_override = ?")
            params.append(score_override)
        if not sets:
            return False
        params.append(annotation_id)
        sql = f"UPDATE mentor_annotations SET {', '.join(sets)} WHERE id = ?"
        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_annotation(self, annotation_id):
        """Delete a mentor annotation by ID. Returns bool."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM mentor_annotations WHERE id = ?", (annotation_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
