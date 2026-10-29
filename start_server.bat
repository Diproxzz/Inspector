@echo off
echo ========================================================
echo Starting Antigravity QC Inspection Server...
echo Web UI will be accessible at: http://localhost:8000
echo ========================================================
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
