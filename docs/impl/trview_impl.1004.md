# 📊 TradingView 차트 구현 작업 보고서 (2025-10-04)

`docs/trview-implementation-plan.md` (v2) 설계에 기반하여 TradingView Lightweight Charts 샘플 페이지 구현을 완료했습니다. 이 문서는 새로 생성된 파일과 각 파일의 역할, 주요 함수에 대해 요약합니다.

---

## 📂 생성된 파일 목록

- `stock-trading-ui/src/lib/tradingview/types.ts`
- `stock-trading-ui/src/lib/tradingview/chartConfig.ts`
- `stock-trading-ui/src/lib/tradingview/dataConverter.ts`
- `stock-trading-ui/src/hooks/useTRViewChart.ts`
- `stock-trading-ui/src/components/trading/TRViewChartControls.tsx`
- `stock-trading-ui/src/components/trading/TRViewChart.tsx`
- `stock-trading-ui/src/app/trview/page.tsx`
- `stock-trading-ui/__tests__/lib/tradingview/dataConverter.test.ts`

---

## 📄 파일별 상세 설명

### 1. `lib/tradingview/types.ts`

- **개요**: TradingView 차트에 사용될 데이터의 TypeScript 타입을 정의하는 파일입니다.
- **주요 타입**:
    - `TRViewCandleData`: 차트의 캔들스틱 시리즈에 필요한 데이터 형식 (time, open, high, low, close)을 정의합니다.
    - `TRViewVolumeData`: 거래량 히스토그램 시리즈에 필요한 데이터 형식 (time, value, color)을 정의합니다.

### 2. `lib/tradingview/chartConfig.ts`

- **개요**: 차트의 시각적 스타일(다크 테마)과 레이아웃 옵션을 중앙에서 관리하는 설정 파일입니다.
- **주요 함수**:
    - `getTRViewChartOptions()`: 차트 배경, 텍스트 색상, 그리드, Crosshair 등 기본 스타일 설정을 반환합니다.

### 3. `lib/tradingview/dataConverter.ts`

- **개요**: 백엔드 API로부터 받은 `ChartCandle` 데이터를 TradingView 차트 라이브러리가 요구하는 형식으로 변환하는 유틸리티 함수를 포함합니다.
- **주요 함수**:
    - `convertToTRViewCandles()`: 백엔드 `timestamp` (ISO 8601)를 차트가 사용하는 `UTCTimestamp` (초 단위)로 변환하고 캔들 데이터를 매핑합니다.
    - `convertToTRViewVolumes()`: 거래량 데이터를 변환하고, 이전 종가와 비교하여 상승/하락에 따라 거래량 막대의 색상을 지정합니다.

### 4. `hooks/useTRViewChart.ts`

- **개요**: 특정 종목 코드의 차트 데이터를 백엔드 API로부터 비동기적으로 가져오는 React 커스텀 훅입니다.
- **주요 함수**:
    - `useTRViewChart()`: `stockCode`를 인자로 받아 데이터 로딩 상태(`isLoading`), 에러(`error`), 그리고 최종 차트 데이터(`chartData`)를 반환하여 UI와 로직을 분리합니다.

### 5. `components/trading/TRViewChartControls.tsx`

- **개요**: 차트를 제어하는 UI (종목 선택, 옵션 토글)를 담당하는 재사용 가능한 React 컴포넌트입니다.
- **주요 컴포넌트**:
    - `TRViewChartControls`: 부모 컴포넌트로부터 상태와 상태 변경 함수를 props로 받아 차트 설정을 변경하는 버튼들을 렌더링합니다.

### 6. `components/trading/TRViewChart.tsx`

- **개요**: `lightweight-charts` 라이브러리를 래핑하는 핵심 차트 컴포넌트입니다. 성능 최적화와 실시간 업데이트를 고려하여 설계되었습니다.
- **주요 컴포넌트**:
    - `TRViewChart`:
        - 차트 초기화 및 시리즈(캔들, 거래량) 생성을 담당합니다.
        - `useEffect`를 분리하여 옵션(그리드, 거래량 표시 등) 변경 시 차트가 재생성되지 않고 동적으로 업데이트되도록 최적화했습니다.
        - `useMemo`를 사용해 데이터 변환 로직을 메모이제이션합니다.
        - `onReady` prop을 통해 외부에서 실시간 데이터를 주입할 수 있는 `updateCandle` 함수를 제공합니다.

### 7. `app/trview/page.tsx`

- **개요**: `/trview` 경로의 메인 페이지로, 위에서 만든 모든 훅과 컴포넌트를 조합하여 실제 차트 데모 페이지를 구성합니다.
- **주요 컴포넌트**:
    - `TRViewPage`: `useState`로 차트 옵션 상태를 관리하고, `useTRViewChart` 훅으로 데이터를 가져와 `TRViewChart`와 `TRViewChartControls` 컴포넌트에 전달합니다.

### 8. `__tests__/lib/tradingview/dataConverter.test.ts`

- **개요**: `dataConverter.ts`의 핵심 변환 로직에 대한 유닛 테스트 파일입니다. 데이터 형식의 정확성과 엣지 케이스를 검증합니다.
- **주요 테스트**:
    - `convertToTRViewCandles`: ISO 타임스탬프가 Unix 타임스탬프로 정확히 변환되는지 검증합니다.
    - `convertToTRViewVolumes`: 거래량 데이터와 함께 상승/하락에 따른 색상 지정 로직이 올바른지 검증합니다.
