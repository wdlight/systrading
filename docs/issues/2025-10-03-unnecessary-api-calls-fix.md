# 불필요한 분봉 API 호출 문제 해결

**날짜**: 2025-10-03
**심각도**: Medium
**상태**: ✅ 해결됨
**관련 파일**:
- `backend/app/services/chart_cache_service.py`
- `backend/app/services/trading_service.py`
- `stock-trading-ui/src/hooks/useRealChartData.ts`

---

## 📋 문제 요약

백엔드 로그에서 아무런 사용자 액션이 없는데도 **분봉 데이터를 계속해서 요청**하는 문제가 발견됨.

### 증상
- 캐시에 데이터가 있음에도 불구하고 반복적인 API 호출 발생
- 한국투자증권 API 불필요한 호출로 인한 Rate Limit 위험
- 서버 리소스 낭비

---

## 🔍 원인 분석

### 1️⃣ **Frontend: 자동 새로고침 활성화**

**파일**: `stock-trading-ui/src/hooks/useRealChartData.ts` (227-241줄)

```typescript
// 자동 새로고침
useEffect(() => {
  if (!autoRefresh || !enabled || !stockCode) {
    return;
  }

  const intervalId = setInterval(() => {
    console.log(`🔄 Auto-refreshing chart data for ${stockCode}`);
    fetchChartData();  // ⚠️ refreshInterval마다 무조건 API 호출
  }, refreshInterval);

  return () => clearInterval(intervalId);
}, [autoRefresh, enabled, stockCode, refreshInterval, fetchChartData]);
```

**문제점**:
- `autoRefresh: true` 시 `refreshInterval` 마다 백엔드에 요청
- 1분봉의 경우 기본값 `refreshInterval = 5000` (5초마다!)
- **캐시 유무와 관계없이 무조건 API 호출**

**영향도**:
- Frontend에서 요청 자체를 계속 보내므로 Backend도 계속 처리해야 함

---

### 2️⃣ **Backend: Gap Fill 조건이 너무 느슨함**

**파일**: `backend/app/services/chart_cache_service.py` (108-160줄)

#### 문제 1: 장 종료 후에도 Gap 감지

```python
# ❌ 기존 코드
def _needs_gap_fill(self, cached_candles, target_date):
    now = datetime.now()

    # 장 시작 전이면 gap-fill 불필요
    if not TradingHoursManager.is_trading_hours(now):
        # 15:30 이후라면 gap-fill 시도  ⚠️ 문제!
        if now.hour < 15 or (now.hour == 15 and now.minute < 30):
            return False

    # 2분 이상 차이나면 gap 존재
    gap_minutes = (now - latest_time).total_seconds() / 60
    if gap_minutes >= 2:
        return True  # ⚠️ 거래시간 종료 후에도 계속 감지
```

**문제점**:
- 15:30 장 종료 후에도 계속 Gap 감지
- 예: 15:32에 요청 → 2분 차이 → Gap 감지 → 불필요한 API 호출

---

### 3️⃣ **Backend: Gap Fill 후 캐시 저장 안 함**

**파일**: `backend/app/services/trading_service.py` (151-158줄)

```python
# ❌ 기존 코드
raw_data = await self.chart_cache_service.get_minute_candles(
    stock_code=stock_code,
    target_date=query_date,
    korea_invest_service=self.korea_invest_service,
    skip_cache_save=True  # ⚠️ 문제: Gap Fill 후 캐시에 저장 안 함!
)
```

**문제점**:
- Gap Fill로 최신 데이터를 받아와도 **중간 캐시에 저장하지 않음**
- 다음 요청 시 또다시 Gap을 감지하고 API 호출 반복
- 캐시의 의미가 없어짐

---

## ✅ 해결 방법

### 1️⃣ **Backend: Gap Fill 조건 개선**

**파일**: `backend/app/services/chart_cache_service.py`

```python
# ✅ 수정된 코드
def _needs_gap_fill(self, cached_candles, target_date):
    # 오늘 날짜가 아니면 gap-fill 불필요
    if target_date.date() != datetime.now().date():
        return False

    now = datetime.now()

    # ✅ 장 시작 전이면 gap-fill 불필요 (9:00 이전)
    if now.hour < 9:
        logger.debug("장 시작 전 - gap fill 불필요")
        return False

    # ✅ 장 종료 후면 gap-fill 불필요 (15:30 이후)
    if now.hour > 15 or (now.hour == 15 and now.minute >= 30):
        logger.debug("장 종료 후 - gap fill 불필요")
        return False

    # ✅ 거래시간(9:00~15:30) 내에만 gap fill 실행
    gap_minutes = (now - latest_time).total_seconds() / 60
    if gap_minutes >= 2:
        logger.info(f"Gap detected: {gap_minutes:.1f}분")
        return True

    return False
```

**개선 사항**:
- 거래시간(9:00~15:30) 외에는 gap fill 안 함
- 장 종료 후 불필요한 API 호출 방지

---

### 2️⃣ **Backend: Cache 저장 활성화**

**파일**: `backend/app/services/trading_service.py`

```python
# ✅ 수정된 코드
raw_data = await self.chart_cache_service.get_minute_candles(
    stock_code=stock_code,
    target_date=query_date,
    korea_invest_service=self.korea_invest_service,
    skip_cache_save=False  # ✅ Gap Fill 시 캐시에 저장
)
```

**개선 사항**:
- Gap Fill 후 중간 캐시에 저장
- 다음 요청 시 캐시에서 즉시 반환 (API 호출 없음)

---

### 3️⃣ **Frontend: autoRefresh 사용 주의 (권장사항)**

**파일**: `stock-trading-ui/src/hooks/useRealChartData.ts`

#### 옵션 1: autoRefresh 비활성화 (권장)
```typescript
const { chartData } = useRealChartData(stockCode, '1m', {
  autoRefresh: false,  // ✅ 불필요한 polling 방지
  enabled: true
});
```

#### 옵션 2: 거래시간에만 polling
```typescript
const isMarketOpen = () => {
  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const time = hours * 60 + minutes;
  return time >= 540 && time <= 930; // 9:00~15:30
};

useEffect(() => {
  if (!autoRefresh || !enabled || !stockCode) return;

  const intervalId = setInterval(() => {
    if (isMarketOpen()) {  // ✅ 거래시간에만 polling
      fetchChartData();
    }
  }, refreshInterval);

  return () => clearInterval(intervalId);
}, [autoRefresh, enabled, stockCode, refreshInterval, fetchChartData]);
```

---

## 📊 개선 효과

### Before (수정 전)
```
┌─────────────────────────────────────────┐
│ Frontend (autoRefresh: true)            │
│ - 5초마다 무조건 API 요청               │
└─────────────────────────────────────────┘
              ↓ (매 5초)
┌─────────────────────────────────────────┐
│ Backend                                  │
│ - 15:30 이후에도 Gap 감지               │
│ - Gap Fill 후 캐시 저장 안 함            │
│ - 매번 한투 API 호출 (불필요)            │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 한국투자증권 API                         │
│ - Rate Limit 위험 증가                  │
│ - 서버 부하 증가                         │
└─────────────────────────────────────────┘
```

### After (수정 후)
```
┌─────────────────────────────────────────┐
│ Frontend                                 │
│ - 필요 시에만 요청 (권장)                │
│ - 거래시간에만 polling (선택)            │
└─────────────────────────────────────────┘
              ↓ (필요 시)
┌─────────────────────────────────────────┐
│ Backend                                  │
│ ✅ 캐시 우선 조회                        │
│ ✅ 거래시간 내에만 Gap Fill              │
│ ✅ Gap Fill 후 캐시 저장                 │
│ ✅ 15:30 이후 API 호출 안 함             │
└─────────────────────────────────────────┘
              ↓ (캐시 미스 시만)
┌─────────────────────────────────────────┐
│ 한국투자증권 API                         │
│ ✅ 최소한의 API 호출                     │
│ ✅ Rate Limit 안전                      │
└─────────────────────────────────────────┘
```

---

## 🎯 캐싱 전략 요약

### **과거 데이터 (Historical Data)**
```
1. 캐시 조회 → 캐시 히트 시 즉시 반환 ✅
2. 캐시 미스 → API 호출 → 영구 캐싱 ✅
3. 비거래일 → 이전 거래일 데이터 자동 반환 ✅
```

### **당일 데이터 (Today's Data)**
```
[거래시간 전 (9:00 이전)]
- 캐시 조회 → 전일 데이터 반환 ✅

[거래시간 중 (9:00~15:30)]
- 캐시 조회 → Gap 감지 → Gap 구간만 API 호출 ✅
- Gap Fill 후 캐시 업데이트 ✅

[거래시간 후 (15:30 이후)]
- 캐시 조회 → Gap Fill 안 함 ✅
- 전체 데이터 캐시에서 반환 ✅
```

---

## 🧪 테스트 시나리오

### 1. 과거 데이터 조회
```bash
# 첫 번째 요청: API 호출 → 캐시 저장
GET /api/chart/005930/minute?date=2025-10-01

# 두 번째 요청: 캐시에서 즉시 반환 (API 호출 없음)
GET /api/chart/005930/minute?date=2025-10-01
```

### 2. 당일 데이터 (거래시간 중)
```bash
# 10:00 첫 요청: API 호출 → 9:00~10:00 데이터
GET /api/chart/005930/minute/full

# 10:05 두 번째 요청: Gap(10:00~10:05) 만 API 호출
GET /api/chart/005930/minute/full

# 10:10 세 번째 요청: 캐시 히트 (Gap < 2분)
GET /api/chart/005930/minute/full
```

### 3. 장 종료 후
```bash
# 16:00 요청: 캐시에서 전체 반환 (API 호출 없음)
GET /api/chart/005930/minute/full
```

---

## 📝 권장사항

### Frontend 개발자
1. **불필요한 autoRefresh 제거**
   - 정적 차트: `autoRefresh: false`
   - 실시간 차트: WebSocket 사용 권장

2. **Polling 최소화**
   - 거래시간에만 polling
   - refreshInterval 적절히 조정 (최소 30초 이상)

### Backend 개발자
1. **캐시 모니터링**
   - 캐시 히트율 추적
   - API 호출 빈도 로깅

2. **Rate Limit 관리**
   - 한투 API 호출 제한 체크
   - 에러 발생 시 Exponential Backoff

---

## 🔗 관련 파일

### Backend
- `backend/app/services/chart_cache_service.py` - 캐시 로직
- `backend/app/services/trading_service.py` - 분봉 데이터 서비스
- `backend/app/core/korea_invest.py` - 한투 API 클라이언트

### Frontend
- `stock-trading-ui/src/hooks/useRealChartData.ts` - 차트 데이터 훅

### 문서
- `backend/CLAUDE.md` - Backend 개발 가이드
- `stock-trading-ui/CLAUDE.md` - Frontend 개발 가이드

---

## ✅ 체크리스트

- [x] Gap Fill 조건 개선 (거래시간 체크)
- [x] Cache 저장 활성화 (skip_cache_save=False)
- [x] 과거 데이터 캐싱 로직 검증
- [x] 문서 작성 및 권장사항 정리
- [ ] Frontend autoRefresh 최적화 (선택사항)
- [ ] 캐시 히트율 모니터링 추가 (향후)
- [ ] Rate Limit 알림 시스템 (향후)

---

**작성자**: Claude Code
**리뷰어**: -
**승인일**: -
