# Run the Space Station Cargo Management System
Write-Host "Starting Space Station Cargo Management System..." -ForegroundColor Green

# Check if Python is installed
if (Get-Command python -ErrorAction SilentlyContinue) {
    # Install requirements if needed
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    
    # Run the application
    Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
    python -m backend.app.main
} else {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8 or higher." -ForegroundColor Red
}
