"""
Main entry point for the Open Source Contribution Tracker.

Initializes the Flask app and registers all blueprints/routes.
Run with: PYTHONPATH=. python3 src/main.py
"""

import os
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from src.api.routes import api
from src.api.webhook import webhook

# Load environment variables from .env if present
load_dotenv()


# Point Flask to the project root's static/ folder
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

# Register blueprints
app.register_blueprint(api)
app.register_blueprint(webhook)


@app.route("/")
def home():
    """Serve the frontend index page."""
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    print("Starting Open Source Contribution Tracker...")
    print("Running at http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)

