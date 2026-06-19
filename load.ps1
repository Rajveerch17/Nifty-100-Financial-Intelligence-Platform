# Windows load script for Nifty 100 project
# Usage: .\load.ps1

Write-Host "Loading data into Nifty 100 database..." -ForegroundColor Yellow
python -m src.etl.loader
Write-Host "Load complete!" -ForegroundColor Green
