"""
GitHub API Integration Module

Handles all interactions with the GitHub REST API v3.
Supports fetching user repositories, pull requests, issues,
commits, and rate limit status.

Reference: https://docs.github.com/en/rest
"""

import requests
import os
import logging

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an unexpected error."""
    pass


class GitHubAPI:
    """
    Wrapper around the GitHub REST API v3.

    Handles authentication, request construction, error handling,
    and pagination for all GitHub API interactions.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        else:
            logger.warning("GITHUB_TOKEN not set. Requests will be rate-limited to 60/hour.")

    def _get(self, endpoint, params=None):
        """
        Internal method to make a GET request to the GitHub API.

        Args:
            endpoint (str): API endpoint path (e.g. '/users/torvalds/repos')
            params (dict): Optional query parameters

        Returns:
            dict | list: Parsed JSON response

        Raises:
            GitHubAPIError: On non-2xx response or network failure
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 404:
                return None
            if response.status_code == 403:
                raise GitHubAPIError("GitHub API rate limit exceeded or access forbidden.")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Request to %s timed out.", url)
            raise GitHubAPIError(f"Request timed out: {url}")
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            raise GitHubAPIError(str(e))

    # ------------------------------------------------------------------
    # User methods
    # ------------------------------------------------------------------

    def get_user(self, username):
        """
        Fetch public profile data for a GitHub user.

        Args:
            username (str): GitHub username

        Returns:
            dict | None: User profile data, or None if user not found
        """
        return self._get(f"/users/{username}")

    def get_user_repos(self, username, per_page=100):
        """
        Fetch all public repositories for a given user.

        Args:
            username (str): GitHub username
            per_page (int): Number of results per page (max 100)

        Returns:
            list: List of repository objects
        """
        result = self._get(
            f"/users/{username}/repos",
            params={"per_page": per_page, "sort": "updated"}
        )
        return result if result is not None else []

    # ------------------------------------------------------------------
    # Pull request methods
    # ------------------------------------------------------------------

    def get_user_pull_requests(self, username, state="closed"):
        """
        Search for pull requests authored by a user across all public repos.

        Args:
            username (str): GitHub username
            state (str): 'open', 'closed', or 'all'

        Returns:
            list: List of pull request objects
        """
        result = self._get(
            "/search/issues",
            params={
                "q": f"author:{username} type:pr state:{state}",
                "per_page": 100,
            }
        )
        if result is None:
            return []
        return result.get("items", [])

    def get_merged_pull_requests(self, username):
        """
        Fetch only merged pull requests for a user.

        Args:
            username (str): GitHub username

        Returns:
            list: List of merged pull request objects
        """
        result = self._get(
            "/search/issues",
            params={
                "q": f"author:{username} type:pr is:merged",
                "per_page": 100,
            }
        )
        if result is None:
            return []
        return result.get("items", [])

    # ------------------------------------------------------------------
    # Issue methods
    # ------------------------------------------------------------------

    def get_user_issues(self, username, state="closed"):
        """
        Search for issues created by a user across all public repos.

        Args:
            username (str): GitHub username
            state (str): 'open', 'closed', or 'all'

        Returns:
            list: List of issue objects
        """
        result = self._get(
            "/search/issues",
            params={
                "q": f"author:{username} type:issue state:{state}",
                "per_page": 100,
            }
        )
        if result is None:
            return []
        return result.get("items", [])

    # ------------------------------------------------------------------
    # Rate limit
    # ------------------------------------------------------------------

    def get_rate_limit(self):
        """
        Fetch the current GitHub API rate limit status.

        Returns:
            dict: Rate limit data including remaining requests and reset time
        """
        result = self._get("/rate_limit")
        if result:
            return result.get("rate", {})
        return {}
