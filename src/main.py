"""
Main entry point for the Open Source Contribution Tracker
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    """Home page"""
    return "Open Source Contribution Tracker - Coming Soon!"

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "Server is running"}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
