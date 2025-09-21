@echo off
echo ========================================
echo   Backend Server Status Check
echo ========================================
echo.

echo [1/4] Checking Python processes...
tasklist | findstr python >nul
if %errorlevel% == 0 (
    echo    ✓ Python processes are running:
    tasklist | findstr python
) else (
    echo    ✗ No Python processes found
)
echo.

echo [2/4] Checking port 8000...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo    ✓ Port 8000 is in use:
    netstat -ano | findstr :8000
) else (
    echo    ✗ Port 8000 is not in use
)
echo.

echo [3/4] Testing API endpoints...
curl -s http://localhost:8000/api/watchlist >nul 2>&1
if %errorlevel% == 0 (
    echo    ✓ API endpoints are responding
    echo    ✓ Watchlist endpoint: http://localhost:8000/api/watchlist
) else (
    echo    ✗ API endpoints are not responding
    echo    ✗ Server may not be running or may have issues
)
echo.

echo [4/4] WebSocket test...
echo    ℹ WebSocket URL: ws://localhost:8000/ws
echo    ℹ Check browser console for WebSocket connection status
echo.

echo ========================================
echo Status check complete!
echo.
echo Quick commands:
echo   Start server: start-backend.bat
echo   Restart server: restart-backend.bat
echo ========================================
pause