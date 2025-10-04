# 차트 초기 화면 및 비거래시간 처리 완전 해결 계획

작성일: 2025-10-03
상태: 실행 준비 완료

---

## 🔍 핵심 분석 결과

### 1. 시간대(Timezone) 이슈 파악

**Backend (Python):**
```python
# chart_cache_service.py:409
timestamp=timestamp.isoformat()  # ✅ ISO 8601 형식: "2025-10-03T09:00:00"
```
- Backend는 Python `datetime.isoformat()` 사용
- **시간대 정보 없음** (naive datetime)
- 로컬 시스템 시간 기준으로 저장 (KST 서버라면 KST)

**Frontend (TypeScript):**
```typescript
// datetime.ts:2
function getLocalDateAsString(date: Date): string {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}
```
- Frontend는 브라우저의 로컬 시간 사용
- `new Date(timestamp)` 파싱 시 브라우저 timezone 적용

**❌ 문제:**
- Backend: `"2025-10-03T09:00:00"` (시간대 정보 없음)
- Frontend 파싱: `new Date("2025-10-03T09:00:00")` → 브라우저 로컬 시간으로 해석
- **해결책:** Backend에서 명시적으로 KST timezone 추가 필요

---

### 2. 비거래시간 공백 문제 (15:30~09:00)

**현재 문제:**
```
[9:00 ━━━━ 15:30] [          빈 공간 (17시간)          ] [9:00 ━━━━ 15:30]
     Day 1                   비거래시간                        Day 2
```

**원인:**
- `xDomain`이 실제 시간(milliseconds)을 사용
- Recharts가 연속적인 시간축으로 렌더링
- 15:30~09:00 사이 데이터 없음 → 빈 공간 발생

---

## 🎯 완전 해결 계획

### 📌 핵심 전략: **인덱스 기반 X축 + 커스텀 Tick 포맷터**

비거래시간을 무시하고 실제 데이터만 연속으로 표시:

```
❌ Before (시간 기반):
[9:00][9:30][10:00]...[15:30][        공백        ][9:00][9:30]

✅ After (인덱스 기반):
[0][30][60]...[390][391][392]...[781]
 ↓   ↓   ↓         ↓    ↓    ↓        ↓
9:00 9:30 10:00  15:30 | 9:00 9:30   15:30
      Day 1            | Day 2 (연속 표시)
```

---

## 🔧 수정 계획 (4단계)

### **1단계: Backend Timezone 명시 ⭐⭐⭐ (필수)**

**목표:** Backend timestamp에 KST timezone 정보 명시

**파일:** `backend/app/services/chart_cache_service.py` (라인 408-409)

**변경 전:**
```python
timestamp = target_date.replace(
    hour=hour, minute=minute, second=second, microsecond=0
)
candle = ChartCandle(
    timestamp=timestamp.isoformat(),  # ❌ 시간대 정보 없음
    ...
)
```

**변경 후:**
```python
from datetime import timezone, timedelta

# KST = UTC+9
KST = timezone(timedelta(hours=9))

timestamp = target_date.replace(
    hour=hour, minute=minute, second=second,
    microsecond=0, tzinfo=KST  # ✅ KST 명시
)
candle = ChartCandle(
    timestamp=timestamp.isoformat(),  # "2025-10-03T09:00:00+09:00"
    ...
)
```

**효과:**
- Frontend에서 `new Date("2025-10-03T09:00:00+09:00")` 파싱 시 정확히 KST 9시로 인식
- 시간대 불일치 문제 완전 해결

---

### **2단계: 인덱스 기반 X축 전환 ⭐⭐⭐ (핵심)**

**목표:** 비거래시간 공백 제거 + 연속 데이터 표시

**파일:** `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx`

**A. 데이터 변환 (라인 206-262):**
```typescript
const formattedData = useMemo(() => {
  // ... 기존 로직 ...

  // ✅ 인덱스 추가
  const uniqueData = mapped.filter(...).map((candle, index) => ({
    ...candle,
    dataIndex: index,  // 0, 1, 2, ..., n
    displayTime: new Date(candle.time).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }));

  return uniqueData;
}, [chartData, onError]);
```

**B. X축 변경 (라인 418-443):**
```typescript
// ❌ 삭제: xDomain 계산 로직 (라인 275-294)

// ✅ 새로운 X축 설정
<XAxis
  dataKey="dataIndex"  // ✅ 시간 → 인덱스
  type="number"
  domain={[0, formattedData.length - 1]}  // 전체 데이터 범위
  ticks={
    // 적절한 간격으로 tick 생성 (예: 30개마다)
    formattedData
      .filter((_, i) => i % 30 === 0)
      .map(d => d.dataIndex)
  }
  tickFormatter={(dataIndex) => {
    const candle = formattedData[dataIndex];
    if (!candle) return '';

    const date = new Date(candle.time);
    const hours = date.getHours();
    const minutes = date.getMinutes();

    // 9:00이면 날짜 표시
    if (hours === 9 && minutes === 0) {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${month}/${day} 9:00`;
    }

    return `${hours}:${minutes.toString().padStart(2, '0')}`;
  }}
  stroke={KOREAN_CHART_THEME.textColor}
  fontSize={12}
/>
```

**C. Brush 변경 (라인 495-528):**
```typescript
<Brush
  dataKey="dataIndex"  // ✅ 시간 → 인덱스
  startIndex={viewWindow?.startIndex ?? Math.max(0, formattedData.length - 120)}
  endIndex={viewWindow?.endIndex ?? formattedData.length - 1}
  tickFormatter={(dataIndex) => {
    const candle = formattedData[dataIndex];
    if (!candle) return '';

    const date = new Date(candle.time);
    // ... 동일한 포맷팅 로직
  }}
/>
```

**효과:**
- 비거래시간 공백 완전 제거
- 데이터가 항상 연속으로 표시됨
- 드래그 시 차트 축소 문제 해결

---

### **3단계: 초기 viewWindow 수정 ⭐⭐**

**목표:** 데이터를 전체 범위에서 균형있게 표시

**파일:** `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx` (라인 312-329)

**변경 전:**
```typescript
// ❌ 항상 마지막 120개만 표시 (우측 밀집)
const windowSize = Math.min(120, formattedData.length);
const defaultStart = Math.max(0, formattedData.length - windowSize);
const defaultEnd = Math.min(defaultStart + windowSize - 1, formattedData.length - 1);
```

**변경 후:**
```typescript
const windowSize = Math.min(120, formattedData.length);

// ✅ 옵션 1: 데이터 중앙에 윈도우 배치
const centerIndex = Math.floor(formattedData.length / 2);
const defaultStart = Math.max(0, centerIndex - Math.floor(windowSize / 2));

// ✅ 옵션 2: 데이터 70% 지점에 윈도우 배치 (최근 데이터 강조)
// const defaultStart = Math.max(0, Math.floor(formattedData.length * 0.7) - windowSize);

const defaultEnd = Math.min(defaultStart + windowSize - 1, formattedData.length - 1);
```

**효과:**
- 초기 화면이 데이터 중앙 또는 적절한 위치에 표시
- 좌우 드래그로 과거/최근 데이터 탐색 가능

---

### **4단계: generateTimeTicks 정리 ⭐**

**목표:** 불필요한 코드 제거 (인덱스 기반으로 전환하므로 불필요)

**파일:** `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx` (라인 19)

**변경:**
```typescript
// ❌ 삭제: import에서 제거
import { TIMEFRAME_CONFIG, generateTimeTicks, isIntraday } from '@/lib/chart-config';

// ✅ 수정: 사용하지 않는 import 제거
import { TIMEFRAME_CONFIG } from '@/lib/chart-config';
```

---

## 📊 예상 결과

### Before (현재):
```
Time-based X-axis (연속 시간):
|9:00|9:30|10:00|...|15:30|[    공백 17시간    ]|9:00|9:30|
  Day 1 (밀집)              비거래시간              Day 2

- 데이터 우측 밀집
- 비거래시간 빈 공간
- 드래그 시 축소
```

### After (수정 후):
```
Index-based X-axis (연속 인덱스):
|0|30|60|...|390|391|420|...|780|
 9:00  10:00  15:30|9:00  10:00  15:30
      Day 1        |     Day 2

- 전체 데이터 고르게 분포
- 비거래시간 공백 없음
- 드래그 시 정상 작동
```

---

## 🔄 실행 순서

1. **Backend 수정 (1단계)** → `pytest` 테스트 → 서버 재시작
2. **Frontend 인덱스 기반 전환 (2단계)** → TypeScript 에러 확인 → 빌드
3. **초기 viewWindow 수정 (3단계)** → 브라우저 테스트
4. **import 정리 (4단계)** → 최종 빌드 확인
5. **통합 테스트:**
   - 초기 화면 위치 확인
   - 좌우 드래그 (과거/최근 데이터 로딩)
   - 비거래시간 공백 확인
   - 시간 축 레이블 정확도

---

## ⚠️ 주의사항

### Backend:
1. **Timezone import:** `from datetime import timezone, timedelta`
2. **기존 캐시 무효화:** 기존에 저장된 JSON 파일은 timezone 정보 없음 → 재생성 필요
3. **테스트:** `timestamp` 파싱 로직이 있는 모든 서비스 테스트

### Frontend:
1. **타입 정의:** `formattedData`에 `dataIndex` 추가
2. **Brush 상태 동기화:** `viewWindow`의 `startIndex`/`endIndex`가 인덱스 기반임
3. **Tooltip:** `CustomTooltip`에서 `time` 필드 접근 방식 확인
4. **성능:** 대량 데이터 시 tick 생성 최적화 필요

---

## 🎯 핵심 개념 정리

### 왜 인덱스 기반인가?

**시간 기반 (현재):**
- X축 = 실제 시간 (milliseconds)
- 9:00 (timestamp 1) → 15:30 (timestamp 390) → [공백 17시간] → 9:00 (timestamp 391+1020분)
- Recharts가 연속 시간축으로 인식 → 공백 발생

**인덱스 기반 (수정 후):**
- X축 = 데이터 순서 (0, 1, 2, ...)
- Candle 0 (9:00) → Candle 390 (15:30) → Candle 391 (다음날 9:00)
- Recharts가 연속 인덱스로 인식 → 공백 없음
- Tick formatter만 시간 표시 → 사용자에게는 시간으로 보임

**결론:** 내부는 인덱스, 표시는 시간 → 최상의 UX

---

## 📝 추가 개선 (선택사항)

1. **날짜 구분선:** 날짜가 바뀌는 지점에 ReferenceLine 추가
2. **거래시간 강조:** 9:00~15:30 영역 배경색 다르게
3. **실시간 업데이트:** 새 캔들 추가 시 `dataIndex` 자동 증가
4. **성능 최적화:** 가상 스크롤링 (대량 데이터)

---

## 📌 핵심 변경 사항 요약

| 구분 | 변경 전 | 변경 후 |
|------|---------|---------|
| **Backend Timestamp** | `"2025-10-03T09:00:00"` (naive) | `"2025-10-03T09:00:00+09:00"` (KST) |
| **X축 기준** | 시간 (milliseconds) | 인덱스 (0, 1, 2, ...) |
| **비거래시간 공백** | 있음 (17시간) | 없음 (연속 표시) |
| **초기 viewWindow** | 마지막 120개 (우측 밀집) | 중앙 또는 70% 지점 (균형) |
| **드래그 동작** | 축소 발생 | 정상 작동 |

---

## 🚀 다음 단계

1. ✅ 계획 검토 완료
2. ⏳ Backend timezone 수정
3. ⏳ Frontend 인덱스 기반 전환
4. ⏳ 통합 테스트
5. ⏳ 프로덕션 배포
