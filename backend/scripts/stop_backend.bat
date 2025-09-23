@echo off
REM Stock Trading Backend Server Stop Script (Windows)
REM This script stops the running FastAPI backend server
REM 
REM 사용법: 어디서든 실행 가능하지만, backend 서버를 찾아서 중지시킵니다.

echo 🛑 Stopping Stock Trading Backend Server...
echo ============================================

REM 실행 위치 저장
set "ORIGINAL_DIR=%CD%"
echo 📁 Original execution directory: %ORIGINAL_DIR%

REM 스크립트 파일의 절대 경로 찾기
set "SCRIPT_DIR=%~dp0"
echo 📁 Script location: %SCRIPT_DIR%

REM Backend 디렉토리 찾기 (스크립트의 상위 폴더)
for %%i in ("%SCRIPT_DIR%") do set "BACKEND_DIR=%%~dpi"
echo 📁 Backend directory: %BACKEND_DIR%

REM Backend 구조 검증
if not exist "%BACKEND_DIR%vkis" (
    echo ❌ Error: 'vkis' virtual environment not found in backend directory
    echo 💡 Expected structure: backend\vkis\
    echo 📁 Backend directory: %BACKEND_DIR%
    pause
    exit /b 1
)

echo.
echo 🔍 Searching for running backend server processes...

REM 방법 1: 포트 8000을 사용하는 프로세스 찾기
echo 📡 Checking processes using port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    set "PORT_PID=%%a"
)

if defined PORT_PID (
    echo ✅ Found process using port 8000: %PORT_PID%
    
    REM 프로세스 정보 표시
    for /f "tokens=1,2,5" %%a in ('tasklist /FI "PID eq %PORT_PID%" /FO CSV /NH') do (
        echo   📋 Process %PORT_PID%: %%c
    )
    
    echo.
    echo 🛑 Stopping process using port 8000...
    echo   🔄 Terminating process %PORT_PID%...
    taskkill /PID %PORT_PID% /T /F >nul 2>&1
    
    REM 최종 확인
    timeout /t 2 /nobreak >nul
    tasklist /FI "PID eq %PORT_PID%" /FO CSV | findstr "%PORT_PID%" >nul
    if errorlevel 1 (
        echo ✅ Successfully stopped process %PORT_PID%
    ) else (
        echo ⚠️  Process %PORT_PID% may still be running
    )
    
    set "PORT_PID="
) else (
    echo ℹ️  No processes found using port 8000
)

echo.
echo 🔍 Searching for Python processes running simple_server.py...

REM 방법 2: simple_server.py를 실행하는 Python 프로세스 찾기
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH ^| findstr simple_server') do (
    set "PYTHON_PID=%%a"
    set "PYTHON_PID=!PYTHON_PID:"=!"
)

if defined PYTHON_PID (
    echo ✅ Found Python process running simple_server.py: %PYTHON_PID%
    
    REM 프로세스 정보 표시
    for /f "tokens=1,2,5" %%a in ('tasklist /FI "PID eq %PYTHON_PID%" /FO CSV /NH') do (
        echo   📋 Process %PYTHON_PID%: %%c
    )
    
    echo.
    echo 🛑 Stopping Python process running simple_server.py...
    echo   🔄 Terminating process %PYTHON_PID%...
    taskkill /PID %PYTHON_PID% /T /F >nul 2>&1
    
    REM 최종 확인
    timeout /t 2 /nobreak >nul
    tasklist /FI "PID eq %PYTHON_PID%" /FO CSV | findstr "%PYTHON_PID%" >nul
    if errorlevel 1 (
        echo ✅ Successfully stopped Python process %PYTHON_PID%
    ) else (
        echo ⚠️  Python process %PYTHON_PID% may still be running
    )
    
    set "PYTHON_PID="
) else (
    echo ℹ️  No Python processes found running simple_server.py
)

echo.
echo 🔍 Searching for uvicorn processes...

REM 방법 3: uvicorn 프로세스 찾기 (FastAPI 서버)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH ^| findstr uvicorn') do (
    set "UVICORN_PID=%%a"
    set "UVICORN_PID=!UVICORN_PID:"=!"
)

if defined UVICORN_PID (
    echo ✅ Found uvicorn process: %UVICORN_PID%
    
    REM 프로세스 정보 표시
    for /f "tokens=1,2,5" %%a in ('tasklist /FI "PID eq %UVICORN_PID%" /FO CSV /NH') do (
        echo   📋 Process %UVICORN_PID%: %%c
    )
    
    echo.
    echo 🛑 Stopping uvicorn process...
    echo   🔄 Terminating process %UVICORN_PID%...
    taskkill /PID %UVICORN_PID% /T /F >nul 2>&1
    
    REM 최종 확인
    timeout /t 2 /nobreak >nul
    tasklist /FI "PID eq %UVICORN_PID%" /FO CSV | findstr "%UVICORN_PID%" >nul
    if errorlevel 1 (
        echo ✅ Successfully stopped uvicorn process %UVICORN_PID%
    ) else (
        echo ⚠️  uvicorn process %UVICORN_PID% may still be running
    )
    
    set "UVICORN_PID="
) else (
    echo ℹ️  No uvicorn processes found
)

echo.
echo 📊 Final Status Check:
echo =====================

REM 최종 상태 확인
set "FINAL_PORT_PID="
set "FINAL_PYTHON_PID="
set "FINAL_UVICORN_PID="

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    set "FINAL_PORT_PID=%%a"
)

for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH ^| findstr simple_server') do (
    set "FINAL_PYTHON_PID=%%a"
    set "FINAL_PYTHON_PID=!FINAL_PYTHON_PID:"=!"
)

for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH ^| findstr uvicorn') do (
    set "FINAL_UVICORN_PID=%%a"
    set "FINAL_UVICORN_PID=!FINAL_UVICORN_PID:"=!"
)

if not defined FINAL_PORT_PID if not defined FINAL_PYTHON_PID if not defined FINAL_UVICORN_PID (
    echo ✅ All backend server processes have been successfully stopped!
    echo 🌐 Port 8000 is now available
    echo.
    echo 💡 To start the server again, run:
    echo    backend\scripts\start_backend.bat
) else (
    echo ⚠️  Some processes may still be running:
    if defined FINAL_PORT_PID echo    - Port 8000: %FINAL_PORT_PID%
    if defined FINAL_PYTHON_PID echo    - Python simple_server.py: %FINAL_PYTHON_PID%
    if defined FINAL_UVICORN_PID echo    - uvicorn: %FINAL_UVICORN_PID%
    echo.
    echo 💡 If processes are still running, you may need to manually kill them:
    echo    taskkill /PID ^<process_id^> /F
)

echo.
echo ============================================
echo 🏁 Backend server stop script completed
pause


