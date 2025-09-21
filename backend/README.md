# Stock Trading Backend API

RSI/MACD 기반 주식 자동매매 시스템의 FastAPI 백엔드 서버입니다.

## 🚀 주요 기능

- **계좌 관리**: 계좌 잔고, 보유 종목 조회
- **자동매매**: RSI/MACD 조건 기반 자동매매 시스템
- **워치리스트**: 실시간 종목 모니터링 및 기술적 지표 계산
- **실시간 통신**: WebSocket을 통한 실시간 데이터 스트리밍
- **RESTful API**: 완전한 REST API 지원

## 📋 요구사항

- Python 3.11+
- 한국투자증권 API 계정
- Redis (선택사항, 캐싱용)

## 🛠️ 설치 및 실행

### 1. 가상환경 설정
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 한국투자증권 API 키 등을 설정
```

### 4. 개발 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Docker 실행 (선택사항)
```bash
# 백엔드만 실행
docker-compose up backend

# 전체 스택 실행 (프론트엔드 포함)
docker-compose --profile full-stack up
```

## 📡 API 엔드포인트

### 계좌 관리
- `GET /api/account/balance` - 계좌 잔고 조회
- `GET /api/account/summary` - 계좌 요약 정보
- `GET /api/account/positions` - 보유 종목 목록
- `POST /api/account/refresh` - 계좌 정보 갱신

### 매매 관리
- `GET /api/trading/conditions` - 매매 조건 조회
- `POST /api/trading/conditions` - 매매 조건 설정
- `POST /api/trading/start` - 자동매매 시작
- `POST /api/trading/stop` - 자동매매 중지
- `GET /api/trading/status` - 매매 상태 조회
- `POST /api/trading/orders/buy` - 매수 주문
- `POST /api/trading/orders/sell` - 매도 주문

### 워치리스트
- `GET /api/watchlist` - 워치리스트 조회
- `POST /api/watchlist/add/{stock_code}` - 종목 추가
- `DELETE /api/watchlist/{stock_code}` - 종목 제거
- `GET /api/watchlist/{stock_code}/indicators` - 기술적 지표 조회

### WebSocket
- `ws://localhost:8000/ws` - 실시간 데이터 스트림

## 🔧 설정

### 기존 config.yaml 호환
기존의 `config.yaml` 파일을 그대로 사용할 수 있습니다. 시스템이 자동으로 설정을 로드합니다.

### 환경변수 우선순위
1. 환경변수 (.env 파일)
2. config.yaml 파일
3. 기본값

## 📊 실시간 데이터 구조

### WebSocket 메시지 타입

#### 계좌 업데이트
```json
{
  "type": "account_update",
  "timestamp": "2024-01-01T12:00:00",
  "data": {
    "total_value": 1000000,
    "positions": [...]
  }
}
```

#### 워치리스트 업데이트
```json
{
  "type": "watchlist_update", 
  "timestamp": "2024-01-01T12:00:00",
  "data": [
    {
      "stock_code": "005930",
      "current_price": 70000,
      "profit_rate": 5.2,
      "rsi": 65.5,
      "macd": 1250.3
    }
  ]
}
```

## 🏗️ 아키텍처

```
backend/
├── app/
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── api/                 # REST API 라우터
│   │   ├── account.py       # 계좌 관련 API
│   │   ├── trading.py       # 매매 관련 API
│   │   └── watchlist.py     # 워치리스트 API
│   ├── models/              # Pydantic 모델
│   │   └── schemas.py       # 데이터 스키마 정의
│   ├── services/            # 비즈니스 로직
│   │   ├── account_service.py
│   │   ├── trading_service.py
│   │   ├── watchlist_service.py
│   │   └── realtime_service.py
│   ├── websocket/           # WebSocket 관리
│   │   └── connection.py    # 연결 관리자
│   └── core/                # 핵심 구성요소
│       ├── config.py        # 설정 관리
│       ├── dependencies.py  # 의존성 주입
│       └── korea_invest.py  # 한국투자증권 API 래퍼
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🔍 기존 시스템과의 호환성

### PyQt5 애플리케이션과의 연동
- 기존 `utils.py`의 `KoreaInvestAPI` 클래스를 그대로 활용
- 동일한 `config.yaml` 설정 파일 사용
- 같은 pandas DataFrame 구조 유지 (`realtime_watchlist_df`, `account_info_df`)

### 데이터 마이그레이션
기존 PyQt5 애플리케이션의 데이터를 그대로 사용할 수 있습니다:
- 매매 조건 설정
- 워치리스트 종목
- 계좌 정보

## 🚨 중요한 수정사항

### 수익률 0.0% 문제 해결
기존 PyQt5 버전에서 발생하던 수익률 계산 문제를 해결했습니다:

**문제**: 매수 시 평균단가가 `None`으로 초기화되어 수익률 계산 불가
**해결**: 워치리스트 추가 시 평균단가를 현재가로 초기화 (`watchlist_service.py:152`)

```python
# 기존 (문제)
'평균단가': None,

# 수정 (해결)  
'평균단가': current_price,
```

## 🧪 테스트

### API 테스트
```bash
# 서버 실행 후
curl http://localhost:8000/health

# Swagger UI 접속
# http://localhost:8000/docs
```

### WebSocket 테스트
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

## 📝 개발 가이드

### 새로운 API 엔드포인트 추가
1. `app/api/` 디렉토리에 라우터 파일 생성
2. `app/models/schemas.py`에 Pydantic 모델 정의
3. `app/services/`에 비즈니스 로직 구현
4. `app/main.py`에 라우터 등록

### 실시간 데이터 추가
1. `app/services/realtime_service.py`에 새로운 루프 함수 추가
2. `app/websocket/connection.py`에서 메시지 타입 정의
3. 클라이언트에서 WebSocket 메시지 처리

## 🔒 보안 고려사항

- API 키는 환경변수로 관리
- CORS 설정으로 허용된 도메인만 접근 가능
- WebSocket 연결 수 제한
- 민감한 정보 로깅 금지

## 📞 지원

- 이슈: GitHub Issues
- 문서: `/docs` 엔드포인트 (Swagger UI)
- 로그: `trading_api.log` 파일 확인