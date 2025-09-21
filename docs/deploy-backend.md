# Backend Server Manual Control Guide

## 📋 Overview

이 문서는 주식 매매 시스템의 백엔드 서버를 수동으로 제어하는 방법을 설명합니다.

## 🚀 서버 시작하기

### 1. 기본 서버 시작
```bash
# 백엔드 디렉토리로 이동
cd "D:\stocktrading\0908.claude-init\backend"

# 서버 시작
python simple_server.py
```

### 2. 백그라운드에서 시작 (Windows)
```bash
# PowerShell 사용
cd "D:\stocktrading\0908.claude-init\backend"
Start-Process python -ArgumentList "simple_server.py" -WindowStyle Hidden

# 또는 nohup 스타일 (Git Bash)
cd "D:\stocktrading\0908.claude-init\backend"
python simple_server.py &
```

### 3. 개발 모드 (자동 재시작)
```bash
# uvicorn 직접 사용
cd "D:\stocktrading\0908.claude-init\backend"
uvicorn simple_server:app --host 0.0.0.0 --port 8000 --reload
```

## 🛑 서버 중지하기

### 1. 프로세스 확인
```bash
# 실행 중인 Python 프로세스 확인
tasklist | findstr python

# 포트 8000을 사용하는 프로세스 확인
netstat -ano | findstr :8000
```

### 2. 프로세스 종료
```bash
# 특정 PID로 종료
taskkill /F /PID [process_id]

# Python 프로세스 모두 종료 (주의: 모든 Python 프로그램이 종료됨)
taskkill /F /IM python.exe

# 포트 8000 사용 프로세스 종료
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a
```

### 3. 안전한 종료
서버가 터미널에서 실행 중인 경우:
- `Ctrl + C` 로 안전하게 종료

## 🔍 서버 상태 확인

### 1. 서버 실행 상태 확인
```bash
# 포트 8000 리스닝 확인
netstat -ano | findstr :8000

# API 응답 확인
curl http://localhost:8000/api/watchlist

# 헬스체크 (브라우저에서)
http://localhost:8000/
```

### 2. 로그 확인
```bash
# 서버 실행 시 콘솔에서 로그 확인
# 주요 로그 패턴:
# - "Uvicorn running on http://0.0.0.0:8000" : 서버 시작됨
# - "WebSocket 연결: 127.0.0.1" : WebSocket 클라이언트 연결
# - "WebSocket 데이터 전송 성공" : 실시간 데이터 전송 중
# - "INFO:     127.0.0.1:xxxxx - "GET /api/watchlist HTTP/1.1" 200 OK" : API 호출 성공
```

## 🔧 트러블슈팅

### 1. 포트 충돌 문제
**증상**: `Address already in use` 오류
```bash
# 해결방법 1: 기존 프로세스 종료
netstat -ano | findstr :8000
taskkill /F /PID [process_id]

# 해결방법 2: 다른 포트 사용
python simple_server.py --port 8001
```

### 2. WebSocket 연결 실패
**증상**: 프론트엔드에서 WebSocket 연결 오류
```bash
# 1. 서버 재시작
taskkill /F /IM python.exe
cd "D:\stocktrading\0908.claude-init\backend"
python simple_server.py

# 2. 방화벽 확인
# Windows 방화벽에서 Python.exe 허용 확인

# 3. CORS 설정 확인
# simple_server.py에서 CORS 설정 확인
```

### 3. API 응답 없음
**증상**: API 호출 시 타임아웃 또는 연결 실패
```bash
# 1. 서버 프로세스 확인
tasklist | findstr python

# 2. 포트 확인
netstat -ano | findstr :8000

# 3. 서버 재시작
cd "D:\stocktrading\0908.claude-init\backend"
python simple_server.py
```

### 4. 한국투자증권 API 토큰 만료
**증상**: API 에러 로그에 토큰 관련 오류
```bash
# 토큰 파일 삭제 후 재시작 (자동 재발급)
rm -f tokens.json
python simple_server.py
```

## 📊 서버 모니터링

### 1. 실시간 로그 모니터링
```bash
# PowerShell에서 실시간 로그 확인
Get-Content .\server.log -Wait -Tail 10

# Git Bash에서
tail -f server.log
```

### 2. 리소스 사용량 확인
```bash
# CPU/메모리 사용량 확인
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE

# 자세한 정보
wmic process where "name='python.exe'" get ProcessId,PageFileUsage,WorkingSetSize
```

### 3. 연결 상태 확인
```bash
# WebSocket 연결 수 확인 (로그에서)
# "활성 연결 수: X" 메시지 확인

# API 응답 시간 측정
curl -w "Response time: %{time_total}s\n" http://localhost:8000/api/watchlist
```

## 🔄 자동화 스크립트

### 1. 서버 시작 스크립트 (start-backend.bat)
```batch
@echo off
cd /d "D:\stocktrading\0908.claude-init\backend"
echo Starting backend server...
python simple_server.py
pause
```

### 2. 서버 재시작 스크립트 (restart-backend.bat)
```batch
@echo off
echo Stopping existing backend servers...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting backend server...
cd /d "D:\stocktrading\0908.claude-init\backend"
python simple_server.py
```

### 3. 서버 상태 확인 스크립트 (check-backend.bat)
```batch
@echo off
echo Checking backend server status...
netstat -ano | findstr :8000
if %errorlevel% == 0 (
    echo Backend server is running on port 8000
) else (
    echo Backend server is not running
)
curl -s http://localhost:8000/api/watchlist >nul
if %errorlevel% == 0 (
    echo API endpoints are responding
) else (
    echo API endpoints are not responding
)
pause
```

## 📝 환경 설정

### 1. 필수 패키지 확인
```bash
# 필수 패키지 설치 확인
pip install fastapi uvicorn websockets python-multipart

# 요구사항 파일에서 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# .env 파일 확인 (있는 경우)
# API 키, 데이터베이스 연결 정보 등

# 환경 변수 직접 설정 (필요한 경우)
set API_KEY=your_api_key
set DATABASE_URL=your_database_url
```

### 3. 포트 설정 변경
`simple_server.py` 파일에서:
```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # 포트 변경 가능
```

## 🚨 주의사항

1. **서버 종료 시**: `Ctrl + C`로 안전하게 종료하는 것을 권장
2. **포트 충돌**: 8000번 포트가 이미 사용 중인 경우 다른 포트 사용
3. **방화벽**: Windows 방화벽에서 Python 프로그램 허용 필요
4. **API 키**: 한국투자증권 API 키가 올바르게 설정되어 있어야 함
5. **권한**: 관리자 권한이 필요할 수 있음 (포트 바인딩 시)

## 📞 지원

문제가 발생하는 경우:
1. 로그 확인
2. 프로세스 상태 확인  
3. 네트워크 연결 확인
4. 서버 재시작 시도

---

**마지막 업데이트**: 2025-09-11  
**버전**: 1.0