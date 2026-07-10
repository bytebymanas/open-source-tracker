"""
Unit tests for the contribution scoring engine (src/utils/scoring.py).
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.scoring import ScoringEngine, SCORE_WEIGHTS, FIRST_CONTRIBUTOR_BONUS


class TestScoringEngineInitialization:

    def test_default_weights_are_set(self):
        engine = ScoringEngine()
        assert engine.weights == SCORE_WEIGHTS

    def test_custom_weights_override_defaults(self):
        custom = {"pull_request": 20, "issue": 5}
        engine = ScoringEngine(weights=custom)
        assert engine.weights["pull_request"] == 20

    def test_default_first_contributor_bonus(self):
        engine = ScoringEngine()
        assert engine.first_contributor_bonus == FIRST_CONTRIBUTOR_BONUS


class TestScoreContribution:

    def test_merged_pr_scores_10_points(self):
        engine = ScoringEngine()
        result = engine.score_contribution({"type": "pull_request", "is_merged": True})
        assert result == 10

    def test_unmerged_pr_scores_zero(self):
        engine = ScoringEngine()
        result = engine.score_contribution({"type": "pull_request", "is_merged": False})
        assert result == 0

    def test_issue_scores_3_points(self):
        engine = ScoringEngine()
        result = engine.score_contribution({"type": "issue", "is_merged": False})
        assert result == 3

    def test_review_scores_5_points(self):
        engine = ScoringEngine()
        result = engine.score_contribution({"type": "review", "is_merged": False})
        assert result == 5

    def test_commit_scores_1_point(self):
        engine = ScoringEngine()
        result = engine.score_contribution({"type": "commit", "is_merged": False})
        assert result == 1

    def test_first_contributor_bonus_added(self):
        engine = ScoringEngine()
        result = engine.score_contribution({
            "type": "issue",
            "is_merged": False,
            "is_first_contribution": True
        })
        assert result == 3 + FIRST_CONTRIBUTOR_BONUS

    def test_unknown_type_scores_zero(self):
        engine = ScoringEngine()
        result = engine.score_contribution({"type": "unknown_event", "is_merged": False})
        assert result == 0


class TestComputeScore:

    def test_empty_contributions_returns_zero(self):
        engine = ScoringEngine()
        result = engine.compute_score([])
        assert result["total_score"] == 0

    def test_total_score_is_sum_of_parts(self):
        engine = ScoringEngine()
        contributions = [
            {"type": "pull_request", "is_merged": True},
            {"type": "issue", "is_merged": False},
            {"type": "review", "is_merged": False},
        ]
        result = engine.compute_score(contributions)
        assert result["total_score"] == 18

    def test_counts_are_correct(self):
        engine = ScoringEngine()
        contributions = [
            {"type": "pull_request", "is_merged": True},
            {"type": "pull_request", "is_merged": False},
            {"type": "issue", "is_merged": False},
            {"type": "review", "is_merged": False},
            {"type": "commit", "is_merged": False},
        ]
        result = engine.compute_score(contributions)
        assert result["pr_count"] == 1
        assert result["issue_count"] == 1
        assert result["review_count"] == 1
        assert result["commit_count"] == 1

    def test_breakdown_has_one_entry_per_contribution(self):
        engine = ScoringEngine()
        contributions = [
            {"type": "pull_request", "is_merged": True, "github_id": "pr_1"},
            {"type": "issue", "is_merged": False, "github_id": "issue_1"},
        ]
        result = engine.compute_score(contributions)
        assert len(result["breakdown"]) == 2

    def test_first_contributor_bonus_applied_in_total(self):
        engine = ScoringEngine()
        contributions = [
            {"type": "pull_request", "is_merged": True, "is_first_contribution": True},
        ]
        result = engine.compute_score(contributions)
        assert result["total_score"] == 10 + FIRST_CONTRIBUTOR_BONUS

    def test_custom_weights_affect_score(self):
        engine = ScoringEngine(weights={"pull_request": 25, "issue": 5, "review": 5, "commit": 1})
        contributions = [{"type": "pull_request", "is_merged": True}]
        result = engine.compute_score(contributions)
        assert result["total_score"] == 25
