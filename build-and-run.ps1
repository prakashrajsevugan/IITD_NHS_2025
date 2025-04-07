# PowerShell script to build and run the Space Station Cargo Management System Docker container

Write-Host "Space Station Cargo Management System - Docker Build & Run Script" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not in PATH. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is installed
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose is installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed or not in PATH. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Building and starting the Docker containers..." -ForegroundColor Yellow

# Build and start the container
try {
    docker-compose up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker containers built and started successfully!" -ForegroundColor Green
        
        # Get container status
        $containerStatus = docker-compose ps
        Write-Host ""
        Write-Host "Container Status:" -ForegroundColor Cyan
        Write-Host $containerStatus
        
        # Get the IP address
        Write-Host ""
        Write-Host "🚀 You can access the application at:" -ForegroundColor Green
        Write-Host "  - Frontend: http://localhost" -ForegroundColor Green
        Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Green
        Write-Host ""
        Write-Host "Useful commands:" -ForegroundColor Yellow
        Write-Host "  - View logs: docker-compose logs -f" -ForegroundColor White
        Write-Host "  - View frontend logs: docker-compose logs -f frontend" -ForegroundColor White
        Write-Host "  - View backend logs: docker-compose logs -f backend" -ForegroundColor White
        Write-Host "  - Stop containers: docker-compose down" -ForegroundColor White
        Write-Host "  - Restart containers: docker-compose restart" -ForegroundColor White
    } else {
        Write-Host "❌ Failed to build and start the Docker containers." -ForegroundColor Red
    }
} catch {
    Write-Host "❌ An error occurred: $_" -ForegroundColor Red
}
