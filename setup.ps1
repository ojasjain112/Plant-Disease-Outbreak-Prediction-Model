# Quick Start Script for Weather-Driven Disease Outbreak Predictor
# Run this script to set up and start the application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Weather-Driven Disease Outbreak Predictor" -ForegroundColor Cyan
Write-Host "Quick Start Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "1. Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "   $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "2. Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "   Virtual environment created!" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "2. Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "3. Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "   Virtual environment activated!" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "4. Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "   Dependencies installed!" -ForegroundColor Green

# Create necessary directories
Write-Host ""
Write-Host "5. Creating project directories..." -ForegroundColor Yellow
$directories = @("models", "data", "cache")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "   Created $dir/" -ForegroundColor Green
    }
    else {
        Write-Host "   $dir/ already exists" -ForegroundColor Green
    }
}

# Generate sample data
Write-Host ""
Write-Host "6. Generating sample outbreak data..." -ForegroundColor Yellow
python scripts\data_ingest.py --samples 1000
Write-Host "   Sample data generated!" -ForegroundColor Green

# Train models
Write-Host ""
Write-Host "7. Training ML models..." -ForegroundColor Yellow
python scripts\train_models.py
Write-Host "   Models trained!" -ForegroundColor Green

# Setup complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor Yellow
Write-Host "   python app.py" -ForegroundColor White
Write-Host ""
Write-Host "Then open your browser to:" -ForegroundColor Yellow
Write-Host "   http://localhost:5000" -ForegroundColor White
Write-Host ""

# Ask if user wants to start the app now
$response = Read-Host "Would you like to start the application now? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Starting application..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    python app.py
}
else {
    Write-Host ""
    Write-Host "You can start the application later with: python app.py" -ForegroundColor Yellow
}
