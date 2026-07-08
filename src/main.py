"""
Main entry point for the Open Source Contribution Tracker.

Initializes the Flask app and registers all blueprints/routes.
Run with: python3 src/main.py
"""

from flask import Flask
from src.api.routes import api

app = Flask(__name__)

# Register blueprints
app.register_blueprint(api)


@app.route('/')
def home():
    """Home page — serves the frontend."""
    return "Open Source Contribution Tracker — Week 1 Skeleton Running ✅"


if __name__ == '__main__':
    print("🚀 Starting Open Source Contribution Tracker...")
    print("📍 Running at http://localhost:5000")
    app.run(debug=True, port=5000)
