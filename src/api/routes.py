"""
Flask Routes

Defines all HTTP API endpoints for the Open Source Contribution Tracker.
All routes return JSON responses.
"""

from flask import Blueprint, jsonify

# Create a blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    Used to verify the server is running correctly.

    Returns:
        JSON: {"status": "ok", "message": "Server is running"}
    """
    return jsonify({"status": "ok", "message": "Server is running"}), 200


@api.route('/user/<username>', methods=['GET'])
def get_user(username):
    """
    Get contribution data for a GitHub user.

    Args:
        username (str): GitHub username from URL path

    Returns:
        JSON: User contribution data (placeholder for Week 2)
    """
    # TODO (Week 2): Implement real GitHub API call here
    return jsonify({
        "username": username,
        "message": "User endpoint coming in Week 2",
        "status": "not_implemented"
    }), 200


@api.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    Get the contribution leaderboard.

    Returns:
        JSON: Ranked list of contributors (placeholder for Week 3)
    """
    # TODO (Week 3): Implement real leaderboard from database
    return jsonify({
        "leaderboard": [],
        "message": "Leaderboard coming in Week 3",
        "status": "not_implemented"
    }), 200
