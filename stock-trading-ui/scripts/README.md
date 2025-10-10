# Frontend Server Scripts

Next.js 프론트엔드 서버를 관리하기 위한 스크립트 모음입니다.

## 📁 스크립트 목록

### 🚀 `start-server.sh` - 서버 시작
Next.js 개발 서버를 시작합니다.

#### 사용법
```bash
# 기본 포트 9000으로 시작
./scripts/start-server.sh

# 특정 포트로 시작
./scripts/start-server.sh 9001

# 도움말 확인
./scripts/start-server.sh --help
```

#### 주요 기능
- ✅ 자동 위치 감지 (어디서 실행해도 정상 동작)
- ✅ 포트 충돌 자동 감지 및 해결
- ✅ 의존성 자동 확인 및 설치
- ✅ 기존 프로세스 자동 종료 옵션

---

### 🛑 `stop-server.sh` - 서버 종료
실행 중인 프론트엔드 서버를 종료합니다.

#### 사용법
```bash
# 기본 포트 9000 종료
./scripts/stop-server.sh

# 특정 포트 종료
./scripts/stop-server.sh 9001

# 모든 Next.js 프로세스 종료
./scripts/stop-server.sh --all

# 개발 포트 스캔
./scripts/stop-server.sh --scan

# 강제 종료 (확인 없이)
./scripts/stop-server.sh --force 9000

# 도움말 확인
./scripts/stop-server.sh --help
```

#### 주요 기능
- ✅ 안전한 프로세스 종료 (SIGTERM → SIGKILL)
- ✅ 프로세스 정보 표시
- ✅ 사용자 확인 프롬프트
- ✅ 포트 스캔 기능
- ✅ 강제 종료 옵션

---

## 🗂️ 실행 위치

이 스크립트들은 다음 위치에서 실행할 수 있습니다:

### 1️⃣ 프로젝트 루트에서
```bash
./stock-trading-ui/scripts/start-server.sh
./stock-trading-ui/scripts/stop-server.sh
```

### 2️⃣ stock-trading-ui 디렉토리에서
```bash
./scripts/start-server.sh
./scripts/stop-server.sh
```

### 3️⃣ scripts 디렉토리에서
```bash
./start-server.sh
./stop-server.sh
```

---

## ⚙️ 시스템 요구사항

- **Node.js** 18.0.0 이상
- **npm** 8.0.0 이상
- **Linux/macOS/WSL** 환경

---

## 🔧 고급 사용법

### 포트 충돌 해결
서버 시작 시 포트가 이미 사용 중인 경우:
```bash
# 자동으로 기존 프로세스 종료 여부를 묻습니다
./scripts/start-server.sh

# 또는 미리 포트를 정리합니다
./scripts/stop-server.sh 9000
./scripts/start-server.sh 9000
```

### 개발 포트 관리
여러 개발 서버가 실행 중일 때:
```bash
# 포트 9000-9010 스캔
./scripts/stop-server.sh --scan

# 모든 Next.js 프로세스 종료
./scripts/stop-server.sh --all
```

### 자동화 스크립트
```bash
#!/bin/bash
# 개발 환경 초기화
./scripts/stop-server.sh --all
./scripts/start-server.sh 9000
```

---

## 🐛 문제 해결

### 포트를 찾을 수 없는 경우
```bash
# 수동으로 프로세스 확인
lsof -i :9000
netstat -tulnp | grep :9000

# 강제 종료
./scripts/stop-server.sh --force 9000
```

### 권한 문제
```bash
# 실행 권한 부여
chmod +x ./scripts/*.sh
```

### Node.js 관련 오류
```bash
# Node.js 버전 확인
node --version
npm --version

# 의존성 재설치
rm -rf node_modules package-lock.json
npm install
```

---

## 📝 로그 예시

### 서버 시작 성공
```
==========================================
  Next.js Frontend 서버 시작 스크립트
==========================================
[INFO] stock-trading-ui 폴더에서 실행됨
[SUCCESS] Frontend 디렉토리 확인: /home/user/projects/systrading/stock-trading-ui
[SUCCESS] Node.js: v18.17.0
[SUCCESS] npm: 9.6.7
[SUCCESS] 의존성이 이미 설치되어 있습니다.
[INFO] Next.js Frontend 서버를 포트 9000에서 시작합니다...
[INFO] 서버 시작 중...
[INFO] 브라우저에서 http://localhost:9000 에 접속하세요
```

### 포트 충돌 해결
```
[WARNING] 포트 9000가 이미 사용 중입니다.
기존 프로세스를 종료하고 새로 시작하시겠습니까? (y/N): y
[WARNING] 포트 9000에서 실행 중인 프로세스를 종료합니다...
[SUCCESS] 포트 9000의 프로세스들을 종료했습니다.
```

---

**개발 팀을 위한 간편한 개발 서버 관리 도구입니다! 🚀**
