from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import pandas as pd
import os

# Import the in-memory data store instead of database
from . import data_store
from .rearrangement import find_rearrangement, execute_rearrangement

# Initialize the data store with sample data if not already initialized
# This is handled automatically in data_store.py

# Global variables
CURRENT_DATE = datetime(2025, 4, 5)

app = FastAPI(title="Space Station Cargo Management System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes from physical folders
from .api import import_containers, import_items, placement, containers, place, simulate, waste, logs, search, items, export, retrieve

# Include routers with the /api prefix
app.include_router(import_containers.router, prefix="/api")
app.include_router(import_items.router, prefix="/api")
app.include_router(placement.router, prefix="/api")
app.include_router(containers.router, prefix="/api")
app.include_router(place.router, prefix="/api")
app.include_router(simulate.router, prefix="/api")
app.include_router(waste.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(retrieve.router, prefix="/api")

# All API endpoints have been moved to separate physical files in the api folder

# 2. Item Search and Retrieval API has been moved to a separate physical file

# Test endpoint for API connectivity
@app.get("/api/test/")
def test_api():
    return {
        "success": True,
        "message": "API connection successful",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the backend directory
backend_dir = os.path.dirname(current_dir)
# Go up one more level to the project root
project_root = os.path.dirname(backend_dir)
# Path to the static files
static_path = os.path.join(project_root, "frontend", "static")

# Check if the directory exists and use it, otherwise fall back to a relative path
if os.path.exists(static_path):
    print(f"Using static files from: {static_path}")
    static_dir = static_path
else:
    # Fall back to relative path for Docker environment
    static_dir = "frontend/static"
    print(f"Static path not found at {static_path}, falling back to {static_dir}")

# Mount static files at the end to avoid conflicts with API routes
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
