# 배포 및 운영 가이드

**프로젝트**: 주식 자동매매 시스템
**최종 업데이트**: 2025-10-08
**대상 독자**: DevOps, 운영자

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [환경 설정](#환경-설정)
3. [Backend 배포](#backend-배포)
4. [Frontend 배포](#frontend-배포)
5. [모니터링](#모니터링)
6. [트러블슈팅](#트러블슈팅)
7. [백업 및 복구](#백업-및-복구)

---

## 사전 요구사항

### 시스템 요구사항
| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| CPU | 2 Core | 4 Core |
| RAM | 4GB | 8GB |
| Disk | 20GB | 50GB SSD |
| Network | 10Mbps | 100Mbps |

### 소프트웨어 요구사항
- **Python**: 3.12+
- **Node.js**: 18.x LTS
- **npm**: 9.x+
- **Git**: 2.x+

---

## 환경 설정

### 1. 한국투자증권 API 준비

#### 1-1. 계좌 개설 및 API 신청
1. 한국투자증권 홈페이지 방문
2. 계좌 개설 (모의투자 또는 실계좌)
3. **KIS Developers** 포털 접속
   - URL: https://apiportal.koreainvestment.com
4. API 신청
   - 모의투자용: **모의투자 AppKey/AppSecret**
   - 실전용: **실전투자 AppKey/AppSecret**

#### 1-2. API 권한 확인
필요한 API 권한:
- ✅ 주식 현재가 조회
- ✅ 주식 호가 조회
- ✅ 주식 차트 (일봉/분봉)
- ✅ 계좌 잔고 조회
- ✅ 주식 주문 (매수/매도)
- ✅ 해외 지수 조회 (NASDAQ, S&P 500)
- ✅ 환율 조회 (USD/KRW)
- ✅ WebSocket 실시간 시세

#### 1-3. 환경 변수 준비
```bash
# KIS API 인증 정보
KOREA_INVESTMENT_APP_KEY=발급받은_AppKey
KOREA_INVESTMENT_APP_SECRET=발급받은_AppSecret
KOREA_INVESTMENT_ACCOUNT_NUMBER=계좌번호_8자리
KOREA_INVESTMENT_ACCOUNT_CODE=계좌코드_2자리

# 환경 설정
ENVIRONMENT=production  # 또는 development
KIS_BASE_URL=https://openapi.koreainvestment.com:9443  # 실전
# KIS_BASE_URL=https://openapivts.koreainvestment.com:29443  # 모의투자
```

---

### 2. Backend 환경 설정

#### 2-1. Python 가상환경 생성
```bash
cd backend

# 가상환경 생성
python3.12 -m venv vkis

# 가상환경 활성화
source vkis/bin/activate  # Linux/Mac
# 또는
.\vkis\Scripts\activate  # Windows
```

#### 2-2. 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**주요 의존성**:
```txt
fastapi==0.115.0
uvicorn[standard]==0.35.0
websockets==14.0
httpx==0.28.1
pandas==2.2.3
pydantic==2.10.0
python-dotenv==1.0.1
pykrx==1.0.46
```

#### 2-3. 환경 변수 파일 생성
```bash
# backend/.env 파일 생성
cat > .env << EOF
# KIS API
KOREA_INVESTMENT_APP_KEY=your_app_key_here
KOREA_INVESTMENT_APP_SECRET=your_app_secret_here
KOREA_INVESTMENT_ACCOUNT_NUMBER=12345678
KOREA_INVESTMENT_ACCOUNT_CODE=01

# 환경
ENVIRONMENT=production
KIS_BASE_URL=https://openapi.koreainvestment.com:9443

# 서버 설정
HOST=0.0.0.0
PORT=8000
WORKERS=4

# CORS
ALLOWED_ORIGINS=http://localhost:9000,https://your-domain.com
EOF
```

#### 2-4. 디렉토리 생성
```bash
# 캐시 디렉토리
mkdir -p kordata

# 로그 디렉토리
mkdir -p logs
```

---

### 3. Frontend 환경 설정

#### 3-1. 의존성 설치
```bash
cd stock-trading-ui
npm install
```

**주요 의존성**:
```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "18.3.0",
    "react-dom": "18.3.0",
    "typescript": "5.6.0",
    "tailwindcss": "3.4.0",
    "lightweight-charts": "4.2.0",
    "socket.io-client": "4.8.1"
  }
}
```

#### 3-2. 환경 변수 설정
```bash
# stock-trading-ui/.env.local 생성
cat > .env.local << EOF
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# 배포 환경
NODE_ENV=production
EOF
```

---

## Backend 배포

### 1. 개발 모드 실행

#### 1-1. FastAPI 개발 서버
```bash
cd backend
source vkis/bin/activate

# 기본 실행
python -m app.main

# 또는 uvicorn 직접 실행 (auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**접속 확인**:
- API: http://localhost:8000
- Health Check: http://localhost:8000/health
- API 문서: http://localhost:8000/docs

#### 1-2. 스크립트로 실행
```bash
# scripts/start_backend.sh
chmod +x scripts/start_backend.sh
./scripts/start_backend.sh
```

---

### 2. 프로덕션 모드 실행

#### 2-1. Uvicorn 프로덕션 설정
```bash
# 단일 워커
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --access-log

# 또는 Gunicorn + Uvicorn Workers (권장)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info
```

#### 2-2. Systemd 서비스 등록

**파일**: `/etc/systemd/system/stock-trading-backend.service`

```ini
[Unit]
Description=Stock Trading Backend API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/systrading/backend
Environment="PATH=/opt/systrading/backend/vkis/bin"
ExecStart=/opt/systrading/backend/vkis/bin/uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 관리**:
```bash
# 서비스 활성화
sudo systemctl enable stock-trading-backend

# 서비스 시작
sudo systemctl start stock-trading-backend

# 서비스 상태 확인
sudo systemctl status stock-trading-backend

# 로그 확인
sudo journalctl -u stock-trading-backend -f

# 서비스 재시작
sudo systemctl restart stock-trading-backend

# 서비스 중지
sudo systemctl stop stock-trading-backend
```

---

## Frontend 배포

### 1. 개발 모드 실행

```bash
cd stock-trading-ui

# 개발 서버 시작
npm run dev

# 접속: http://localhost:9000
```

---

### 2. 프로덕션 빌드

#### 2-1. 빌드 실행
```bash
npm run build

# 빌드 결과: .next/ 디렉토리
```

#### 2-2. 프로덕션 서버 실행
```bash
npm run start

# 또는 PM2로 실행 (권장)
npm install -g pm2
pm2 start npm --name "stock-trading-ui" -- start
pm2 save
pm2 startup
```

#### 2-3. Systemd 서비스 등록

**파일**: `/etc/systemd/system/stock-trading-frontend.service`

```ini
[Unit]
Description=Stock Trading Frontend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/systrading/stock-trading-ui
Environment="NODE_ENV=production"
Environment="PORT=9000"
ExecStart=/usr/bin/npm start

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

### 3. Nginx 리버스 프록시 (선택)

#### 3-1. Nginx 설치
```bash
sudo apt update
sudo apt install nginx
```

#### 3-2. Nginx 설정

**파일**: `/etc/nginx/sites-available/stock-trading`

```nginx
# Backend API
upstream backend {
    server 127.0.0.1:8000;
}

# Frontend
upstream frontend {
    server 127.0.0.1:9000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

**활성화**:
```bash
sudo ln -s /etc/nginx/sites-available/stock-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 모니터링

### 1. 로그 모니터링

#### Backend 로그
```bash
# 실시간 로그 확인
tail -f logs/backend.log

# 에러 로그만 확인
tail -f logs/backend.log | grep ERROR

# 특정 종목 로그 확인
tail -f logs/backend.log | grep "005930"
```

#### Frontend 로그
```bash
# PM2 로그
pm2 logs stock-trading-ui

# Systemd 로그
sudo journalctl -u stock-trading-frontend -f
```

---

### 2. 헬스 체크

#### Backend Health Check
```bash
# 기본 헬스 체크
curl http://localhost:8000/health

# 응답 예시
{
  "status": "healthy",
  "timestamp": "2025-10-08T10:00:00Z",
  "uptime": 3600,
  "version": "0.9.0"
}
```

#### KIS API 연결 확인
```bash
# CLI 스크립트로 확인
python scripts/check_overseas_indices.py --target nasdaq
python scripts/check_overseas_indices.py --target sp500
python scripts/check_overseas_indices.py --target usdkrw
```

---

### 3. 성능 모니터링

#### CPU & 메모리
```bash
# 전체 시스템
htop

# 특정 프로세스
ps aux | grep uvicorn
ps aux | grep node
```

#### 네트워크
```bash
# 포트 확인
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 9000

# 연결 상태
ss -s
```

#### 디스크 사용량
```bash
# 캐시 디렉토리 크기
du -sh backend/kordata

# 로그 디렉토리 크기
du -sh backend/logs
```

---

## 트러블슈팅

### 1. Backend 이슈

#### 문제: 포트 8000 이미 사용 중
```bash
# 프로세스 확인
sudo lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 또는
sudo pkill -f uvicorn
```

#### 문제: KIS API 토큰 만료
```bash
# 로그 확인
grep "token expired" logs/backend.log

# 해결: 자동 재발급 확인
grep "token_manager" logs/backend.log

# 수동 재시작
sudo systemctl restart stock-trading-backend
```

#### 문제: WebSocket 연결 실패
```bash
# WebSocket 로그 확인
grep "websocket" logs/backend.log

# KIS WebSocket 상태 확인
grep "H0STISE0" logs/backend.log

# 재연결 확인
grep "reconnect" logs/backend.log
```

#### 문제: 캐시 데이터 손상
```bash
# 캐시 초기화
rm -rf backend/kordata/*

# 서비스 재시작
sudo systemctl restart stock-trading-backend
```

---

### 2. Frontend 이슈

#### 문제: npm run build 실패
```bash
# node_modules 재설치
rm -rf node_modules package-lock.json
npm install

# 다시 빌드
npm run build
```

#### 문제: API 연결 실패 (404)
```bash
# .env.local 확인
cat .env.local

# Backend URL 확인
curl http://localhost:8000/health

# CORS 설정 확인 (Backend .env)
grep ALLOWED_ORIGINS backend/.env
```

#### 문제: WebSocket 연결 안 됨
```bash
# 브라우저 콘솔 확인
# WebSocket connection to 'ws://localhost:8000/ws' failed

# Backend WebSocket 엔드포인트 확인
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8000/ws
```

---

### 3. 데이터 이슈

#### 문제: KOSDAQ 지수 0 표시
```bash
# 후보 코드 테스트
cd backend
./vkis/bin/python tests/test_kosdaq_index_service.py -v

# 원본 응답 확인
grep "KOSDAQ" logs/backend.log | tail -20
```

#### 문제: 해외 지수 0 표시
```bash
# CLI로 직접 확인
python scripts/check_overseas_indices.py --target nasdaq
python scripts/check_overseas_indices.py --target sp500

# API 권한 확인 (KIS Developers 포털)
# - 해외 지수 조회 권한 있는지 확인
```

#### 문제: 차트 데이터 로딩 느림
```bash
# 캐시 상태 확인
ls -lh backend/kordata/005930/daily/
ls -lh backend/kordata/005930/minute/

# 캐시 재생성
rm -rf backend/kordata/005930/daily/*
# 다시 요청하면 자동 생성됨
```

---

## 백업 및 복구

### 1. 백업

#### 1-1. 환경 설정 백업
```bash
# 백업 디렉토리 생성
mkdir -p backups/$(date +%Y%m%d)

# .env 파일 백업
cp backend/.env backups/$(date +%Y%m%d)/backend.env
cp stock-trading-ui/.env.local backups/$(date +%Y%m%d)/frontend.env.local
```

#### 1-2. 캐시 데이터 백업
```bash
# 전체 캐시 백업 (tar.gz)
tar -czf backups/$(date +%Y%m%d)/kordata.tar.gz backend/kordata/

# 특정 종목만 백업
tar -czf backups/$(date +%Y%m%d)/005930.tar.gz backend/kordata/005930/
```

#### 1-3. 로그 백업
```bash
# 로그 백업 (최근 7일)
find backend/logs -name "*.log" -mtime -7 -exec cp {} backups/$(date +%Y%m%d)/ \;
```

#### 1-4. 자동 백업 스크립트
```bash
#!/bin/bash
# backups/daily_backup.sh

BACKUP_DIR="/opt/backups/systrading/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 환경 설정
cp /opt/systrading/backend/.env $BACKUP_DIR/backend.env

# 캐시 데이터 (압축)
tar -czf $BACKUP_DIR/kordata.tar.gz /opt/systrading/backend/kordata/

# 로그 (최근 7일)
find /opt/systrading/backend/logs -name "*.log" -mtime -7 -exec cp {} $BACKUP_DIR/ \;

# 7일 이상 된 백업 삭제
find /opt/backups/systrading -type d -mtime +7 -exec rm -rf {} \;
```

**Cron 등록**:
```bash
# 매일 새벽 3시 백업
0 3 * * * /opt/backups/daily_backup.sh >> /var/log/backup.log 2>&1
```

---

### 2. 복구

#### 2-1. 환경 설정 복구
```bash
# 백업에서 복구
cp backups/20251008/backend.env backend/.env
cp backups/20251008/frontend.env.local stock-trading-ui/.env.local

# 서비스 재시작
sudo systemctl restart stock-trading-backend
sudo systemctl restart stock-trading-frontend
```

#### 2-2. 캐시 데이터 복구
```bash
# 기존 캐시 제거
rm -rf backend/kordata/*

# 백업에서 복구
tar -xzf backups/20251008/kordata.tar.gz -C backend/

# 서비스 재시작 (선택)
sudo systemctl restart stock-trading-backend
```

---

## 보안 권장사항

### 1. 방화벽 설정
```bash
# UFW 활성화
sudo ufw enable

# SSH 허용 (22번 포트)
sudo ufw allow 22/tcp

# HTTP/HTTPS 허용 (Nginx 사용 시)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Backend/Frontend 포트는 localhost만 허용 (Nginx 사용 시)
sudo ufw deny 8000/tcp
sudo ufw deny 9000/tcp

# 상태 확인
sudo ufw status
```

### 2. SSL/TLS 인증서 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 확인
sudo certbot renew --dry-run
```

### 3. 환경 변수 암호화
```bash
# .env 파일 권한 제한
chmod 600 backend/.env
chmod 600 stock-trading-ui/.env.local

# 소유자 확인
chown www-data:www-data backend/.env
```

---

## 체크리스트

### 배포 전 체크리스트
- [ ] KIS API AppKey/AppSecret 발급 완료
- [ ] 계좌 번호 확인 및 권한 설정
- [ ] `.env` 파일 생성 및 확인
- [ ] Python 가상환경 생성 및 의존성 설치
- [ ] Node.js 의존성 설치 완료
- [ ] Backend Health Check 성공
- [ ] Frontend 빌드 성공
- [ ] 캐시 디렉토리 생성
- [ ] 로그 디렉토리 생성
- [ ] 방화벽 규칙 설정

### 배포 후 체크리스트
- [ ] Backend API 정상 응답 확인
- [ ] Frontend 페이지 로딩 확인
- [ ] WebSocket 연결 확인
- [ ] KOSPI/KOSDAQ 지수 표시 확인
- [ ] 해외 지수/환율 표시 확인
- [ ] 차트 데이터 로딩 확인
- [ ] 로그 파일 생성 및 기록 확인
- [ ] 캐시 파일 생성 확인
- [ ] Systemd 서비스 자동 시작 확인
- [ ] 백업 스크립트 동작 확인

---

**문서 버전**: 1.0
**작성일**: 2025-10-08
**담당자**: DevOps Team
