"""
Main entry point for the Open Source Contribution Tracker (FastAPI).

Initializes the FastAPI app and registers all routers.
Run with: PYTHONPATH=. python3 src/main.py
"""

import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routes import router as api_router
from src.api.webhook import router as webhook_router

# Load environment variables from .env if present
load_dotenv()

# Point to the project root's static/ folder
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

app = FastAPI(title="CuSOC Tracker API")

# Register routers
app.include_router(api_router, prefix="/api")
app.include_router(webhook_router, prefix="/webhook")

# Mount static files
app.mount("/css", StaticFiles(directory=os.path.join(STATIC_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")
app.mount("/pages", StaticFiles(directory=os.path.join(STATIC_DIR, "pages")), name="pages")
app.mount("/components", StaticFiles(directory=os.path.join(STATIC_DIR, "components")), name="components")

@app.get("/")
async def home():
    """Serve the frontend index page."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    print("Starting Open Source Contribution Tracker (FastAPI)...")
    print("Running at http://127.0.0.1:5000")
    uvicorn.run("src.main:app", host="127.0.0.1", port=5000, reload=True)
