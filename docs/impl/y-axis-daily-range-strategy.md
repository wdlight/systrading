# Y축 일별 최고/최저 기준 90% 범위 전략

**작성일**: 2025-10-02
**목적**: 일별 최고점/최저점 기준으로 Y축을 고정하여 캔들 가시성 확보

---

## 📊 전략 변경 배경

### 기존 문제점 (시초가 기준 ±30%)
```
시초가: 60,000원
Y축 범위: 42,000 ~ 78,000원 (36,000원 범위)

실제 가격 변동: 59,500 ~ 60,500원 (1,000원 범위)
→ 캔들이 너무 작아서 가시성 저하
→ 실제 변동폭의 36배나 넓은 Y축 범위
```

### 새로운 접근 (일별 최고/최저 기준 90%)
```
실제 최저: 59,500원
실제 최고: 60,500원
가격 범위: 1,000원

패딩(5%): 50원 (상하 각각)
Y축 범위: 59,450 ~ 60,550원 (1,100원 범위)

→ 캔들이 화면의 90%를 차지
→ 가격 변동이 명확하게 보임
```

---

## 🎯 새로운 전략

### 핵심 원칙
1. **실제 데이터 기준**: 당일 전체 데이터의 최고/최저점 사용
2. **90% 가시성**: 캔들이 Y축 범위의 90%를 차지하도록 패딩
3. **상하 5% 여유**: 실제 범위에서 상하 각 5%씩 패딩 추가
4. **호가 단위 정렬**: 깔끔한 Y축 라벨을 위한 호가 단위 반올림

### 계산 공식
```typescript
// 1. 실제 가격 범위
actualMin = Math.min(...모든_저가);
actualMax = Math.max(...모든_고가);
priceRange = actualMax - actualMin;

// 2. 패딩 계산 (5%)
padding = priceRange * 0.05;

// 3. Y축 범위
rawLowerLimit = actualMin - padding;
rawUpperLimit = actualMax + padding;

// 4. 호가 단위 정렬
finalLowerLimit = Math.floor(rawLowerLimit / tickUnit) * tickUnit;
finalUpperLimit = Math.ceil(rawUpperLimit / tickUnit) * tickUnit;
```

---

## 💻 구현 코드

### RechartsAdapter.tsx (Lines 345-383)

```typescript
// 🎯 Y축 고정: 일별 최고/최저점 기준 90% 범위
const yDomain = useMemo(() => {
  if (!formattedData || formattedData.length === 0) {
    return [0, 0] as [number, number];
  }

  // ✅ 당일 전체 데이터의 실제 가격 범위 계산
  const actualPrices = formattedData.flatMap(d => [d.high, d.low]);
  const actualMin = Math.min(...actualPrices);
  const actualMax = Math.max(...actualPrices);

  // 가격 범위 계산
  const priceRange = actualMax - actualMin;

  // 90% 범위로 여유 공간 확보 (상하 각 5% 패딩)
  // 실제 범위의 상하에 5%씩 여유를 둠
  const padding = priceRange * 0.05;
  const rawLowerLimit = actualMin - padding;
  const rawUpperLimit = actualMax + padding;

  // 호가 단위 기준으로 Y축 범위를 깔끔하게 정렬
  const avgPrice = (actualMin + actualMax) / 2;
  const tickUnit = getTickUnitByPrice(avgPrice);

  const finalLowerLimit = Math.floor(rawLowerLimit / tickUnit) * tickUnit;
  const finalUpperLimit = Math.ceil(rawUpperLimit / tickUnit) * tickUnit;

  console.log('📊 Y축 고정 (일별 최고/최저 기준 90% 범위):', {
    actualMin: actualMin.toLocaleString(),
    actualMax: actualMax.toLocaleString(),
    priceRange: priceRange.toLocaleString(),
    padding: `${(padding).toFixed(0)} (5%)`,
    tickUnit,
    finalRange: `${finalLowerLimit.toLocaleString()} ~ ${finalUpperLimit.toLocaleString()}`,
    rangeRatio: ((finalUpperLimit - finalLowerLimit) / priceRange).toFixed(2)
  });

  return [finalLowerLimit, finalUpperLimit] as [number, number];
}, [formattedData]); // xDomain 의존성 제거 → drag해도 Y축 불변
```

---

## 📈 실제 예시

### 예시 1: 소폭 변동 (삼성전자 일반 거래일)
```javascript
실제 가격 변동:
- 최저: 59,500원
- 최고: 60,500원
- 범위: 1,000원

Y축 계산:
- 패딩: 50원 (5%)
- Y축: 59,450 ~ 60,550원
- 총 범위: 1,100원

결과:
→ 캔들이 화면의 90% 차지
→ 가격 변동이 명확하게 보임
```

### 예시 2: 큰 변동 (급등/급락)
```javascript
실제 가격 변동:
- 최저: 55,000원
- 최고: 65,000원
- 범위: 10,000원

Y축 계산:
- 패딩: 500원 (5%)
- Y축: 54,500 ~ 65,500원
- 총 범위: 11,000원

결과:
→ 큰 변동도 90% 가시성 유지
→ 패딩으로 상하 여유 확보
```

### 예시 3: 호가 단위 정렬
```javascript
원시 계산:
- rawLowerLimit: 59,487원
- rawUpperLimit: 60,513원

호가 단위 적용 (tickUnit = 50):
- finalLowerLimit: 59,450원 (59,487 내림)
- finalUpperLimit: 60,550원 (60,513 올림)

결과:
→ Y축 라벨이 깔끔하게 표시
→ 50원 단위로 정렬됨
```

---

## 🔄 기존 전략과 비교

| 항목 | 기존 (시초가 ±30%) | 개선 (일별 최고/최저 90%) |
|------|-------------------|------------------------|
| 기준 | 시초가 | 실제 최고/최저점 |
| 범위 | 고정 ±30% | 실제 변동 + 5% 패딩 |
| 가시성 | 낮음 (캔들 작음) | 높음 (캔들 90%) |
| 적응성 | 변동폭 무시 | 변동폭 반영 |
| 사용성 | 상한가/하한가 맥락 | 실제 가격 변동 명확 |

---

## ✅ 장점

### 1. **가시성 대폭 개선**
- 캔들이 화면의 90%를 차지
- 작은 가격 변동도 명확하게 보임
- 실시간 변화 파악 용이

### 2. **적응형 범위**
- 소폭 변동: 좁은 Y축 범위로 확대
- 큰 변동: 넓은 Y축 범위로 전체 표시
- 자동으로 최적의 범위 설정

### 3. **일관된 가시성**
- 변동폭과 무관하게 항상 90% 가시성 유지
- 다양한 종목/시나리오에서 동일한 UX

### 4. **호가 단위 정렬**
- Y축 라벨이 깔끔하게 표시
- 가격대별 적절한 단위 자동 적용

---

## ⚠️ 주의사항

### 1. **극단적 케이스**
**문제**: 가격이 거의 변하지 않는 경우
```javascript
실제 범위: 60,000 ~ 60,010원 (10원 변동)
패딩: 0.5원 (5%)
Y축: 59,999.5 ~ 60,010.5원
```

**대응**: 최소 범위 설정 고려
```typescript
const minRange = tickUnit * 10; // 최소 10 호가 단위
const adjustedRange = Math.max(priceRange, minRange);
```

### 2. **Drag 시 Y축 변경?**
**현재**: `formattedData` 전체 기준 → drag해도 Y축 불변
**대안**: `visibleData` 기준 → drag 시 Y축 변경 (동적 확대/축소)

**권장**: 현재 구현 유지 (일별 고정)
- 일관된 가격 스케일 유지
- 드래그 시 안정성
- 전체 맥락 파악 용이

### 3. **패딩 비율 조정**
**현재**: 5% 패딩 (90% 가시성)
**조정 가능**:
- 10% 패딩 → 80% 가시성 (더 여유롭게)
- 2.5% 패딩 → 95% 가시성 (더 타이트하게)

---

## 🧪 테스트 검증

### Console 로그 확인
```javascript
📊 Y축 고정 (일별 최고/최저 기준 90% 범위): {
  actualMin: "59,500",
  actualMax: "60,500",
  priceRange: "1,000",
  padding: "50 (5%)",
  tickUnit: 50,
  finalRange: "59,450 ~ 60,550",
  rangeRatio: "1.10"  // Y축 범위 / 실제 범위 = 1.1배 (90% 가시성)
}
```

### 검증 항목
- [ ] `rangeRatio`가 약 1.1 (90% + 10% 패딩)
- [ ] 캔들이 화면의 대부분을 차지
- [ ] Y축 라벨이 호가 단위로 정렬
- [ ] Drag 시 Y축 불변

---

## 📊 성능 및 UX

### 성능
- **계산 복잡도**: O(n) - 전체 데이터 스캔
- **useMemo 캐싱**: formattedData 변경 시에만 재계산
- **Drag 성능**: Y축 재계산 없음 (의존성 제거)

### 사용자 경험
- **가시성**: ⭐⭐⭐⭐⭐ (매우 우수)
- **일관성**: ⭐⭐⭐⭐⭐ (drag 시 불변)
- **적응성**: ⭐⭐⭐⭐⭐ (변동폭 반영)
- **가독성**: ⭐⭐⭐⭐⭐ (호가 단위 정렬)

---

## 🔧 향후 개선 가능 옵션

### Option 1: 최소 범위 보장
```typescript
const minRange = tickUnit * 20; // 최소 20 호가 단위
const adjustedRange = Math.max(priceRange, minRange);
const padding = adjustedRange * 0.05;
```

### Option 2: 패딩 비율 설정
```typescript
const PADDING_RATIO = 0.05; // 5% (설정 가능)
const padding = priceRange * PADDING_RATIO;
```

### Option 3: 동적 Y축 (Drag 시 확대/축소)
```typescript
// visibleData 기준으로 Y축 계산
const visiblePrices = visibleData.flatMap(d => [d.high, d.low]);
// → Drag 시 Y축 변경 (확대/축소 효과)
```

---

## 📝 관련 파일

- **구현**: `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx:345-383`
- **Utils**: `stock-trading-ui/src/lib/utils.ts:371-379` (getTickUnitByPrice)
- **기존 문서**: `docs/impl/y-axis-fixed-range-implementation.md`

---

## 🎓 학습 포인트

### 1. 데이터 기반 UI 설계
- 실제 데이터 범위를 분석하여 적절한 표시 범위 설정
- 이론적 범위(±30%)보다 실제 사용성 우선

### 2. 적응형 알고리즘
- 고정 비율이 아닌 실제 변동폭에 따른 동적 조정
- 다양한 시나리오에 대응 가능한 유연성

### 3. 성능과 UX의 균형
- useMemo로 불필요한 재계산 방지
- Drag 시 Y축 불변으로 안정성 확보
- 90% 가시성으로 최적의 사용자 경험
