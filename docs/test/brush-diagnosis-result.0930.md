# Brush 드래그 이벤트 진단 결과

**날짜**: 2025-09-30  
**진단 도구**: Playwright  
**문제**: Brush 드래그 시 onChange 이벤트가 전혀 발생하지 않음

---

## 🔍 Playwright 진단 결과

### 1. Brush 요소 존재 확인
✅ **Brush 요소 발견**: 4개
- `recharts-layer recharts-brush` (위치: x=77.5, y=1495.5, 크기: 985x31)
- `recharts-brush-slide` (위치: x=83, y=1496, 크기: 974x30)
- `recharts-brush-traveller` (왼쪽, x=78)
- `recharts-brush-traveller` (오른쪽, x=1057)

### 2. Brush Slider 확인
❌ **Brush Slider 없음**: `.recharts-brush-slider` 클래스 미발견

### 3. Traveller 드래그 테스트
**테스트 시나리오**:
- 왼쪽 Traveller를 클릭 (x=81, y=1511)
- 왼쪽으로 303px 드래그 (x=-222)
- 30 steps로 부드럽게 이동

**결과**:
- ❌ `🔥 Brush onChange triggered` 로그 없음
- ❌ `[RechartsAdapter] Brush changed` 로그 없음  
- ❌ UI에 이벤트 로그 표시 없음
- ❌ 어떤 콘솔 로그도 발생하지 않음

---

## 🐛 근본 원인 분석

### 문제 1: Recharts Brush onChange가 작동하지 않음
**현상**:
```typescript
<Brush
  data={displayData}
  dataKey="time"
  startIndex={0}
  endIndex={60}
  onChange={(brushData: any) => {
    console.log('🔥 Brush onChange triggered:', brushData);  // ❌ 실행 안됨
    onBrushChange(brushData);
  }}
/>
```

**가능한 원인**:
1. **Recharts Brush 버그**: 특정 버전의 Recharts에서 Brush onChange가 작동하지 않는 알려진 이슈
2. **데이터 형식 문제**: Brush가 `time` dataKey를 제대로 인식하지 못함
3. **DOM 이벤트 전파 차단**: 다른 레이어가 Brush의 이벤트를 가로챔
4. **Brush 초기화 문제**: startIndex/endIndex 설정 시 onChange가 비활성화됨

### 문제 2: 커스텀 마우스 드래그와 충돌
RechartsAdapter에는 커스텀 마우스 드래그 핸들러가 구현되어 있음:
```typescript
onMouseDown={handleMouseDown}
onMouseMove={handleMouseMove}
onMouseUp={handleMouseUp}
```

이 핸들러들이 Brush의 드래그 이벤트를 가로채고 있을 가능성이 높음.

---

## ✅ 해결 방안

### 방안 1: 커스텀 드래그 비활성화 (권장)
Brush를 사용할 때는 차트의 커스텀 드래그를 비활성화:

```typescript
<div
  ref={containerRef}
  className="bg-[#0a0a0b] border border-gray-700 rounded-lg p-2"
  style={{ height, cursor: 'default' }}  // ✅ grab 제거
  // onMouseDown/Move/Up 제거
>
```

### 방안 2: Brush 영역 제외
Brush 영역에서만 커스텀 드래그를 비활성화:

```typescript
const handleMouseDown = useCallback((event: React.MouseEvent) => {
  // Brush 요소 클릭 시 무시
  const target = event.target as HTMLElement;
  if (target.closest('.recharts-brush')) {
    return;  // Brush는 자체 핸들러 사용
  }
  
  // 기존 드래그 로직...
}, []);
```

### 방안 3: 대체 라이브러리 사용
Recharts Brush 대신 다른 솔루션 고려:
- **Lightweight Charts**: 내장 TimeScale 네비게이션
- **TradingView Charts**: 강력한 범위 선택 기능
- **Custom Slider**: React 기반 커스텀 슬라이더 구현

---

## 📋 다음 단계

### 1단계: 방안 1 시도 (가장 빠름)
- 커스텀 드래그 핸들러 제거
- Brush onChange 작동 여부 확인

### 2단계: 방안 2 구현 (Brush와 드래그 공존)
- Brush 영역 감지 로직 추가
- Brush 외부에서만 커스텀 드래그 활성화

### 3단계: 대안 검토 (Recharts 문제 지속 시)
- Lightweight Charts로 마이그레이션 고려
- 커스텀 Range Selector 구현

---

## 🔬 추가 테스트 필요 사항

1. **Recharts 버전 확인**
   ```bash
   npm list recharts
   # 현재: recharts@3.2.1
   ```

2. **Brush 단독 테스트**
   - 간단한 예제로 Brush만 테스트
   - onChange가 작동하는지 확인

3. **다른 차트 라이브러리 PoC**
   - Lightweight Charts 드래그 동작 확인
   - ECharts datazoom 기능 테스트

---

## 📊 스크린샷

- `/tmp/brush-before-drag.png`: 초기 상태
- `/tmp/brush-traveller-drag.png`: 드래그 후 (변화 없음)

---

## 💡 권장 사항

**즉시 조치**:
1. 커스텀 드래그 핸들러를 조건부로 비활성화
2. Brush onChange 정상 작동 확인

**장기 해결책**:
- Recharts의 한계를 고려하여 Lightweight Charts로 마이그레이션 검토
- 전문 트레이딩 차트 라이브러리가 더 적합할 수 있음

---

**작성자**: Claude Code + Playwright  
**테스트 파일**: `tests/brush-traveller-drag.spec.ts`  
**최종 업데이트**: 2025-09-30
