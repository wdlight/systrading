# Backend - FastAPI 주식 매매 시스템

## 📁 프로젝트 개요
- **프레임워크**: FastAPI
- **언어**: Python 3.12
- **아키텍처**: Clean Architecture + Service Layer

---

## 🏗️ 핵심 구조

```
backend/
├── app/
│   ├── main.py            # FastAPI 애플리케이션 진입점
│   ├── api/               # API 라우터
│   ├── core/              # 설정 및 의존성
│   ├── models/            # 데이터 모델
│   ├── services/          # 비즈니스 로직
│   └── websocket/         # WebSocket 핸들러
├── tests/                 # 테스트
└── vkis/                  # Python 가상환경
```

---

## 🤖 Gemini Code Agent 활용 (Backend)

### 우선 사용 Agent

#### **Backend 아키텍처**
```bash
# API 설계 및 구조
Task: backend-architect
"새로운 portfolio API 엔드포인트 설계하고 RESTful 패턴으로 구현"

# Python 최적화
Task: python-pro
"비동기 처리를 활용한 FastAPI 성능 최적화"
```

#### **Trading 시스템 전문**
```bash
# 자동매매 엔진
Task: trading-engine-specialist
"RSI/MACD 기반 매매 신호 생성 및 주문 실행 로직 구현"

# 데이터 분석
Task: quantitative-analyst
"백테스팅 시스템 구축 및 매매 전략 성과 분석"

# 시장 데이터
Task: market-data-engineer
"한국투자증권 API 실시간 데이터 수집 및 WebSocket 스트리밍"

# 리스크 관리
Task: risk-manager
"포지션 사이징 및 손실 제한 로직 구현"

# 성과 모니터링
Task: performance-monitor
"매매 결과 분석 및 실시간 모니터링 대시보드"
```

#### **한국투자증권 API 전문**
```bash
# API 연동 및 디버깅
Task: korean-stock-api-debugger
"토큰 만료, 데이터 파싱 오류, 주문 실패 등 API 관련 문제 해결"
```

#### **인프라 및 데이터**
```bash
# 데이터베이스 관리
Task: database-admin
"거래 데이터 백업, 성능 최적화, 인덱스 관리"

# 에러 디버깅
Task: debugger
"WebSocket 연결 문제, 비동기 처리 오류 해결"
```

### Backend 작업별 Agent 매핑

| 작업 유형 | 추천 Agent | 예시 |
|----------|------------|------|
| API 엔드포인트 | `backend-architect` | REST API 설계 |
| 매매 로직 | `trading-engine-specialist` | 자동매매 알고리즘 |
| 데이터 분석 | `quantitative-analyst` | RSI/MACD 최적화 |
| 한투 API 연동 | `korean-stock-api-debugger` | 토큰/주문 오류 |
| 실시간 데이터 | `market-data-engineer` | WebSocket 스트리밍 |
| 리스크 관리 | `risk-manager` | 손익 제한 로직 |
| 성과 분석 | `performance-monitor` | 매매 결과 리포트 |
| DB 운영 | `database-admin` | 데이터 관리 |
| Python 최적화 | `python-pro` | 비동기 성능 개선 |

---

## 🔧 개발 명령어

### ⚠️ 필수: vkis 가상환경 사용
**Backend 실행 시 반드시 vkis 가상환경을 활성화해야 합니다!**

```bash
# 1. Backend 디렉토리로 이동
cd backend

# 2. vkis 가상환경 활성화 (필수!)
source vkis/bin/activate  # Linux/Mac/WSL
# 또는
vkis\Scripts\activate     # Windows

# 3. 가상환경 활성화 확인
which python              # vkis/bin/python 경로 표시되어야 함
python --version          # Python 3.12.x 확인

# 4. 서버 실행
python app/main.py        # 개발 서버 (포트 8000)
python simple_server.py  # 간단한 테스트 서버

# 5. 테스트 실행
pytest tests/

# 6. 개발 완료 후 가상환경 비활성화
deactivate
```

### 🚨 가상환경 사용 이유
- **의존성 격리**: 프로젝트별 패키지 버전 관리
- **Python 3.12**: 특정 Python 버전 사용
- **패키지 충돌 방지**: 시스템 Python과 분리
- **일관된 개발환경**: 모든 개발자가 동일한 환경 사용

---

## 📡 API 구조

### 핵심 엔드포인트
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="주식 매매 시스템 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 주요 라우터
app.include_router(account_router, prefix="/api/account")
app.include_router(trading_router, prefix="/api/trading")
app.include_router(watchlist_router, prefix="/api/watchlist")
```

### 데이터 모델
```python
# app/models/schemas.py
from pydantic import BaseModel
from typing import Optional

class WatchlistItem(BaseModel):
    종목코드: str
    종목명: str
    현재가: int
    수익률: float
    평균단가: Optional[int]
    보유수량: int
    MACD: float
    RSI: float

class AccountInfo(BaseModel):
    종목코드: str
    종목명: str
    보유수량: int
    매입단가: int
    수익률: float
    현재가: int
```

---

## 🏛️ 서비스 레이어

### 계좌 서비스
```python
# app/services/account_service.py
class AccountService:
    def __init__(self, korea_invest_client):
        self.client = korea_invest_client

    async def get_balance(self) -> List[AccountInfo]:
        """계좌 잔고 조회"""
        response = await self.client.get_account_balance()
        return [AccountInfo(**item) for item in response['data']]

    async def get_stock_price(self, stock_code: str) -> int:
        """주식 현재가 조회"""
        response = await self.client.get_current_price(stock_code)
        return response['현재가']
```

### 매매 서비스
```python
# app/services/trading_service.py
class TradingService:
    def __init__(self, korea_invest_client):
        self.client = korea_invest_client

    async def buy_stock(self, stock_code: str, quantity: int, price: int):
        """주식 매수"""
        order_data = {
            "stock_code": stock_code,
            "quantity": quantity,
            "price": price,
            "order_type": "buy"
        }
        return await self.client.place_order(order_data)

    async def sell_stock(self, stock_code: str, quantity: int, price: int):
        """주식 매도"""
        order_data = {
            "stock_code": stock_code,
            "quantity": quantity,
            "price": price,
            "order_type": "sell"
        }
        return await self.client.place_order(order_data)
```

---

## 🔌 WebSocket 실시간 통신

### WebSocket 핸들러
```python
# app/websocket/realtime.py
from fastapi import WebSocket

class RealTimeManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_price_update(self, data: dict):
        """실시간 가격 업데이트 브로드캐스트"""
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                await self.disconnect(connection)

# WebSocket 엔드포인트
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 클라이언트 요청 처리
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
```

---

## 🔗 외부 API 연동

### 한국투자증권 API
```python
# app/core/korea_invest.py
import httpx
from typing import Dict, Any

class KoreaInvestClient:
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None

    async def get_access_token(self) -> str:
        """액세스 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.api_key,
            "appsecret": self.secret_key
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.json()["access_token"]

    async def get_current_price(self, stock_code: str) -> Dict[str, Any]:
        """주식 현재가 조회"""
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.api_key,
            "appsecret": self.secret_key,
            "tr_id": "FHKST01010100"
        }
        params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": stock_code}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
                headers=headers,
                params=params
            )
            return response.json()
```

---

## ⚡ FastAPI Best Practices

### 1. **의존성 주입**
```python
# app/core/dependencies.py
from fastapi import Depends

async def get_korea_invest_client() -> KoreaInvestClient:
    return KoreaInvestClient(
        api_key=settings.KOREA_INVEST_API_KEY,
        secret_key=settings.KOREA_INVEST_SECRET_KEY
    )

# 라우터에서 사용
@router.get("/balance")
async def get_balance(
    client: KoreaInvestClient = Depends(get_korea_invest_client)
):
    service = AccountService(client)
    return await service.get_balance()
```

### 2. **에러 핸들링**
```python
# app/core/exceptions.py
from fastapi import HTTPException

class TradingException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class APIException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=502, detail=f"API 오류: {detail}")

# 사용 예시
async def place_order(order_data: dict):
    try:
        result = await client.place_order(order_data)
        return result
    except Exception as e:
        raise TradingException(f"주문 실패: {str(e)}")
```

### 3. **설정 관리**
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    KOREA_INVEST_API_KEY: str
    KOREA_INVEST_SECRET_KEY: str
    DATABASE_URL: str = "sqlite:///./trading.db"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🚫 Over-Engineering 방지

### ❌ 피해야 할 것들
1. **과도한 추상화**: 간단한 CRUD는 복잡하게 만들지 말 것
2. **불필요한 ORM**: 단순한 데이터는 dict 사용
3. **복잡한 미들웨어**: 정말 필요할 때만 추가
4. **과도한 검증**: 기본적인 Pydantic 검증으로 충분
5. **조기 캐싱**: 성능 문제가 실제로 발생할 때 적용

### ✅ 권장 사항
1. **단순함 우선**: 가장 직접적인 구현부터 시작
2. **FastAPI 기본 기능 활용**: 자동 문서화, 검증 등
3. **점진적 개선**: 기능이 동작한 후 최적화
4. **표준 패턴 사용**: FastAPI 공식 가이드 준수

---

## 🧪 테스트 전략

### 기본 테스트 구조
```python
# tests/test_account_service.py
import pytest
from app.services.account_service import AccountService

@pytest.fixture
def mock_client():
    # Mock 클라이언트 생성
    pass

@pytest.mark.asyncio
async def test_get_balance(mock_client):
    service = AccountService(mock_client)
    result = await service.get_balance()
    assert len(result) > 0
    assert result[0].종목코드 is not None
```

### API 테스트
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_balance():
    response = client.get("/api/account/balance")
    assert response.status_code == 200
    assert "data" in response.json()
```

---

## 🔍 개발 워크플로우

### 1. **새 API 개발 순서**
1. 모델 정의 (Pydantic)
2. 서비스 로직 작성
3. 라우터 생성
4. 테스트 작성
5. 문서 확인 (`/docs`)

### 2. **에러 처리 패턴**
```python
try:
    result = await external_api_call()
    return {"status": "success", "data": result}
except Exception as e:
    logger.error(f"API 호출 실패: {e}")
    raise HTTPException(status_code=500, detail="서버 오류")
```

### 3. **로깅 설정**
```python
# app/core/logging.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

---

## 📋 체크리스트

### API 개발 전
- [ ] 요구사항 명확히 정의
- [ ] 외부 API 연동 방법 확인
- [ ] 데이터 모델 설계

### API 개발 중
- [ ] Pydantic 모델로 요청/응답 검증
- [ ] 적절한 HTTP 상태 코드 사용
- [ ] 에러 처리 구현

### API 개발 후
- [ ] `/docs`에서 API 문서 확인
- [ ] 기본 테스트 실행
- [ ] 프론트엔드 연동 테스트

---

**핵심 원칙**: 동작하는 코드를 먼저 만들고, 필요에 따라 개선하기