# PowerShell script to start Agentic Orchestra frontend
# Run from project root: .\start-frontend.ps1

Write-Host "🎨 Starting Agentic Orchestra Frontend..." -ForegroundColor Cyan
Write-Host ""

# Check if in project root
if (-not (Test-Path "CLAUDE.md") -or -not (Test-Path "requirements.txt")) {
    Write-Host "❌ ERROR: Not in project root!" -ForegroundColor Red
    Write-Host "   Please navigate to agentic-orchestra/ first" -ForegroundColor Yellow
    Write-Host "   Example: cd C:\Users\luca.la-malfa\PycharmProjects\agentic-orchestra" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ In project root: $(Get-Location)" -ForegroundColor Green

# Check if node_modules exists
if (-not (Test-Path "orchestrator-ui\frontend\node_modules")) {
    Write-Host "⚠️  node_modules not found, installing dependencies..." -ForegroundColor Yellow
    Set-Location -Path "orchestrator-ui\frontend"
    npm install
    Set-Location -Path "..\..\"
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
}

# Navigate to frontend directory
Set-Location -Path "orchestrator-ui\frontend"
Write-Host "✓ Changed to frontend directory" -ForegroundColor Green
Write-Host ""

# Start frontend
Write-Host "Starting Vite dev server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

npm run dev
