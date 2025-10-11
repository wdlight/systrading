# 포트폴리오 차트 툴팁 버그 수정

**문제 발견일**: 2025-10-11
**심각도**: Low (UI 표시 오류)
**해결 상태**: ✅ 완료

---

## 🐛 문제 설명

### 증상
- Portfolio Performance 차트에서 마우스 오버 시 툴팁 표시
- KOSPI 라인에 마우스를 올려도 "Portfolio"로 표시됨
- 두 라인 모두 "Portfolio"로 잘못 표시

### 재현 조건
- http://localhost:9000 접속
- Portfolio Performance 차트에서 마우스 오버

---

## 🔍 원인 분석

### 버그 코드
`stock-trading-ui/src/components/trading/PortfolioPerformanceChart.tsx`

```typescript
// Line 37-40 (문제)
const tooltipFormatter = (value: number, name: string) => {
  const label = name === 'benchmark' ? 'KOSPI' : 'Portfolio';
  //                    ^^^^^^^^^^^
  //                    실제로는 'KOSPI'가 넘어옴
  return [formatCurrency(value), label];
};

// Line 88-89, 98-99 (실제 name 값)
<Line
  dataKey="portfolio"
  name="Portfolio"    // ← tooltipFormatter의 name 파라미터로 전달
  ...
/>
<Line
  dataKey="benchmark"
  name="KOSPI"        // ← tooltipFormatter의 name 파라미터로 전달
  ...
/>
```

### 핵심 문제
- `tooltipFormatter`의 `name` 파라미터는 `<Line>` 컴포넌트의 `name` prop 값
- `name === 'benchmark'` 조건은 **절대 참이 될 수 없음**
- 실제 name 값: `"Portfolio"` 또는 `"KOSPI"`

### 로직 흐름
```
1. Portfolio 라인: name = "Portfolio"
   → name === 'benchmark' ? false
   → label = 'Portfolio' ✅

2. KOSPI 라인: name = "KOSPI"
   → name === 'benchmark' ? false  ❌
   → label = 'Portfolio' ❌ (잘못됨!)
```

---

## ✅ 해결 방법

### 수정 코드

```typescript
// 수정 전 (버그)
const tooltipFormatter = (value: number, name: string) => {
  const label = name === 'benchmark' ? 'KOSPI' : 'Portfolio';
  return [formatCurrency(value), label];
};

// 수정 후 (정상)
const tooltipFormatter = (value: number, name: string) => {
  // name은 Line 컴포넌트의 name prop 값 ("Portfolio" 또는 "KOSPI")
  return [formatCurrency(value), name];
};
```

### 수정 이유
- Recharts의 `<Line name="...">` 값이 그대로 formatter의 `name` 파라미터로 전달됨
- 이미 Line 99에서 `name="KOSPI"`로 올바르게 설정되어 있음
- 불필요한 조건문 제거하고 `name` 값 그대로 사용

---

## 🧪 검증 방법

### 1. 브라우저에서 확인
```bash
# 프론트엔드 재시작
cd stock-trading-ui
npm run dev

# http://localhost:9000 접속
# Portfolio Performance 차트에서 마우스 오버
```

**예상 결과**:
- Portfolio 라인 (파란색): "Portfolio ₩101,456"
- KOSPI 라인 (회색): "KOSPI ₩101,456"

### 2. 개발자 도구 확인
```javascript
// Console에서 확인
// 1. Chart 컴포넌트 props 확인
// 2. Tooltip이 올바른 label을 표시하는지 확인
```

---

## 📚 관련 개념 설명

### Recharts Tooltip Formatter

**형식**:
```typescript
formatter: (value: number, name: string, props: any) => [ReactNode, ReactNode]
```

**파라미터**:
- `value`: 데이터 포인트의 값 (예: 101456)
- `name`: `<Line name="...">` prop의 값
- `props`: 추가 정보 (entry, dataKey 등)

**반환값**: `[표시할 값, 표시할 라벨]`

### 예시

```typescript
// 패턴 1: name 그대로 사용 (권장)
const formatter = (value: number, name: string) => {
  return [formatCurrency(value), name];
};

// 패턴 2: 조건부 변환
const formatter = (value: number, name: string) => {
  const label = name === 'Portfolio' ? '내 포트폴리오' : 'KOSPI 지수';
  return [formatCurrency(value), label];
};

// 패턴 3: dataKey 기반 (props 사용)
const formatter = (value: number, name: string, props: any) => {
  const label = props.dataKey === 'benchmark' ? 'KOSPI' : 'Portfolio';
  return [formatCurrency(value), label];
};
```

---

## 🎯 추가 개선 사항

### 벤치마크 정규화 설명 추가

현재 사용자가 혼란스러워하는 부분:
- "KOSPI가 101,456원이라고?"
- "왜 포트폴리오와 같은 값인가?"

**해결책**: 차트 아래에 설명 추가

```typescript
<div className="mt-2 text-xs text-gray-400">
  💡 벤치마크는 포트폴리오 시작 시점 기준으로 정규화되어 표시됩니다.
  (예: 포트폴리오 시작일에 KOSPI에 동일 금액을 투자했다면?)
</div>
```

### 툴팁 포맷 개선

더 명확한 정보 제공:

```typescript
const tooltipFormatter = (value: number, name: string) => {
  const percentage = name === 'KOSPI'
    ? '(+0.00%)' // 벤치마크 변화율 계산
    : '(+0.00%)'; // 포트폴리오 변화율 계산

  return [
    `${formatCurrency(value)} ${percentage}`,
    name
  ];
};
```

---

## 📝 교훈

1. **API 응답 확인**: 툴팁 버그를 찾기 전에 API 데이터부터 확인
2. **Recharts 동작 이해**: formatter의 `name` 파라미터가 `<Line name>`에서 온다는 것
3. **조건문 검증**: 하드코딩된 문자열 비교는 위험 (오타 가능성)
4. **단순함 유지**: 불필요한 조건문보다 직접 사용이 더 안전

---

**수정 완료**: 2025-10-11 16:10
**검증 완료**: 2025-10-11 16:11
**문서 작성**: 2025-10-11 16:12
