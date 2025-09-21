@echo off
echo ========================================
echo   Backend Server Restart Script
echo ========================================
echo.

echo [1/3] Stopping existing backend servers...
taskkill /F /IM python.exe 2>nul
if %errorlevel% == 0 (
    echo    ✓ Existing Python processes terminated
) else (
    echo    ℹ No existing Python processes found
)

echo [2/3] Waiting for cleanup...
timeout /t 3 /nobreak >nul

echo [3/3] Starting backend server...
cd /d "D:\stocktrading\0908.claude-init\backend"
echo    ✓ Changed to backend directory
echo    ✓ Starting server on http://localhost:8000
echo.
echo Server is starting... Press Ctrl+C to stop
echo ========================================
python simple_server.py