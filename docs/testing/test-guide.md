# 테스트 가이드

**프로젝트**: 주식 자동매매 시스템
**최종 업데이트**: 2025-10-08
**대상 독자**: 개발자, QA

---

## 📋 목차

1. [테스트 개요](#테스트-개요)
2. [Backend 테스트](#backend-테스트)
3. [Frontend 테스트](#frontend-테스트)
4. [통합 테스트](#통합-테스트)
5. [CLI 검증 도구](#cli-검증-도구)
6. [성능 테스트](#성능-테스트)

---

## 테스트 개요

### 테스트 전략
- **단위 테스트**: 개별 함수/메서드 검증
- **통합 테스트**: API 엔드포인트 검증
- **E2E 테스트**: 사용자 시나리오 검증 (향후 구현)
- **성능 테스트**: 응답 시간 및 처리량 측정

### 테스트 환경
- **Backend**: pytest 사용
- **Frontend**: Jest + React Testing Library (설정 필요)
- **API**: curl, Postman, HTTPie
- **CLI**: 커스텀 Python 스크립트

---

## Backend 테스트

### 1. 단위 테스트 (pytest)

#### 1-1. 환경 설정
```bash
cd backend
source vkis/bin/activate

# pytest 설치 (requirements.txt에 포함되어야 함)
pip install pytest pytest-asyncio pytest-cov
```

#### 1-2. 테스트 파일 구조
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # pytest 설정
│   ├── test_kosdaq_index_service.py   # KOSDAQ 지수 테스트
│   ├── test_overseas_index_service.py # 해외 지수 테스트
│   ├── test_chart_cache_service.py    # 차트 캐시 테스트
│   └── test_trading_service.py        # 매매 서비스 테스트
```

#### 1-3. 테스트 실행
```bash
# 전체 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_kosdaq_index_service.py

# 상세 출력 (-v verbose)
pytest tests/test_kosdaq_index_service.py -v

# 커버리지 확인
pytest --cov=app --cov-report=html

# 결과 확인
open htmlcov/index.html  # Mac
# 또는
xdg-open htmlcov/index.html  # Linux
```

---

### 2. KOSDAQ 지수 테스트

**파일**: `tests/test_kosdaq_index_service.py`

#### 테스트 내용
- 후보 코드 순회 검증
- 원본 응답 메타 정보 확인
- 0 값 fallback 동작 확인

#### 실행 예시
```bash
./vkis/bin/python tests/test_kosdaq_index_service.py -v
```

**예상 출력**:
```
[J-1001]
  current: 0.0
  rt_cd: 0
  msg_cd: SUCCESS
  msg1: 정상처리 되었습니다.
  ❌ FAILED (0 value)

[J-0201]
  current: 750.50
  change: 5.20
  change_rate: 0.70
  rt_cd: 0
  ✅ SUCCESS
```

#### 코드 예시
```python
import pytest
from app.core.korea_invest import KoreaInvestAPIService

@pytest.mark.asyncio
async def test_kosdaq_candidates():
    """KOSDAQ 후보 코드 테스트"""
    service = KoreaInvestAPIService()

    candidates = [
        ("J", "1001"),
        ("J", "0201"),
        ("J", "1501"),
    ]

    for market_code, index_code in candidates:
        result = await service.get_index_current_price(
            index_code, market_code
        )

        print(f"\n[{market_code}-{index_code}]")
        assert result is not None, "결과가 None이 아니어야 함"

        # 원본 응답 확인
        raw = service.last_raw_response
        assert raw.get("rt_cd") == "0", "rt_cd는 '0'이어야 함"

        if result.current > 0:
            print("  ✅ SUCCESS")
            break
```

---

### 3. 해외 지수 테스트

**파일**: `tests/test_overseas_index_service.py`

#### 테스트 내용
- NASDAQ, S&P 500, USD/KRW 조회
- 후보 코드 순회 검증
- API 응답 파싱 정확성

#### 실행 예시
```bash
./vkis/bin/python -m pytest tests/test_overseas_index_service.py -v
```

#### 코드 예시
```python
@pytest.mark.asyncio
async def test_nasdaq_index():
    """NASDAQ 지수 조회 테스트"""
    service = KoreaInvestAPIService()
    result = await service.get_overseas_index_price("nasdaq")

    assert result is not None
    assert result.current > 0, "NASDAQ 현재가가 0보다 커야 함"
    assert result.meta.get("rt_cd") == "0"

@pytest.mark.asyncio
async def test_sp500_index():
    """S&P 500 지수 조회 테스트"""
    service = KoreaInvestAPIService()
    result = await service.get_overseas_index_price("sp500")

    assert result is not None
    assert result.current > 0

@pytest.mark.asyncio
async def test_usdkrw_exchange():
    """USD/KRW 환율 조회 테스트"""
    service = KoreaInvestAPIService()
    result = await service.get_overseas_index_price("usdkrw")

    assert result is not None
    assert result.current > 1000, "USD/KRW는 1000 이상이어야 함"
```

---

### 4. 차트 캐시 테스트

**파일**: `tests/test_chart_cache_service.py`

#### 테스트 내용
- 캐시 파일 생성 확인
- 캐시 Hit/Miss 시나리오
- 연도별 분리 검증

#### 코드 예시
```python
import os
import pytest
from datetime import datetime
from app.services.chart_cache_service import ChartCacheService
from app.core.korea_invest import KoreaInvestAPIService

@pytest.mark.asyncio
async def test_daily_cache_creation():
    """일봉 캐시 파일 생성 테스트"""
    cache_service = ChartCacheService()
    kis_service = KoreaInvestAPIService()

    stock_code = "005930"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # 캐시 파일이 없는 경우 생성되는지 확인
    result = await cache_service.get_daily_candles(
        stock_code, start_date, end_date, kis_service
    )

    assert result is not None
    assert len(result) > 0

    # 캐시 파일 존재 확인
    cache_path = f"kordata/{stock_code}/daily/2024.json"
    assert os.path.exists(cache_path)

@pytest.mark.asyncio
async def test_cache_hit():
    """캐시 Hit 시나리오 테스트"""
    cache_service = ChartCacheService()
    kis_service = KoreaInvestAPIService()

    stock_code = "005930"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # 1차 호출 (캐시 생성)
    result1 = await cache_service.get_daily_candles(
        stock_code, start_date, end_date, kis_service
    )

    # 2차 호출 (캐시에서 로드)
    import time
    start_time = time.time()
    result2 = await cache_service.get_daily_candles(
        stock_code, start_date, end_date, kis_service
    )
    elapsed = time.time() - start_time

    assert result1 == result2
    assert elapsed < 0.5, "캐시 응답은 0.5초 이내여야 함"
```

---

## CLI 검증 도구

### 1. 해외 지수 확인 스크립트

**파일**: `scripts/check_overseas_indices.py`

#### 사용법
```bash
cd backend

# NASDAQ 확인
python scripts/check_overseas_indices.py --target nasdaq

# S&P 500 확인
python scripts/check_overseas_indices.py --target sp500

# USD/KRW 확인
python scripts/check_overseas_indices.py --target usdkrw

# 전체 확인
for target in nasdaq sp500 usdkrw; do
    python scripts/check_overseas_indices.py --target $target
done
```

#### 예상 출력
```
✅ NASDAQ 성공
  현재가: 15234.56
  전일대비: +125.30 (+0.83%)
  rt_cd: 0
  msg1: 정상처리 되었습니다.
```

#### 코드 예시
```python
import asyncio
import argparse
from app.core.korea_invest import KoreaInvestAPIService

async def check_index(target: str):
    """해외 지수/환율 확인"""
    service = KoreaInvestAPIService()
    result = await service.get_overseas_index_price(target)

    if result and result.current > 0:
        print(f"✅ {target.upper()} 성공")
        print(f"  현재가: {result.current}")
        print(f"  전일대비: {result.change:+.2f} ({result.change_rate:+.2f}%)")
        print(f"  rt_cd: {result.meta.get('rt_cd')}")
    else:
        print(f"❌ {target.upper()} 실패")
        raw = service.last_raw_response
        print(f"  rt_cd: {raw.get('rt_cd')}")
        print(f"  msg1: {raw.get('msg1')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target",
                       choices=["nasdaq", "sp500", "usdkrw"],
                       required=True)
    args = parser.parse_args()

    asyncio.run(check_index(args.target))
```

---

### 2. 계좌 잔고 확인 스크립트

**파일**: `scripts/check_account_balance.py`

```python
import asyncio
from app.services.stock_info_service import StockInfoService

async def check_balance():
    """계좌 잔고 확인"""
    service = StockInfoService()
    balance = await service.get_account_balance()

    print(f"총 평가금액: {balance.total_value:,}원")
    print(f"총 매입금액: {balance.total_purchase:,}원")
    print(f"총 평가손익: {balance.total_profit:+,}원")
    print(f"수익률: {balance.profit_rate:+.2f}%")

    print("\n보유 종목:")
    for position in balance.positions:
        print(f"  {position.name} ({position.code})")
        print(f"    수량: {position.quantity}")
        print(f"    매입가: {position.avg_price:,}원")
        print(f"    현재가: {position.current_price:,}원")
        print(f"    수익률: {position.profit_rate:+.2f}%")

if __name__ == "__main__":
    asyncio.run(check_balance())
```

**실행**:
```bash
python scripts/check_account_balance.py
```

---

## Frontend 테스트

### 1. 환경 설정 (향후 구현)

```bash
cd stock-trading-ui

# Jest 설치
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
```

**jest.config.js**:
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
```

---

### 2. 컴포넌트 테스트 예시

**파일**: `__tests__/MarketOverview.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import { MarketOverview } from '@/components/trading/MarketOverview';

describe('MarketOverview', () => {
  it('renders all index tiles', () => {
    render(<MarketOverview />);

    expect(screen.getByText('KOSPI')).toBeInTheDocument();
    expect(screen.getByText('KOSDAQ')).toBeInTheDocument();
    expect(screen.getByText('NASDAQ')).toBeInTheDocument();
    expect(screen.getByText('S&P 500')).toBeInTheDocument();
    expect(screen.getByText('USD/KRW')).toBeInTheDocument();
  });

  it('displays fallback message for zero values', () => {
    render(<MarketOverview />);

    // 0 값일 때 "실시간 데이터 수신 대기" 표시
    const badges = screen.getAllByText('실시간 데이터 수신 대기');
    expect(badges.length).toBeGreaterThan(0);
  });
});
```

---

## 통합 테스트

### 1. API 엔드포인트 테스트

#### 1-1. curl로 테스트

**Market Overview**:
```bash
curl http://localhost:8000/api/stocks/overview | jq
```

**예상 응답**:
```json
{
  "kospi": {
    "name": "KOSPI",
    "current": 2580.50,
    "change": 15.30,
    "change_rate": 0.60
  },
  "kosdaq": {
    "name": "KOSDAQ",
    "current": 750.20,
    "change": -2.10,
    "change_rate": -0.28
  },
  "nasdaq": {
    "name": "NASDAQ",
    "current": 15234.56,
    "change": 125.30,
    "change_rate": 0.83
  },
  "sp500": {...},
  "usdkrw": {...},
  "timestamp": "2025-10-08T10:00:00Z"
}
```

**일봉 차트 데이터**:
```bash
curl "http://localhost:8000/api/chart/005930/day?start_date=2024-01-01&end_date=2025-10-08" | jq
```

**분봉 차트 데이터**:
```bash
curl "http://localhost:8000/api/chart/005930/minute?start_date=2025-10-08&end_date=2025-10-08" | jq
```

---

#### 1-2. HTTPie로 테스트

```bash
# HTTPie 설치
pip install httpie

# Market Overview
http GET localhost:8000/api/stocks/overview

# 계좌 잔고
http GET localhost:8000/api/account/balance

# 매매 조건
http GET localhost:8000/api/conditions
```

---

### 2. WebSocket 테스트

**Python 스크립트**:
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        print("WebSocket 연결 성공")

        # 메시지 수신
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            print(f"수신: {data.get('type')}")
            if data.get("type") == "market_index_update":
                index_name = data.get("index_name")
                current = data.get("data", {}).get("current")
                print(f"  {index_name}: {current}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
```

**실행**:
```bash
python scripts/test_websocket.py
```

---

## 성능 테스트

### 1. 캐시 성능 측정

**스크립트**: `scripts/benchmark_cache.py`

```python
import asyncio
import time
from app.services.chart_cache_service import ChartCacheService
from app.core.korea_invest import KoreaInvestAPIService
from datetime import datetime

async def benchmark_cache():
    cache_service = ChartCacheService()
    kis_service = KoreaInvestAPIService()

    stock_code = "005930"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # 1차 호출 (캐시 Miss)
    start_time = time.time()
    result1 = await cache_service.get_daily_candles(
        stock_code, start_date, end_date, kis_service
    )
    time1 = time.time() - start_time

    # 2차 호출 (캐시 Hit)
    start_time = time.time()
    result2 = await cache_service.get_daily_candles(
        stock_code, start_date, end_date, kis_service
    )
    time2 = time.time() - start_time

    print(f"캐시 Miss: {time1:.3f}초")
    print(f"캐시 Hit: {time2:.3f}초")
    print(f"성능 향상: {(1 - time2/time1) * 100:.1f}%")

if __name__ == "__main__":
    asyncio.run(benchmark_cache())
```

**예상 출력**:
```
캐시 Miss: 2.345초
캐시 Hit: 0.082초
성능 향상: 96.5%
```

---

### 2. API 부하 테스트 (Apache Bench)

```bash
# Apache Bench 설치
sudo apt install apache2-utils

# GET 요청 부하 테스트
ab -n 1000 -c 10 http://localhost:8000/api/stocks/overview

# 결과 분석
# - Requests per second: 초당 요청 처리량
# - Time per request: 평균 응답 시간
# - Transfer rate: 전송 속도
```

**예상 출력**:
```
Requests per second:    250.00 [#/sec] (mean)
Time per request:       40.000 [ms] (mean)
Time per request:       4.000 [ms] (mean, across all concurrent requests)
```

---

## 테스트 자동화

### 1. GitHub Actions (향후 구현)

**파일**: `.github/workflows/test.yml`

```yaml
name: Test

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12
      - name: Install dependencies
        run: |
          cd backend
          python -m venv vkis
          source vkis/bin/activate
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          source vkis/bin/activate
          pytest --cov=app

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Install dependencies
        run: |
          cd stock-trading-ui
          npm install
      - name: Run tests
        run: |
          cd stock-trading-ui
          npm test
```

---

## 테스트 체크리스트

### Backend 테스트
- [ ] 단위 테스트 전체 통과
- [ ] KOSDAQ 후보 코드 테스트 성공
- [ ] 해외 지수 조회 테스트 성공
- [ ] 차트 캐시 테스트 성공
- [ ] API 엔드포인트 테스트 성공
- [ ] WebSocket 연결 테스트 성공

### Frontend 테스트
- [ ] 컴포넌트 렌더링 테스트 (향후)
- [ ] 훅 동작 테스트 (향후)
- [ ] API 통합 테스트 (향후)

### CLI 검증
- [ ] NASDAQ 지수 확인 성공
- [ ] S&P 500 지수 확인 성공
- [ ] USD/KRW 환율 확인 성공
- [ ] 계좌 잔고 확인 성공

### 성능 테스트
- [ ] 캐시 성능 95% 이상 향상
- [ ] API 응답 시간 1초 이내
- [ ] WebSocket 연결 안정성 확인

---

**문서 버전**: 1.0
**작성일**: 2025-10-08
**담당자**: QA Team
