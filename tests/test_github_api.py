"""
Unit tests for GitHub API integration
"""

import pytest
from src.api.github_api import GitHubAPI

class TestGitHubAPI:
    """Test cases for GitHubAPI class"""
    
    def test_github_api_initialization(self):
        """Test that GitHubAPI initializes correctly"""
        api = GitHubAPI()
        assert api.base_url == "https://api.github.com"
    
    def test_get_user_repos_with_valid_user(self):
        """Test fetching repos for a valid user"""
        api = GitHubAPI()
        repos = api.get_user_repos("torvalds")  # Linus Torvalds - very public
        assert isinstance(repos, list)
        assert len(repos) > 0
    
    def test_get_user_repos_with_invalid_user(self):
        """Test fetching repos for non-existent user"""
        api = GitHubAPI()
        repos = api.get_user_repos("invalid_user_xyz_12345")
        assert isinstance(repos, list)
        # May be empty or error depending on API response
