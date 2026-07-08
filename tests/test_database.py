"""
Unit tests for database models.

Tests database connection and model operations defined in src/models/database.py.
Run with: python3 -m pytest tests/ -v

NOTE: These are placeholder stubs for Week 2.
      Full implementation happens when the database schema is built.
"""

import pytest
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDatabaseConnection:
    """
    Tests for database connectivity.
    TODO (Week 2): Implement when database.py has real models.
    """

    def test_placeholder_database_module_exists(self):
        """Verify the database module file exists."""
        db_path = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'models', 'database.py'
        )
        assert os.path.exists(db_path), "database.py should exist in src/models/"

    def test_placeholder_pass(self):
        """
        Placeholder test — always passes.
        Replace with real database tests in Week 2.
        """
        # TODO (Week 2): Replace with real database connection test
        assert True


class TestUserModel:
    """
    Tests for the User database model.
    TODO (Week 2): Implement after database schema is created.
    """

    def test_placeholder_user_model(self):
        """Placeholder for User model tests."""
        # TODO (Week 2): Test User CRUD operations
        assert True


class TestContributionModel:
    """
    Tests for the Contribution database model.
    TODO (Week 2): Implement after database schema is created.
    """

    def test_placeholder_contribution_model(self):
        """Placeholder for Contribution model tests."""
        # TODO (Week 2): Test Contribution CRUD operations
        assert True
