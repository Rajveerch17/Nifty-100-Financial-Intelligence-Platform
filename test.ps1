# Windows test script for Nifty 100 project
# Usage: .\test.ps1

Write-Host "Running Nifty 100 tests..." -ForegroundColor Yellow
python -m pytest tests/ -v
