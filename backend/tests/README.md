# Simple Server 테스트 가이드

## 개요
`simple_server.py`의 모든 API 엔드포인트와 함수들에 대한 단위 테스트를 제공합니다.

## 테스트 구조

### 테스트 파일 구성
```
tests/
├── __init__.py                 # 테스트 패키지 초기화
├── conftest.py                 # pytest 설정 및 공통 픽스처
├── test_simple_server.py       # simple_server.py 단위 테스트
└── README.md                   # 이 파일
```

### 테스트 클래스 구성
- `TestSimpleServerAPI`: 기본 API 엔드포인트 테스트
- `TestAccountBalanceAPI`: 계좌 잔고 관련 API 테스트
- `TestTradingConditionsAPI`: 매매 조건 API 테스트
- `TestWatchlistAPI`: 워치리스트 API 테스트
- `TestMarketOverviewAPI`: 시장 개요 API 테스트
- `TestWebSocketEndpoint`: WebSocket 연결 및 데이터 전송 테스트
- `TestMiscellaneousEndpoints`: 기타 엔드포인트 테스트
- `TestUtilityFunctions`: 유틸리티 함수 테스트
- `TestCORSMiddleware`: CORS 미들웨어 테스트

## 테스트 실행

### 기본 실행
```bash
# 전체 테스트 실행
cd backend
python -m pytest tests/test_simple_server.py -v

# 또는 테스트 러너 사용
python run_tests.py simple_server
```

### 특정 테스트 클래스 실행
```bash
# 계좌 잔고 API만 테스트
python -m pytest tests/test_simple_server.py::TestAccountBalanceAPI -v

# WebSocket 테스트만 실행
python -m pytest tests/test_simple_server.py::TestWebSocketEndpoint -v
```

### 특정 테스트 메서드 실행
```bash
# 특정 함수만 테스트
python -m pytest tests/test_simple_server.py::TestSimpleServerAPI::test_root_endpoint -v
```

### 커버리지와 함께 실행
```bash
python -m pytest tests/test_simple_server.py --cov=simple_server --cov-report=html
```

## 테스트 범위

### API 엔드포인트 테스트 (100% 커버리지)

#### 기본 엔드포인트
- ✅ `GET /` - 루트 엔드포인트
- ✅ `GET /hello` - Hello 메시지
- ✅ `GET /health` - 헬스체크
- ✅ `GET /debug/tokens` - 토큰 디버그 정보

#### 계좌 관련 엔드포인트
- ✅ `GET /api/account/balance` - 계좌 잔고 조회
  - 실제 API 없을 때 더미 데이터 반환
  - 실제 API 있을 때 실제 데이터 반환
  - API 오류시 더미 데이터 fallback
- ✅ `POST /api/account/refresh` - 계좌 정보 갱신

#### 매매 조건 관련 엔드포인트
- ✅ `GET /api/trading/conditions` - 매매 조건 조회
- ✅ `PUT /api/trading/conditions` - 매매 조건 업데이트
  - 성공 케이스
  - 데이터 유효성 검증 (RSI 범위, 최소 금액 등)
  - 오류 처리

#### 워치리스트 관련 엔드포인트
- ✅ `GET /api/watchlist` - 워치리스트 조회
  - 실제 API 없을 때 더미 데이터
  - 실제 API 있을 때 실제 데이터 + 보유 종목 정보

#### 시장 정보 엔드포인트
- ✅ `GET /api/market/overview` - 시장 개요
  - 기본 지수 정보 (KOSPI, KOSDAQ, USD/KRW)
  - 상승/하락 종목 정보

#### WebSocket 엔드포인트
- ✅ `WS /ws` - WebSocket 연결
  - 연결 수립 테스트
  - 실시간 데이터 전송 테스트

### 유틸리티 함수 테스트

#### 전역 변수 및 설정
- ✅ `trading_conditions_data` - 매매 조건 데이터 구조 검증
- ✅ `active_connections` - 활성 WebSocket 연결 목록

#### 미들웨어
- ✅ `CustomCORSMiddleware` - CORS 헤더 처리
  - GET 요청시 헤더 확인
  - OPTIONS 프리플라이트 요청 처리

## Mock 및 Fixture 사용

### 주요 Mock 객체
```python
# 실제 API 모킹
with patch('simple_server.real_api', mock_real_api):
    # 테스트 코드

# 설정 모킹
with patch('simple_server.get_settings', return_value=mock_settings):
    # 테스트 코드
```

### 테스트 데이터
- 계좌 잔고 데이터 (DataFrame 형태)
- 차트 데이터 (pandas DataFrame)
- 매매 조건 설정
- WebSocket 메시지 형태

## 테스트 결과 해석

### 성공한 테스트
```
tests/test_simple_server.py::TestSimpleServerAPI::test_root_endpoint PASSED
tests/test_simple_server.py::TestAccountBalanceAPI::test_get_account_balance_no_real_api PASSED
```

### 실패한 테스트
```
tests/test_simple_server.py::TestTradingConditionsAPI::test_update_trading_conditions_error FAILED
```

## 추가할 수 있는 테스트

### 성능 테스트
```python
@pytest.mark.slow
def test_websocket_multiple_connections():
    """다중 WebSocket 연결 성능 테스트"""
    # 여러 클라이언트 동시 연결 테스트
```

### 통합 테스트
```python
@pytest.mark.integration
def test_full_trading_workflow():
    """전체 매매 워크플로우 통합 테스트"""
    # 워치리스트 조회 → 매매 조건 확인 → 주문 실행
```

### 보안 테스트
```python
def test_cors_security():
    """CORS 보안 설정 테스트"""
    # 허용되지 않은 도메인에서의 요청 차단
```

## 테스트 환경 설정

### 필수 패키지
```bash
pip install pytest pytest-asyncio httpx
```

### 환경 변수 (선택적)
```bash
export PYTEST_CURRENT_TEST=1  # 테스트 모드 활성화
```

## 디버깅 팁

### 테스트 실패시 디버깅
```bash
# 더 자세한 오류 정보 출력
python -m pytest tests/test_simple_server.py::TestAccountBalanceAPI::test_get_account_balance_with_real_api -v -s --tb=long

# pdb 디버거 사용
python -m pytest tests/test_simple_server.py::TestAccountBalanceAPI::test_get_account_balance_with_real_api --pdb
```

### 로그 출력 확인
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 지속적인 테스트 개선

### 커버리지 목표
- 현재: API 엔드포인트 100% 커버리지
- 목표: 전체 코드 90% 이상 커버리지

### 추가 개선 사항
1. **에러 케이스 확대**: 더 다양한 예외 상황 테스트
2. **데이터 검증**: 응답 데이터 스키마 검증 강화
3. **성능 테스트**: 부하 테스트 및 메모리 사용량 테스트
4. **보안 테스트**: 인증, 권한, 입력 검증 테스트