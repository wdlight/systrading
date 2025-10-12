# 프로젝트 구조 분리 및 스크립트 수정 내역

## 📅 날짜: 2025-09-20

## 📋 개요
기존에 통합되어 있던 backend와 frontend 프로젝트를 분리하여 독립적으로 실행할 수 있도록 구조를 개선하고, 관련 스크립트들을 수정했습니다.

## 🔧 주요 수정 사항

### 1. Backend 서버 스크립트 개선

#### 1.1 Backend 시작 스크립트 (`backend/scripts/start_backend.sh`)
- **위치**: `/home/wide/projects/systrading/backend/scripts/start_backend.sh`
- **개선사항**:
  - 어디서든 실행 가능하도록 경로 자동 감지 기능 추가
  - 반드시 backend 폴더에서 실행되도록 보장
  - 강화된 경로 검증 로직 추가
  - 실행 위치 저장 및 복원 기능

```bash
# 주요 기능
- 실행 위치 자동 감지
- backend 폴더로 자동 이동
- vkis 가상환경 활성화
- simple_server.py 실행
```

#### 1.2 Backend 중지 스크립트 (`backend/scripts/stop_backend.sh`)
- **위치**: `/home/wide/projects/systrading/backend/scripts/stop_backend.sh`
- **기능**:
  - 포트 8000 사용 프로세스 자동 감지 및 종료
  - simple_server.py 실행 프로세스 감지 및 종료
  - uvicorn 프로세스 감지 및 종료
  - 우아한 종료 (SIGTERM) 후 강제 종료 (SIGKILL)
  - 최종 상태 확인 및 보고

#### 1.3 Windows 배치 파일 (`backend/scripts/start_backend.bat`, `stop_backend.bat`)
- Linux 스크립트와 동일한 기능을 Windows 환경에서 제공
- Windows 명령어를 사용한 프로세스 관리

### 2. Frontend 서버 스크립트 개선

#### 2.1 Frontend 시작 스크립트 (`stock-trading-ui/scripts/start-server.sh`)
- **위치**: `/home/wide/projects/systrading/stock-trading-ui/scripts/start-server.sh`
- **주요 문제 해결**:
  - CRLF 줄바꿈 문자 문제 해결 (Windows → Unix)
  - Unicode BOM 제거
  - WSL 환경에서 Windows CMD 실행 문제 해결
  - Next.js 직접 실행으로 경로 문제 해결

#### 2.2 WSL 환경 대응
```bash
# WSL 환경 감지
if [[ "$WSL_DISTRO_NAME" != "" ]] || [[ -n "$WSLENV" ]] || [[ -n "$WSL_INTEROP" ]]; then
    # Node.js 직접 실행
    exec "$node_path" "$next_js_path" dev --port $port --turbopack --hostname 0.0.0.0
fi
```

#### 2.3 Next.js 설정 수정 (`stock-trading-ui/next.config.ts`)
```typescript
// 수정 전
const nextConfig: NextConfig = {
  server: {
    port: 3000 
  }
};

// 수정 후
const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname  // WSL 환경에서 올바른 루트 디렉토리 설정
  }
};
```

#### 2.4 Package.json 스크립트 개선
```json
{
  "scripts": {
    "dev": "next dev --turbopack --port 3000",
    "dev:custom": "next dev --turbopack"
  }
}
```

## 📁 새로운 프로젝트 구조

```
systrading/
├── backend/
│   ├── vkis/                    # 가상환경
│   ├── simple_server.py         # FastAPI 서버
│   └── scripts/
│       ├── start_backend.sh     # Linux/macOS 시작 스크립트
│       ├── start_backend.bat    # Windows 시작 스크립트
│       ├── stop_backend.sh      # Linux/macOS 중지 스크립트
│       ├── stop_backend.bat     # Windows 중지 스크립트
│       └── BACKEND_START_GUIDE.md
└── stock-trading-ui/
    ├── src/
    │   ├── app/                 # Next.js App Router
    │   ├── components/
    │   ├── hooks/
    │   └── lib/
    ├── node_modules/
    ├── package.json
    ├── next.config.ts
    └── scripts/
        └── start-server.sh      # Frontend 시작 스크립트
```

## 🚀 사용 방법

### Backend 서버 관리
```bash
# 서버 시작 (어디서든 실행 가능)
./backend/scripts/start_backend.sh

# 서버 중지
./backend/scripts/stop_backend.sh

# Windows
backend\scripts\start_backend.bat
backend\scripts\stop_backend.bat
```

### Frontend 서버 관리
```bash
# 서버 시작 (어디서든 실행 가능)
./stock-trading-ui/scripts/start-server.sh

# 특정 포트로 시작
./stock-trading-ui/scripts/start-server.sh 3001
```

## 🔍 해결된 문제들

### 1. Backend 관련
- ✅ 스크립트 실행 위치 문제 해결
- ✅ 가상환경 경로 문제 해결
- ✅ 프로세스 중지 기능 추가
- ✅ Windows 호환성 추가

### 2. Frontend 관련
- ✅ WSL 환경에서 Windows CMD 실행 문제 해결
- ✅ CRLF 줄바꿈 문자 문제 해결
- ✅ Next.js 경로 문제 해결
- ✅ Turbopack 루트 디렉토리 설정 문제 해결

## 📊 테스트 결과

### Backend 서버
- ✅ 정상 시작: `Ready in 1106ms`
- ✅ 포트 8000에서 실행
- ✅ 가상환경 정상 활성화
- ✅ API 엔드포인트 정상 응답

### Frontend 서버
- ✅ 정상 시작: `Ready in 1106ms`
- ✅ 포트 3001에서 실행
- ✅ WSL 환경에서 정상 실행
- ✅ 경고 메시지 제거

## 🎯 개선 효과

1. **독립성**: Frontend와 Backend가 독립적으로 실행 가능
2. **안정성**: WSL 환경에서 안정적인 실행
3. **편의성**: 어디서든 스크립트 실행 가능
4. **관리성**: 프로세스 시작/중지 기능 제공
5. **호환성**: Linux, macOS, Windows 모두 지원

## 📝 참고사항

- Backend는 `backend/vkis` 가상환경을 사용
- Frontend는 Node.js 직접 실행으로 WSL 호환성 확보
- 모든 스크립트는 실행 위치 자동 감지 기능 포함
- 프로세스 관리 기능으로 안전한 서버 제어 가능

## 🔄 향후 개선 계획

1. Docker 컨테이너화 검토
2. 환경 변수 관리 개선
3. 로그 관리 시스템 구축
4. 자동 재시작 기능 추가
5. 헬스체크 기능 강화


