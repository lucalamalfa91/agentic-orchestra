# PowerShell script to start Agentic Orchestra backend
# Run from project root: .\start-backend.ps1

Write-Host "🚀 Starting Agentic Orchestra Backend..." -ForegroundColor Cyan
Write-Host ""

# Check if in project root
if (-not (Test-Path "CLAUDE.md") -or -not (Test-Path "requirements.txt")) {
    Write-Host "❌ ERROR: Not in project root!" -ForegroundColor Red
    Write-Host "   Please navigate to agentic-orchestra/ first" -ForegroundColor Yellow
    Write-Host "   Example: cd C:\Users\luca.la-malfa\PycharmProjects\agentic-orchestra" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ In project root: $(Get-Location)" -ForegroundColor Green

# Set PYTHONPATH to project root
$env:PYTHONPATH = (Get-Location).Path
Write-Host "✓ PYTHONPATH set to: $env:PYTHONPATH" -ForegroundColor Green

# Navigate to backend directory
Set-Location -Path "orchestrator-ui\backend"
Write-Host "✓ Changed to backend directory" -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python main.py
