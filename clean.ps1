# Windows cleanup script for Nifty 100 project
# Usage: .\clean.ps1

$ErrorActionPreference = "SilentlyContinue"

Write-Host "Cleaning Nifty 100 project..." -ForegroundColor Yellow

# Remove database file
if (Test-Path "data\nifty100.db") {
    Remove-Item "data\nifty100.db" -Force
    Write-Host "Removed database file" -ForegroundColor Green
}

# Remove output directory
if (Test-Path "output") {
    Remove-Item "output" -Recurse -Force
    Write-Host "Removed output directory" -ForegroundColor Green
}

Write-Host "Cleanup complete!" -ForegroundColor Green
