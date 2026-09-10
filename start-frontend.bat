@echo off
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [i] Installing frontend dependencies...
    call npm install
)
call npm run dev