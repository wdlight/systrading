# 과거 차트 데이터 자동 로딩 구현 완료 (2025-10-03)

## ✅ 구현 완료 사항

### Phase 1: Backend 구현 ✅

#### 1. 거래일 유틸리티 (`trading_calendar.py`)
```python
@classmethod
def get_previous_trading_days(cls, from_date: datetime, count: int) -> list[datetime]:
    """특정 날짜로부터 이전 N개 거래일 반환"""
    # 주말/공휴일 자동 제외
    # 예: 월요일 10/7 → [목 10/2, 수 10/1, 화 9/30]

@classmethod
def get_trading_days_in_range(cls, start_date: datetime, end_date: datetime) -> list[datetime]:
    """날짜 범위 내의 모든 거래일 리스트 반환"""
```

**특징:**
- 한국 공휴일 (2024/2025년) 자동 처리
- 추석 연휴 (10/5-10/7/2025) 정확히 제외
- 최대 10일 전까지 탐색 (연휴 대비)

#### 2. 범위 조회 서비스 (`trading_service.py`)
```python
async def get_minute_chart_data_range(
    self,
    stock_code: str,
    end_date: Optional[datetime] = None,
    max_days: int = 10
) -> Dict[str, List[ChartCandle]]:
    """
    날짜 범위의 분봉 데이터 조회

    Returns:
        {
            "20251006": [360개 ChartCandle],
            "20251003": [360개 ChartCandle],
            ...
        }
    """
```

**특징:**
- 캐시 우선 전략 (캐시 있으면 API 호출 안 함)
- 비거래일 자동 제외
- 날짜별 딕셔너리로 반환 (Frontend 메모리 캐시용)

#### 3. API 엔드포인트 (`chart.py`)
```http
GET /api/chart/{stock_code}/minute-range?end_date=2025-10-06&max_days=4

응답:
{
  "20251006": [360개 ChartCandle],  // 월요일
  "20251003": [360개 ChartCandle],  // 금요일
  "20251002": [360개 ChartCandle],  // 목요일
  "20251001": [360개 ChartCandle]   // 수요일
}
```

**특징:**
- 미래 날짜 방지 검증
- 날짜 형식 검증 (YYYY-MM-DD)
- 1~30일 범위 제한
- 상세한 로깅

---

### Phase 2: Frontend 구현 ✅

#### 1. 커스텀 훅 (`useHistoricalChartData.ts`)

**핵심 기능:**
```typescript
const {
  chartData,       // 전체 차트 데이터 (오늘 + 과거 N일)
  isLoading,       // 로딩 상태
  error,           // 에러 메시지
  handleRangeChange, // Brush/Drag 이벤트 핸들러
  loadMoreData     // 수동 데이터 로드
} = useHistoricalChartData({
  stockCode: '005930',
  enabled: true,
  initialDays: 3
});
```

**동작 원리:**

1. **초기 로딩 (컴포넌트 마운트 시)**
   ```
   - 오늘 데이터 fetch: GET /api/chart/{stockCode}/minute
   - 과거 3일 데이터 fetch: GET /api/chart/{stockCode}/minute-range?max_days=3
   - 메모리 캐시에 날짜별로 저장
   - 시간순으로 병합하여 chartData 업데이트
   ```

2. **좌측 드래그 감지 (자동 로딩)**
   ```typescript
   handleRangeChange({ startIndex: 5, endIndex: 125 })

   if (startIndex < 10) {
     // 첫 번째 캔들의 하루 전 날짜 계산
     const previousDate = new Date(chartData[0].timestamp);
     previousDate.setDate(previousDate.getDate() - 1);

     // 과거 데이터 자동 로드
     loadMoreData(previousDate);
   }
   ```

3. **중복 요청 방지**
   ```typescript
   // 메모리 캐시 체크
   if (cacheRef.current[dateKey]) {
     console.log('캐시된 데이터 사용');
     return;
   }

   // 로딩 중 체크
   if (loadingDatesRef.current.has(dateKey)) {
     console.log('이미 로딩 중');
     return;
   }
   ```

#### 2. 차트 컴포넌트 수정 (`RealtimeCandlestickChart.tsx`)

**변경 전:**
```typescript
<RealtimeCandlestickChart
  chartData={candles}  // Props로 데이터 전달
  timeframe="1m"
/>
```

**변경 후:**
```typescript
<RealtimeCandlestickChart
  stockCode="005930"           // ✅ stockCode로 변경
  timeframe="1m"
  enableHistoricalLoad={true}  // 과거 데이터 자동 로딩
  initialDays={3}              // 초기 3일 프리로드
/>
```

**자동 처리 기능:**
- 초기 로딩 상태 표시
- 에러 처리 및 표시
- 과거 데이터 자동 병합
- Brush/Drag 이벤트 자동 연결

---

## 📊 사용 예제

### 기본 사용 (과거 3일 자동 로드)
```typescript
'use client';

import RealtimeCandlestickChart from '@/components/trading/RealtimeCandlestickChart';

export default function TradingPage() {
  return (
    <div>
      <h1>삼성전자 차트</h1>
      <RealtimeCandlestickChart
        stockCode="005930"
        timeframe="1m"
        height={500}
      />
    </div>
  );
}
```

### 고급 사용 (초기 7일 로드)
```typescript
<RealtimeCandlestickChart
  stockCode="005930"
  timeframe="1m"
  enableHistoricalLoad={true}
  initialDays={7}  // 과거 7일치 프리로드
  height={600}
/>
```

### 과거 데이터 비활성화 (오늘만)
```typescript
<RealtimeCandlestickChart
  stockCode="005930"
  timeframe="1m"
  enableHistoricalLoad={false}  // 과거 로딩 비활성화
/>
```

---

## 🔄 데이터 플로우

```
[사용자 액션]
  → 차트 마운트
    ↓
[useHistoricalChartData Hook]
  → 1. 오늘 데이터 fetch: /api/chart/005930/minute
  → 2. 과거 3일 fetch: /api/chart/005930/minute-range?max_days=3
  → 3. 메모리 캐시 저장: { "20251003": [...], "20251002": [...], ... }
  → 4. 시간순 병합: [...과거 데이터..., ...오늘 데이터...]
    ↓
[RechartsAdapter]
  → 전체 데이터 렌더링
  → Brush 컴포넌트로 120개 캔들 표시
    ↓
[사용자 좌측 드래그]
  → Brush onChange 이벤트 발생
  → handleRangeChange({ startIndex: 5, ... })
    ↓
[useHistoricalChartData]
  → if (startIndex < 10) {
      loadMoreData(이전 날짜)
    }
  → GET /api/chart/005930/minute-range?end_date=2025-10-02&max_days=1
  → 캐시 업데이트
  → chartData 앞에 추가: [...새 데이터..., ...기존 데이터...]
    ↓
[RechartsAdapter]
  → 전체 데이터 재렌더링
  → 사용자는 과거 데이터 확인 가능
```

---

## 🧪 테스트 방법

### Backend 테스트
```bash
cd backend
source vkis/bin/activate

# 거래일 유틸리티 테스트
python tests/test_trading_calendar_range.py

# API 테스트 (FastAPI 서버 실행 필요)
curl "http://localhost:8000/api/chart/005930/minute-range?end_date=2025-10-06&max_days=4"

# 예상 응답: 4개 날짜의 분봉 데이터 (총 1440개 캔들)
```

### Frontend 테스트
```bash
cd stock-trading-ui
npm run dev

# 브라우저에서 확인:
# 1. http://localhost:9000/trading 접속
# 2. 삼성전자 차트 확인 (초기 로딩: 오늘 + 과거 3일)
# 3. 차트 좌측으로 드래그 → 과거 데이터 자동 로드 확인
# 4. 브라우저 콘솔에서 로그 확인:
#    - "✅ 초기 데이터 로드 완료"
#    - "🔍 좌측 드래그 감지 → 과거 데이터 로드"
#    - "📥 과거 데이터 추가: 20251002, 360개 캔들"
```

---

## 🎯 주요 특징

### 1. 캐시 전략
- **Backend 파일 캐시**: `kordata/{stock_code}/{YYYYMMDD}.json`
- **Frontend 메모리 캐시**: `cacheRef.current[dateKey]`
- **중복 요청 방지**: `loadingDatesRef.current`

### 2. 성능 최적화
- 초기 로딩 시 1회 range API 호출 (3일치)
- 좌측 드래그 시 필요한 날짜만 fetch (1일치)
- 캐시된 데이터는 재사용 (네트워크 요청 없음)

### 3. 사용자 경험
- 로딩 상태 표시 ("과거 3일치 데이터 불러오는 중")
- 에러 처리 및 표시
- 매끄러운 데이터 병합 (깜빡임 없음)
- 자동 시간순 정렬

### 4. 확장성
- `initialDays` 파라미터로 초기 로딩 일수 조정 가능
- `enableHistoricalLoad` 로 기능 ON/OFF 가능
- `loadMoreData()` 함수로 수동 로딩 지원

---

## 🔧 트러블슈팅

### 문제 1: "미래 날짜는 조회할 수 없습니다"
**원인**: end_date가 오늘 이후
**해결**: useHistoricalChartData에서 자동으로 현재 날짜 이전만 요청

### 문제 2: 빈 데이터 반환
**원인**: 비거래일 (주말/공휴일) 요청
**해결**: TradingCalendar가 자동으로 거래일만 조회

### 문제 3: 중복 데이터
**원인**: 같은 날짜 여러 번 fetch
**해결**: 메모리 캐시와 loadingDatesRef로 중복 방지

### 문제 4: 차트가 업데이트되지 않음
**확인 사항**:
1. Backend API 서버 실행 여부 (`http://localhost:8000`)
2. 브라우저 콘솔에서 네트워크 오류 확인
3. stockCode 올바른지 확인 (예: "005930")

---

## 📁 변경된 파일 목록

### Backend
- ✅ `backend/app/utils/trading_calendar.py` - 거래일 유틸리티 추가
- ✅ `backend/app/services/trading_service.py` - 범위 조회 메서드 추가
- ✅ `backend/app/api/chart.py` - `/minute-range` 엔드포인트 추가
- ✅ `backend/tests/test_trading_calendar_range.py` - 테스트 추가

### Frontend
- ✅ `stock-trading-ui/src/hooks/useHistoricalChartData.ts` - 커스텀 훅 생성
- ✅ `stock-trading-ui/src/components/trading/RealtimeCandlestickChart.tsx` - Props 변경 및 훅 통합

### Documentation
- ✅ `docs/plan/historical-chart-drag.1003.md` - 구현 계획
- ✅ `docs/implementation/historical-chart-implementation.1003.md` - 구현 완료 문서

---

## 🚀 다음 단계 (선택 사항)

### 추가 기능 아이디어
1. **실시간 데이터 자동 업데이트**: WebSocket으로 현재 분봉 자동 갱신
2. **무한 스크롤 최적화**: Virtual scrolling으로 수천 개 캔들 처리
3. **날짜 범위 선택 UI**: 사용자가 직접 날짜 범위 선택
4. **다중 시간 프레임**: 5분봉, 10분봉, 1시간봉 지원
5. **데이터 내보내기**: CSV/JSON 다운로드 기능

### 성능 개선
1. **Progressive Loading**: 스크롤에 따라 점진적으로 데이터 로드
2. **Virtualization**: react-window로 렌더링 성능 개선
3. **Worker Thread**: 데이터 병합을 Web Worker에서 처리

---

## 📚 참고 자료

- Backend API: `/api/chart/{stock_code}/minute-range`
- Frontend Hook: `useHistoricalChartData`
- Chart Component: `RealtimeCandlestickChart`
- Adapter: `RechartsAdapter` (드래그 기능 내장)
- Calendar Utility: `TradingCalendar` (한국 공휴일 처리)

---

**구현 완료일**: 2025-10-03
**작성자**: Claude Code
**상태**: ✅ 완료 (Backend + Frontend 통합 완료)
