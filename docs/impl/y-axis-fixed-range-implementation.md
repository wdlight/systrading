# Y축 고정 범위 구현 - 시초가 기준 ±30%

**작성일**: 2025-10-02
**목적**: 분봉 차트 Y축을 시초가 기준 ±30% 범위로 고정하여 drag 시 Y축 변동 방지

---

## 📊 구현 배경

### 문제점
- **기존**: 차트를 drag할 때마다 보이는 영역(xDomain)의 가격 범위에 따라 Y축이 동적으로 변경
- **결과**:
  - 드래그 시 가격 비율이 계속 변경되어 시각적 혼란
  - 상한가/하한가 맥락 파악 어려움
  - 일관된 가격 스케일 유지 불가

### 요구사항
1. 시초가 기준으로 Y축 범위 고정
2. 한국 주식 시장의 상한가/하한가(±30%) 범위 반영
3. drag 시에도 Y축 불변 유지
4. 일별(daily) 차트에 대해 고정 범위 적용

---

## 🎯 구현 전략

### 핵심 원칙
```
시초가 = chartData[0].open  // 당일 첫 캔들의 시가
Y축 최소값 = 시초가 × 0.70  // 하한가 (-30%)
Y축 최대값 = 시초가 × 1.30  // 상한가 (+30%)
```

### 기술적 접근
1. **시초가 추출**: 정렬된 분봉 데이터의 첫 번째 캔들의 `open` 값
2. **고정 범위 계산**: ±30% 범위 계산 후 정수로 반올림
3. **의존성 제거**: `xDomain` 의존성 제거하여 drag 시 재계산 방지

---

## 💻 코드 변경

### 파일: `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx`

**변경 위치**: Lines 345-366

#### Before (동적 Y축)
```typescript
const yDomain = useMemo(() => {
  if (!formattedData || formattedData.length === 0) {
    return [0, 0] as [number, number];
  }

  // ❌ 현재 보이는 영역(xDomain)의 데이터만 기준으로 Y축 계산
  const [xMin, xMax] = xDomain;
  const visibleData = formattedData.filter(d => d.time >= xMin && d.time <= xMax);

  if (visibleData.length === 0) {
    // fallback: 전체 데이터 기준
    const prices = formattedData.flatMap(d => [d.open, d.high, d.low, d.close]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const padding = (maxPrice - minPrice) * 0.1;
    return [Math.floor(minPrice - padding), Math.ceil(maxPrice + padding)] as [number, number];
  }

  // Y-domain은 현재 보이는 영역의 가격 기준
  const prices = visibleData.flatMap(d => [d.open, d.high, d.low, d.close]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1;
  const calculatedYDomain: [number, number] = [Math.floor(minPrice - padding), Math.ceil(maxPrice + padding)];

  return calculatedYDomain;
}, [formattedData, xDomain]); // ❌ xDomain 의존
```

#### After (고정 Y축)
```typescript
// 🎯 Y축 고정: 시초가 기준 ±30% 범위 (상한가/하한가)
const yDomain = useMemo(() => {
  if (!formattedData || formattedData.length === 0) {
    return [0, 0] as [number, number];
  }

  // ✅ 시초가 = 당일 첫 캔들의 open 가격
  const openingPrice = formattedData[0].open;

  // 한국 주식 시장 상한가/하한가 ±30% 범위
  const lowerLimit = Math.floor(openingPrice * 0.70);
  const upperLimit = Math.ceil(openingPrice * 1.30);

  console.log('📊 Y축 고정 (시초가 기준 ±30%):', {
    openingPrice,
    lowerLimit,
    upperLimit,
    range: `${lowerLimit.toLocaleString()} ~ ${upperLimit.toLocaleString()}`
  });

  return [lowerLimit, upperLimit] as [number, number];
}, [formattedData]); // ✅ xDomain 의존성 제거 → drag해도 Y축 불변
```

---

## 📋 주요 변경 사항

### 1. 시초가 기준 계산 (Line 352)
```typescript
const openingPrice = formattedData[0].open;
```
- 정렬된 분봉 데이터의 첫 번째 캔들이 시초가(9:00 첫 거래)
- Backend에서 시간순 정렬된 데이터를 받으므로 신뢰 가능

### 2. 상한가/하한가 계산 (Lines 355-356)
```typescript
const lowerLimit = Math.floor(openingPrice * 0.70);  // 하한가
const upperLimit = Math.ceil(openingPrice * 1.30);   // 상한가
```
- 한국 주식 시장의 ±30% 제한 범위 반영
- `Math.floor/ceil`로 정수 가격 보장

### 3. 의존성 제거 (Line 366)
```typescript
}, [formattedData]); // xDomain 제거
```
- **Before**: `[formattedData, xDomain]` → drag 시 xDomain 변경으로 yDomain 재계산
- **After**: `[formattedData]` → 데이터 변경 시에만 yDomain 재계산

---

## ✅ 예상 효과

### 1. 시각적 안정성
- drag 시 Y축 고정으로 가격 비율 일관성 유지
- 캔들의 상대적 크기가 변하지 않아 패턴 분석 용이

### 2. 상한가/하한가 맥락 제공
- ±30% 범위가 항상 표시되어 현재 가격의 위치 파악 가능
- 급등/급락 여부를 직관적으로 판단 가능

### 3. 성능 개선
- drag 이벤트 시 yDomain 재계산 불필요
- 불필요한 리렌더링 감소

---

## 🧪 테스트 시나리오

### 시나리오 1: 정상 거래 범위
**조건**: 삼성전자 시초가 60,000원
- **Y축 범위**: 42,000원 ~ 78,000원
- **테스트**: 차트 drag 시 Y축 범위 불변 확인

### 시나리오 2: 상한가 근접
**조건**: 가격이 시초가 대비 +25% 상승
- **예상**: 78,000원(상한가) 근처까지 캔들 표시
- **테스트**: Y축 범위 내 모든 캔들 표시 확인

### 시나리오 3: 하한가 근접
**조건**: 가격이 시초가 대비 -25% 하락
- **예상**: 42,000원(하한가) 근처까지 캔들 표시
- **테스트**: Y축 범위 내 모든 캔들 표시 확인

---

## 🔧 추가 개선 고려사항

### Option 1: 호가 단위 반영
```typescript
import { getTickUnitByPrice } from '@/lib/utils';

const tickUnit = getTickUnitByPrice(openingPrice);
const lowerLimit = Math.floor(openingPrice * 0.70 / tickUnit) * tickUnit;
const upperLimit = Math.ceil(openingPrice * 1.30 / tickUnit) * tickUnit;
```
- Y축 범위를 호가 단위에 맞춰 정렬
- 더 깔끔한 가격 표시 가능

### Option 2: 실제 범위 검증
```typescript
const actualPrices = formattedData.flatMap(d => [d.high, d.low]);
const actualMin = Math.min(...actualPrices);
const actualMax = Math.max(...actualPrices);

// 실제 범위가 ±30%를 벗어나면 확장
const lowerLimit = Math.min(Math.floor(openingPrice * 0.70), actualMin);
const upperLimit = Math.max(Math.ceil(openingPrice * 1.30), actualMax);
```
- 극단적 가격 변동 시 자동 범위 확장
- 데이터 손실 방지

### Option 3: 전날 종가 기준
```typescript
// Backend에서 전날 종가를 metadata로 전달 시
const previousClose = metadata?.previousClose || formattedData[0].open;
const lowerLimit = Math.floor(previousClose * 0.70);
const upperLimit = Math.ceil(previousClose * 1.30);
```
- 전날 종가 기준으로 상한가/하한가 계산
- 시초가가 갭(gap)으로 시작할 경우 더 정확

---

## ⚠️ 주의사항

### 1. 시초가 데이터 정확성
- **필수**: 첫 번째 캔들이 9:00 시초가여야 함
- **Backend 검증**: `chart.py`에서 시간순 정렬 확인
- **데이터 무결성**: 시초가 누락 시 오류 발생 가능

### 2. 극단적 가격 변동
- ±30% 범위를 실제로 벗어나는 경우 (서킷 브레이커 등)
- Option 2의 실제 범위 검증으로 대응 가능

### 3. 일봉 vs 분봉
- **현재 구현**: 분봉 데이터에 최적화
- **일봉 적용 시**: 동일한 로직 사용 가능 (첫 캔들 = 당일 시가)

---

## 📊 실행 결과 예시

### Console 출력
```
📊 Y축 고정 (시초가 기준 ±30%): {
  openingPrice: 60000,
  lowerLimit: 42000,
  upperLimit: 78000,
  range: '42,000 ~ 78,000'
}
```

### 사용자 경험
1. **차트 로드**: 시초가 기준 ±30% Y축 표시
2. **Drag 좌측**: 과거 데이터 조회, Y축 고정 유지
3. **Drag 우측**: 최신 데이터 조회, Y축 고정 유지
4. **시각적 일관성**: 모든 캔들의 상대적 크기 동일 유지

---

## 🚀 배포 및 운영

### Frontend 서버 재시작
```bash
cd stock-trading-ui
npm run dev
```

### 접속 URL
- **메인 대시보드**: http://localhost:9000
- **테스트 차트**: http://localhost:9000/test-chart

### 확인 사항
- [ ] Y축이 시초가 기준 ±30% 범위로 고정됨
- [ ] drag 시 Y축 범위 불변
- [ ] 모든 캔들이 범위 내 표시
- [ ] Console에 Y축 범위 로그 출력

---

## 📝 관련 파일

- **Frontend**: `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx`
- **Backend**: `backend/app/api/chart.py` (데이터 정렬 확인)
- **Hook**: `stock-trading-ui/src/hooks/useRealChartData.ts` (데이터 제공)
- **Utils**: `stock-trading-ui/src/lib/utils.ts` (getTickUnitByPrice)

---

## 🎓 학습 포인트

### React useMemo 의존성 관리
- 의존성 배열에서 불필요한 값 제거로 성능 개선
- drag 이벤트와 Y축 계산 분리로 안정성 확보

### 한국 주식 시장 특성
- 상한가/하한가 ±30% 제도
- 시초가 기준 가격 범위 설정의 중요성

### 차트 UX 설계
- 고정 Y축이 사용자 경험에 미치는 영향
- 일관된 시각적 스케일의 중요성
