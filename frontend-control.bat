@echo off
cd /d "D:\stocktrading\0908.claude-init\stock-trading-ui"

if "%1"=="start" (
    echo 🚀 Frontend 서버 시작...
    npm run dev
) else if "%1"=="stop" (
    echo ⏹️ Frontend 서버 중지...
    taskkill /F /IM node.exe
) else if "%1"=="restart" (
    echo 🔄 Frontend 서버 재시작...
    taskkill /F /IM node.exe
    timeout /t 2 /nobreak >nul
    npm run dev
) else (
    echo 사용법:
    echo frontend-control.bat start   - 서버 시작
    echo frontend-control.bat stop    - 서버 중지  
    echo frontend-control.bat restart - 서버 재시작
)