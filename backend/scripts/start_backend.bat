@echo off
REM Stock Trading Backend Server Start Script (Windows)
REM This script activates the virtual environment and starts the FastAPI backend server
REM 
REM 사용법: 어디서든 실행 가능하지만, 반드시 backend 폴더에서 실행됩니다.
REM 예: backend\scripts\start_backend.bat 또는 cd backend\scripts && start_backend.bat

echo 🚀 Starting Stock Trading Backend Server...
echo ============================================

REM 실행 위치 저장 (나중에 복원용)
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
    echo 💡 Please ensure this script is in the correct location: backend\scripts\
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%simple_server.py" (
    echo ❌ Error: 'simple_server.py' not found in backend directory
    echo 💡 Expected file: backend\simple_server.py
    echo 📁 Backend directory: %BACKEND_DIR%
    pause
    exit /b 1
)

REM Backend 디렉토리로 이동 (반드시 여기서 실행)
echo 📁 Navigating to backend directory for execution...
cd /d "%BACKEND_DIR%" || (
    echo ❌ Error: Failed to navigate to backend directory
    pause
    exit /b 1
)
echo 📁 Now executing from: %CD%

REM Check if virtual environment exists
set "VENV_DIR=.\vkis"
echo 🐍 Virtual environment directory: %VENV_DIR%

if not exist "%VENV_DIR%" (
    echo ❌ Error: Virtual environment not found at %VENV_DIR%
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

if errorlevel 1 (
    echo ❌ Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated successfully
python --version
where python

REM Check if simple_server.py exists
set "SERVER_FILE=.\simple_server.py"
echo 📄 Server file: %SERVER_FILE%

if not exist "%SERVER_FILE%" (
    echo ❌ Error: simple_server.py not found at %SERVER_FILE%
    pause
    exit /b 1
)

REM Check if required packages are installed
echo 📦 Checking required packages...
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo ⚠️  Warning: Some required packages may not be installed
    echo 💡 You may need to run: pip install -r requirements.txt
)

REM Start the server
echo.
echo 🌟 Starting FastAPI server...
echo 🌐 Server will be available at: http://localhost:8000
echo 📊 API documentation at: http://localhost:8000/docs
echo 🔗 Health check at: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo ============================================

REM Run the server
python "%SERVER_FILE%"

pause
