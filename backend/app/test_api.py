from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict, Any
from datetime import datetime

# Create FastAPI app
app = FastAPI(title="Space Station Cargo Management Test API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        with open("backend/app/static/index.html") as f:
            return f.read()
    except FileNotFoundError:
        return {"message": "Space Station Cargo Management System Test API"}

# Test endpoint for API connectivity
@app.get("/api/test", response_model=Dict[str, Any])
def test_api():
    """
    Simple test endpoint to verify API connectivity.
    """
    return {
        "success": True,
        "message": "API connection successful",
        "timestamp": datetime.now().isoformat()
    }

# Simulation status endpoint
@app.get("/api/simulation/status", response_model=Dict[str, Any])
def get_simulation_status():
    """
    Get current mission date and simulation statistics.
    """
    try:
        current_date = datetime.now()
        return {
            "success": True,
            "missionDate": current_date.isoformat(),
            "daysSinceStart": (current_date - datetime(2025, 1, 1)).days,
            "message": "Simulation status retrieved successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get simulation status: {str(e)}"
        }

# Current date endpoint
@app.get("/api/simulate/day", response_model=Dict[str, Any])
def get_current_date():
    """
    Get the current simulation date.
    """
    return {"success": True, "currentDate": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
