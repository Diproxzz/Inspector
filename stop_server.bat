@echo off
echo ========================================================
echo Stopping Antigravity QC Inspection Server on port 8000...
echo ========================================================
powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
echo Server stopped successfully.
pause
