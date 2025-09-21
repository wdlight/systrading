@echo off
cd /d "D:\stocktrading\0908.claude-init\backend"
echo Starting backend server...
echo.
echo Server will start on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python simple_server.py
pause