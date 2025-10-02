# Brush 이벤트 테스트 가이드
**작성일**: 2025-09-30
**목적**: 왼쪽 드래그 시 Brush onChange 이벤트가 정상적으로 발생하는지 확인

---

## 🎯 테스트 목적

무한 스크롤 기능 구현을 위해 **Recharts Brush 컴포넌트의 onChange 이벤트**가 정상적으로 발생하는지 확인합니다.

특히 **왼쪽으로 드래그**했을 때:
- `startIndex`가 변경되는지
- `startIndex < 20`일 때 이전 데이터 로드 트리거가 작동하는지

---

## 📍 테스트 페이지 접속

### 1. 디버그 전용 페이지 (권장)
```
http://localhost:9000/debug-brush
```

**특징**:
- ✅ Brush 이벤트 실시간 로그 표시
- ✅ startIndex/endIndex 값 시각화
- ✅ startIndex < 20일 때 녹색 하이라이트
- ✅ 테스트 체크리스트 제공
- ✅ 문제 해결 가이드 포함

### 2. 무한 스크롤 통합 페이지
```
http://localhost:9000/test-infinite-scroll
```

**특징**:
- 실제 무한 스크롤 기능 통합
- 이전 날짜 자동 로드 테스트

---

## ✅ 테스트 절차

### Step 1: 페이지 접속 확인
1. 브라우저에서 `http://localhost:9000/debug-brush` 접속
2. 차트가 정상적으로 로드되는지 확인
3. "005930 (삼성전자)" 데이터가 표시되는지 확인
4. 캔들 개수가 100개 이상인지 확인

### Step 2: Brush 컴포넌트 확인
1. 차트 **하단**에 슬라이더(Brush) 확인
2. Brush 모양:
   - 회색 배경의 작은 차트
   - 드래그 가능한 윈도우 영역
   - 시간 눈금 표시

**예상 모습**:
```
┌─────────────────────────────────┐
│     [캔들스틱 차트 메인]          │
│                                 │
│                                 │
└─────────────────────────────────┘
┌─────────────────────────────────┐ ← Brush
│ ░░░░░░[    윈도우    ]░░░░░░░░░ │
│ 13:30    14:00    14:30    15:00│
└─────────────────────────────────┘
```

### Step 3: 왼쪽 드래그 테스트
1. Brush의 **윈도우 영역**을 마우스로 클릭
2. **왼쪽으로 드래그**
3. "Brush 이벤트 로그" 섹션에 새 항목 추가 확인

**예상 결과**:
```
🔍 Brush 이벤트 로그

┌─────────────────────────────────┐
│ 20:45:32                         │
│ startIndex: 45                   │
│ endIndex: 105                    │
│ range: 61                        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 20:45:30                         │
│ startIndex: 50                   │
│ endIndex: 110                    │
│ range: 61                        │
└─────────────────────────────────┘
```

### Step 4: 트리거 조건 확인
1. 계속 **왼쪽으로 드래그**하여 startIndex를 20 미만으로 만들기
2. **녹색 배경**으로 변경되는지 확인
3. "⚡ 이전 데이터 로드 트리거!" 메시지 확인

**예상 결과 (startIndex < 20)**:
```
┌─────────────────────────────────┐ ← 녹색 배경!
│ 20:45:35                         │
│ ⚡ 이전 데이터 로드 트리거!        │
│ startIndex: 18                   │
│ endIndex: 78                     │
│ range: 61                        │
└─────────────────────────────────┘
```

### Step 5: 콘솔 로그 확인
1. **브라우저 개발자 도구 열기**:
   - Chrome/Edge: `F12` 또는 `Ctrl+Shift+I`
   - Mac: `Cmd+Option+I`
2. **Console 탭** 선택
3. `🔥 Brush Event` 로그 확인

**예상 콘솔 출력**:
```javascript
🔥 Brush Event: {
  time: "20:45:32",
  startIndex: 45,
  endIndex: 105
}

[RechartsAdapter] Brush changed: {
  startIndex: 45,
  endIndex: 105,
  totalData: 120
}

[InfiniteScroll] Auto-loading previous day, startIndex: 18
```

---

## 🐛 문제 발생 시 체크리스트

### ❌ Problem 1: Brush가 보이지 않음

**증상**:
- 차트 하단에 슬라이더가 없음
- 차트만 크게 표시됨

**원인 및 해결**:
```typescript
// ✅ 확인 1: RechartsAdapter.tsx에 Brush import 확인
import { Brush } from 'recharts';

// ✅ 확인 2: ComposedChart 내부에 Brush 컴포넌트 존재 확인
<ComposedChart data={displayData}>
  {/* ... 다른 컴포넌트들 ... */}

  <Brush
    dataKey="time"
    height={30}
    stroke={KOREAN_CHART_THEME.gridColor}
    fill={KOREAN_CHART_THEME.backgroundColor}
    onChange={(brushData: any) => {
      // onChange 핸들러
    }}
  />
</ComposedChart>
```

**해결 방법**:
```bash
# 파일 확인
grep -n "Brush" stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx

# 예상 출력:
# 14:  Brush,                           <- import 문
# 402:  <Brush                          <- Brush 컴포넌트
```

---

### ❌ Problem 2: Brush는 보이지만 이벤트가 발생하지 않음

**증상**:
- Brush를 드래그해도 로그에 아무것도 표시되지 않음
- 콘솔에도 로그 없음

**원인 및 해결**:
```typescript
// ✅ 확인 1: onChange prop 연결 확인
<Brush
  onChange={(brushData: any) => {
    if (onBrushChange && brushData) {
      const { startIndex, endIndex } = brushData;
      console.log('[RechartsAdapter] Brush changed:', { startIndex, endIndex });
      onBrushChange({ startIndex, endIndex });
    }
  }}
/>

// ✅ 확인 2: ChartAdapterProps에 onBrushChange 정의 확인
export interface ChartAdapterProps {
  chartData: ChartCandle[];
  height?: number;
  timeframe: string;
  onError?: (error: string) => void;
  onBrushChange?: (indices: { startIndex: number; endIndex: number }) => void;  // ← 이것!
}

// ✅ 확인 3: 부모 컴포넌트에서 props 전달 확인
<ChartSelector
  library="recharts"
  chartData={candles}
  onBrushChange={handleBrushChange}  // ← 이것!
/>
```

**해결 방법**:
```bash
# 브라우저 콘솔에서 직접 테스트
# 1. Elements 탭에서 Brush 요소 찾기
# 2. Console에서 이벤트 리스너 확인
getEventListeners($0)  # $0은 선택된 요소
```

---

### ❌ Problem 3: 이벤트는 발생하지만 startIndex가 항상 같음

**증상**:
- Brush를 드래그해도 startIndex 값이 변하지 않음
- 항상 0이거나 고정된 값

**원인**:
- Brush의 데이터 범위 설정 문제
- dataKey가 잘못 설정됨

**해결**:
```typescript
// ❌ 잘못된 설정
<Brush dataKey="index" />  // 인덱스 필드가 없음

// ✅ 올바른 설정
<Brush
  dataKey="time"  // 실제 존재하는 데이터 키
  startIndex={0}  // 초기 시작 인덱스
  endIndex={Math.min(60, displayData.length - 1)}  // 초기 끝 인덱스
/>
```

---

### ❌ Problem 4: 드래그가 안 됨

**증상**:
- Brush를 클릭해도 움직이지 않음
- 마우스 커서가 변하지 않음

**가능한 원인**:
1. **데이터 부족**: 캔들 개수가 너무 적음 (< 20개)
2. **CSS 간섭**: 다른 요소가 Brush를 덮고 있음
3. **z-index 문제**: Brush가 다른 레이어 뒤에 숨김

**해결**:
```typescript
// 해결 1: 최소 데이터 확인
if (chartData.length < 50) {
  console.warn('캔들 개수가 부족합니다. 최소 50개 권장');
}

// 해결 2: Brush에 스타일 추가
<Brush
  dataKey="time"
  height={30}
  style={{ zIndex: 100 }}  // z-index 명시
  travelerWidth={10}  // 드래그 핸들 크기 증가
/>
```

---

### ❌ Problem 5: TypeScript 에러

**증상**:
```
Property 'onBrushChange' does not exist on type 'ChartAdapterProps'
```

**해결**:
```typescript
// stock-trading-ui/src/components/trading/chart-adapters/ChartAdapter.tsx
export interface ChartAdapterProps {
  chartData: ChartCandle[];
  height?: number;
  timeframe: string;
  onError?: (error: string) => void;
  onBrushChange?: (indices: { startIndex: number; endIndex: number }) => void;  // 추가
}
```

---

## 📊 정상 작동 시 예상 동작

### 1. 초기 로드
```
✓ 차트 로드 완료
✓ 120개 캔들 표시
✓ Brush 하단에 표시
✓ 초기 윈도우: startIndex=0, endIndex=60
```

### 2. 왼쪽 드래그
```
→ Brush를 왼쪽으로 드래그
→ onChange 이벤트 발생
→ startIndex 감소: 60 → 50 → 40 → 30 → 20 → 18
→ 로그에 실시간 표시
```

### 3. 트리거 발동
```
→ startIndex < 20 감지
→ 녹색 배경으로 변경
→ "⚡ 이전 데이터 로드 트리거!" 표시
→ (무한 스크롤 페이지에서는 실제 API 호출)
```

### 4. 콘솔 로그
```javascript
🔥 Brush Event: { time: "20:45:35", startIndex: 18, endIndex: 78 }
[RechartsAdapter] Brush changed: { startIndex: 18, endIndex: 78, totalData: 120 }
[InfiniteScroll] Auto-loading previous day, startIndex: 18
[ChartAPI] Fetching candles: { stockCode: "005930", date: "2025-09-29" }
```

---

## 🔧 디버깅 명령어

### 백엔드 확인
```bash
# API 엔드포인트 테스트
curl http://localhost:8000/api/chart/005930/minute?date=2025-09-30 | jq '.[0:3]'

# 캐시 파일 확인
ls -lh backend/kordata/005930/

# 백엔드 로그 확인
tail -f backend/backend.log
```

### 프론트엔드 확인
```bash
# Next.js 개발 서버 로그
# 터미널에서 실행 중인 npm run dev 출력 확인

# 빌드 에러 확인
cd stock-trading-ui
npm run build

# TypeScript 에러 확인
npx tsc --noEmit
```

### 브라우저 디버깅
```javascript
// 콘솔에서 실행

// 1. Brush 요소 찾기
document.querySelector('.recharts-brush')

// 2. 이벤트 리스너 확인
getEventListeners(document.querySelector('.recharts-brush'))

// 3. React DevTools에서 컴포넌트 props 확인
// React DevTools 확장 프로그램 설치 필요
```

---

## ✅ 테스트 완료 기준

다음 모든 항목이 확인되면 테스트 완료:

- [ ] Brush 컴포넌트가 차트 하단에 표시됨
- [ ] Brush를 왼쪽으로 드래그할 수 있음
- [ ] 드래그 시 "Brush 이벤트 로그"에 새 항목 추가됨
- [ ] startIndex 값이 드래그에 따라 변경됨
- [ ] startIndex < 20일 때 녹색 배경으로 표시됨
- [ ] 콘솔에 `🔥 Brush Event` 로그 출력됨
- [ ] 콘솔에 `[RechartsAdapter] Brush changed` 로그 출력됨
- [ ] (무한 스크롤 페이지) startIndex < 20일 때 이전 데이터 자동 로드됨

---

## 📝 테스트 결과 보고

테스트 완료 후 다음 정보를 기록:

```markdown
### 테스트 결과

**날짜**: 2025-09-30
**테스터**: [이름]
**브라우저**: Chrome 130.0 / Firefox 132.0 / Safari 17.0

#### 체크리스트
- [x] Brush 컴포넌트 표시
- [x] 왼쪽 드래그 가능
- [x] 이벤트 로그 표시
- [x] startIndex 변경 확인
- [x] 트리거 조건 (startIndex < 20) 확인
- [x] 콘솔 로그 확인

#### 발견된 문제
1. [문제 설명]
   - 증상: ...
   - 재현 방법: ...
   - 스크린샷: ...

2. [문제 설명]
   - ...

#### 스크린샷
![Brush 이벤트 로그](./screenshots/brush-events.png)
![콘솔 로그](./screenshots/console-logs.png)
```

---

## 🚀 다음 단계

테스트가 성공적으로 완료되면:

1. **무한 스크롤 통합 테스트**
   - `/test-infinite-scroll` 페이지에서 실제 데이터 로드 확인
   - 이전 거래일 데이터 로드 확인
   - 캐시 동작 확인

2. **E2E 테스트 작성**
   ```typescript
   // tests/brush-infinite-scroll.spec.ts
   test('infinite scroll loads previous data', async ({ page }) => {
     await page.goto('/test-infinite-scroll');

     const brush = page.locator('.recharts-brush');
     await brush.drag({ x: -200, y: 0 });

     await expect(page.locator('[data-testid="date-range"]'))
       .toContainText('2025-09-29');
   });
   ```

3. **프로덕션 배포**
   - TypeScript 에러 수정
   - 성능 최적화
   - 문서화 완료

---

**작성자**: Claude Code
**문서 버전**: 1.0
**최종 업데이트**: 2025-09-30