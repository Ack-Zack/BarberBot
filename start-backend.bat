@echo off
cd /d "%~dp0backend"
if not exist "..\.venv\Scripts\python.exe" (
    echo [!] Virtual env not found. Run: python -m venv .venv ^&^& .venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000