"""
GitHub API Integration Module

This module handles all interactions with the GitHub REST API v3
"""

import requests
import os

class GitHubAPI:
    """Wrapper around GitHub API"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}' if self.token else '',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_user_repos(self, username):
        """
        Fetch all repositories for a given user
        
        Args:
            username (str): GitHub username
            
        Returns:
            list: List of repositories
        """
        try:
            url = f"{self.base_url}/users/{username}/repos"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repos: {e}")
            return []
    
    def get_user_contributions(self, username):
        """
        Fetch user's contributions (commits, PRs, issues)
        
        Args:
            username (str): GitHub username
            
        Returns:
            dict: Contribution statistics
        """
        try:
            # This is a placeholder - actual implementation will be more complex
            repos = self.get_user_repos(username)
            return {
                "username": username,
                "total_repos": len(repos),
                "repositories": repos
            }
        except Exception as e:
            print(f"Error fetching contributions: {e}")
            return None
