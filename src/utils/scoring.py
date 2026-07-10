"""
Contribution Scoring Engine

Computes weighted scores for GitHub contributions based on type,
merge status, and first-time contributor status.

Scoring formula:
    score = (merged_prs × 10) + (reviews × 5) + (issues_closed × 3) + first_contributor_bonus

Bonus:
    +5 points if the user is a first-time contributor to that repository.

Usage:
    from src.utils.scoring import ScoringEngine
    engine = ScoringEngine()
    score = engine.compute_score(contributions)
"""

import logging

logger = logging.getLogger(__name__)

# Point weights per contribution type
SCORE_WEIGHTS = {
    "pull_request": 10,   # merged pull requests
    "review": 5,          # code reviews submitted
    "issue": 3,           # issues closed/opened
    "commit": 1,          # individual commits
}

FIRST_CONTRIBUTOR_BONUS = 5


class ScoringEngine:
    """
    Computes contribution scores using a configurable weighted formula.

    Weights can be overridden at instantiation for future flexibility
    (e.g., per-department custom scoring).
    """

    def __init__(self, weights=None, first_contributor_bonus=None):
        """
        Initialize the scoring engine.

        Args:
            weights (dict): Override default score weights per contribution type.
            first_contributor_bonus (int): Override the first-contributor point bonus.
        """
        self.weights = weights or SCORE_WEIGHTS
        self.first_contributor_bonus = (
            first_contributor_bonus
            if first_contributor_bonus is not None
            else FIRST_CONTRIBUTOR_BONUS
        )

    def score_contribution(self, contribution):
        """
        Compute the score for a single contribution record.

        Args:
            contribution (dict): A contribution record with at least:
                - 'type' (str): 'pull_request', 'review', 'issue', or 'commit'
                - 'is_merged' (bool | int): Whether a PR was merged
                - 'is_first_contribution' (bool | int): First-time contributor flag

        Returns:
            int: Points awarded for this contribution
        """
        contribution_type = contribution.get("type", "")
        is_merged = bool(contribution.get("is_merged", False))
        is_first = bool(contribution.get("is_first_contribution", False))

        base_score = 0

        if contribution_type == "pull_request":
            # Only award PR points if the PR was actually merged
            if is_merged:
                base_score = self.weights.get("pull_request", 10)
            else:
                base_score = 0
        else:
            base_score = self.weights.get(contribution_type, 0)

        bonus = self.first_contributor_bonus if is_first else 0
        total = base_score + bonus

        logger.debug(
            "Scored contribution type=%s merged=%s first=%s → %d pts",
            contribution_type, is_merged, is_first, total
        )
        return total

    def compute_score(self, contributions):
        """
        Compute the total score and breakdown across a list of contributions.

        Args:
            contributions (list[dict]): List of contribution records

        Returns:
            dict: Score summary with keys:
                - 'total_score' (int)
                - 'pr_count' (int): number of merged PRs
                - 'issue_count' (int)
                - 'review_count' (int)
                - 'commit_count' (int)
                - 'breakdown' (list[dict]): per-contribution scores
        """
        total_score = 0
        pr_count = 0
        issue_count = 0
        review_count = 0
        commit_count = 0
        breakdown = []

        for contrib in contributions:
            points = self.score_contribution(contrib)
            total_score += points
            ctype = contrib.get("type", "")

            if ctype == "pull_request" and contrib.get("is_merged"):
                pr_count += 1
            elif ctype == "issue":
                issue_count += 1
            elif ctype == "review":
                review_count += 1
            elif ctype == "commit":
                commit_count += 1

            breakdown.append({
                "github_id": contrib.get("github_id"),
                "type": ctype,
                "points": points,
            })

        return {
            "total_score": total_score,
            "pr_count": pr_count,
            "issue_count": issue_count,
            "review_count": review_count,
            "commit_count": commit_count,
            "breakdown": breakdown,
        }
