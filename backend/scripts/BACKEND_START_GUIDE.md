# Backend Server 시작 가이드

## 📋 개요
이 가이드는 Stock Trading Backend 서버를 시작하는 방법을 설명합니다.

## 🚀 서버 시작/중지 방법

### Linux/macOS (WSL 포함)

**서버 시작:**
```bash
# 프로젝트 루트 디렉토리에서 실행
./backend/scripts/start_backend.sh

# 또는 backend/scripts 폴더로 이동 후 실행
cd backend/scripts
./start_backend.sh
```

**서버 중지:**
```bash
# 프로젝트 루트 디렉토리에서 실행
./backend/scripts/stop_backend.sh

# 또는 backend/scripts 폴더로 이동 후 실행
cd backend/scripts
./stop_backend.sh
```

### Windows

**서버 시작:**
```cmd
# 프로젝트 루트 디렉토리에서 실행
backend\scripts\start_backend.bat

# 또는 backend/scripts 폴더로 이동 후 실행
cd backend\scripts
start_backend.bat
```

**서버 중지:**
```cmd
# 프로젝트 루트 디렉토리에서 실행
backend\scripts\stop_backend.bat

# 또는 backend/scripts 폴더로 이동 후 실행
cd backend\scripts
stop_backend.bat
```

## 📁 디렉토리 구조
```
systrading/
└── backend/
    ├── vkis/              # 가상환경 (venv)
    │   ├── bin/           # Linux/macOS용 activate 스크립트
    │   └── Scripts/       # Windows용 activate 스크립트
    ├── simple_server.py   # FastAPI 서버 파일
    └── scripts/
        ├── start_backend.sh       # Linux/macOS 시작 스크립트
        ├── start_backend.bat      # Windows 시작 스크립트
        ├── stop_backend.sh        # Linux/macOS 중지 스크립트
        ├── stop_backend.bat       # Windows 중지 스크립트
        └── BACKEND_START_GUIDE.md # 이 가이드 파일
```

## ⚠️ 주의사항
- 스크립트는 **어디서든 실행 가능**합니다 (프로젝트 루트, backend 폴더, 또는 backend/scripts 폴더에서)
- 스크립트가 자동으로 backend 구조를 찾아서 **반드시 backend 폴더에서 실행**됩니다
- 백엔드 서버는 `backend/vkis` 가상환경을 사용합니다
- 실행 위치와 관계없이 항상 backend 폴더에서 서버가 시작됩니다

## 🌐 서버 접속 정보
서버가 시작되면 다음 주소로 접속할 수 있습니다:

- **메인 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **헬스체크**: http://localhost:8000/health
- **Hello 엔드포인트**: http://localhost:8000/hello

## 🔧 문제 해결

### 가상환경 활성화 실패
```bash
# 가상환경이 제대로 생성되었는지 확인
ls -la backend/vkis/bin/activate  # Linux/macOS
ls -la backend\vkis\Scripts\activate.bat  # Windows
```

### 패키지 설치 오류
```bash
# 가상환경 활성화 후 패키지 설치
cd backend
source vkis/bin/activate  # Linux/macOS
# 또는
vkis\Scripts\activate.bat  # Windows

pip install -r requirements.txt
```

### 포트 충돌
- 8000번 포트가 사용 중인 경우, `simple_server.py`에서 포트 번호를 변경할 수 있습니다.

## 📞 지원
문제가 발생하면 로그 메시지를 확인하고, 필요시 개발자에게 문의하세요.
