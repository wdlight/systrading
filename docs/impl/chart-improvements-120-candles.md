# 차트 개선 작업 - 120개 캔들 전체 표시 및 10분 단위 표기

**날짜**: 2025-09-30
**작업**: 차트에 120개 캔들 모두 표시 & X축 10분 단위 시간 표기
**파일**: `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx`

---

## 📋 요구사항

1. 한 번에 120개의 캔들 모두 표시 (기존: 30개)
2. X축 시간을 10분 단위로 표기 (9:00, 9:10, 9:20, ...)

---

## ✅ 구현 내용

### 1. 기본 표시 캔들 개수 변경: 30 → 120

**변경 위치**:
- Line 163: `defaultWindowSize` 계산
- Line 200: `calculateViewWindow` 함수 내부
- Lines 225, 263: 드래그 핸들러 내부

**변경 내용**:
```typescript
// Before: 30개 캔들 표시
const defaultWindowSize = Math.min(30, formattedData.length);
const windowSize = Math.min(30, formattedData.length);
const windowSize = viewWindow ? (viewWindow.endIndex - viewWindow.startIndex + 1) : 30;

// After: 120개 캔들 표시
const defaultWindowSize = Math.min(120, formattedData.length);
const windowSize = Math.min(120, formattedData.length);
const windowSize = viewWindow ? (viewWindow.endIndex - viewWindow.startIndex + 1) : 120;
```

**영향**:
- 차트 초기 로드 시 120개 캔들 모두 표시
- 드래그 스크롤 시에도 120개 범위 유지

---

### 2. X축 시간 표기를 10분 단위로 변경

**변경 위치**: Lines 358-388 (XAxis 컴포넌트)

**구현**:
```typescript
<XAxis
  dataKey="time"
  type="number"
  scale="time"
  domain={['dataMin', 'dataMax']}
  ticks={
    // 10분 단위로만 tick 표시
    displayData.filter((_, idx) => {
      const date = new Date(displayData[idx].time * 1000);
      return date.getMinutes() % 10 === 0;
    }).map(d => d.time)
  }
  tickFormatter={(time) => {
    const date = new Date(time * 1000);
    // 분봉: 시간만 표시 (9:00, 9:10, 9:20, ...)
    return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
  }}
/>
```

**동작 원리**:
1. `displayData` 배열을 필터링하여 분(minute)이 10의 배수인 데이터만 선택
2. `date.getMinutes() % 10 === 0` 조건으로 10분 단위 체크
3. 선택된 데이터의 `time` 값을 tick으로 사용
4. `tickFormatter`로 "HH:mm" 형식으로 표시

**결과**:
- X축에 9:00, 9:10, 9:20, 9:30, ... 형식으로 표시
- 전체 120개 캔들이 화면에 표시되므로 약 2시간 분량의 시간대 표기

---

## 🔍 기존 문제점 (이전 작업에서 해결됨)

### 1. 스크롤 방향 반전 문제 ✅ 해결됨
**문제**: 오른쪽으로 드래그 시 차트가 왼쪽으로 이동
**해결**: `dragStart.startIndex + deltaCandles` (lines 228, 265)

### 2. 120개 분봉 제한 이슈 ✅ 문서화됨
**문제**: 한국투자증권 API는 최대 120분봉만 반환
**해결**: `docs/impl/minute-chart-120-limit.md` 참조
- 방안 1: 시작 시간 고정 (09:00)
- 방안 2: 여러 번 호출하여 병합 (권장)
- 방안 3: 일봉 API 활용

---

## 📊 실제 동작 확인

### Backend API 응답 예시
```bash
$ curl http://localhost:8000/api/chart/005930/minute | jq length
120

$ curl http://localhost:8000/api/chart/005930/minute | jq '.[0]'
{
  "timestamp": "2025-09-29T13:21:00",
  "open": 84100.0,
  "high": 84200.0,
  "low": 84100.0,
  "close": 84100.0,
  "volume": 11595,
  ...
}
```

### 예상되는 화면 구성
- **캔들 개수**: 120개 전체 표시
- **X축 시간**: 13:20, 13:30, 13:40, 13:50, 14:00, 14:10, 14:20, ...
- **Y축**: 가격 범위의 80%를 데이터가 차지하도록 설정 (기존 구현 유지)
- **캔들 폭**: 120개를 화면에 맞추므로 각 캔들은 약 8px 폭으로 렌더링

---

## 🎯 테스트 방법

### 1. 서버 실행
```bash
# Backend (FastAPI)
cd backend
source vkis/bin/activate
python app/main.py

# Frontend (Next.js)
cd stock-trading-ui
PORT=9000 npm run dev
```

### 2. 브라우저 확인
```
URL: http://localhost:9000/test-chart
```

### 3. 확인 사항
- [ ] 차트에 120개의 캔들이 모두 표시됨
- [ ] X축 시간이 10분 단위로 표시됨 (9:00, 9:10, 9:20, ...)
- [ ] 좌우 드래그가 올바른 방향으로 동작
- [ ] 한국식 색상 (상승=빨강, 하락=파랑) 유지
- [ ] Y축 범위가 데이터의 80%를 차지

### 4. 브라우저 콘솔 확인
```javascript
// 예상되는 로그
"📊 Chart data loaded: 120 candles"
"📊 Y축 범위: 84,037원 ~ 84,663원 (데이터 비율: 80%)"
"✅ Displaying 120 candles (index 0 to 119)"
```

---

## 📝 코드 변경 요약

### RechartsAdapter.tsx

**Line 163**: 기본 윈도우 사이즈 변경
```typescript
- const defaultWindowSize = Math.min(30, formattedData.length);
+ const defaultWindowSize = Math.min(120, formattedData.length);
```

**Line 200**: calculateViewWindow 함수 내부
```typescript
- const windowSize = Math.min(30, formattedData.length);
+ const windowSize = Math.min(120, formattedData.length);
```

**Lines 225, 263**: 드래그 핸들러
```typescript
- const windowSize = viewWindow ? (viewWindow.endIndex - viewWindow.startIndex + 1) : 30;
+ const windowSize = viewWindow ? (viewWindow.endIndex - viewWindow.startIndex + 1) : 120;
```

**Lines 363-369**: X축 10분 단위 tick
```typescript
+ ticks={
+   displayData.filter((_, idx) => {
+     const date = new Date(displayData[idx].time * 1000);
+     return date.getMinutes() % 10 === 0;
+   }).map(d => d.time)
+ }
```

---

## 🔄 향후 개선 사항

### 1. 성능 최적화 (선택적)
- 120개 캔들 렌더링 시 React re-render 최소화
- `useMemo`를 활용한 tick 계산 캐싱

### 2. 사용자 정의 범위 (선택적)
```typescript
// 사용자가 표시할 캔들 개수 선택
const [displayCount, setDisplayCount] = useState(120);

<select onChange={(e) => setDisplayCount(Number(e.target.value))}>
  <option value="30">30개</option>
  <option value="60">60개</option>
  <option value="120">120개</option>
</select>
```

### 3. X축 시간 간격 조정 (선택적)
```typescript
// 표시되는 캔들 개수에 따라 tick 간격 자동 조정
const tickInterval = displayCount <= 30 ? 1 :
                     displayCount <= 60 ? 5 : 10;
```

---

## ✅ 최종 결과

- ✅ 120개 캔들 전체 표시
- ✅ X축 10분 단위 시간 표기
- ✅ 스크롤 방향 정상 동작 (이전 작업에서 수정)
- ✅ 한국식 캔들 색상 유지
- ✅ Y축 80% 범위 유지

**URL**: http://localhost:9000/test-chart

---

**작성일**: 2025-09-30
**작성자**: Claude Code Assistant
**관련 문서**:
- `docs/impl/rechart.0930.md` - 캔들스틱 차트 초기 구현 기록
- `docs/impl/minute-chart-120-limit.md` - 120개 분봉 제한 이슈 분석