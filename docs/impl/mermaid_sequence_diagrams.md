## 📊 Mermaid Sequence Diagrams

Diagram 1: 초기 로드 (캐시 히트)

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant ChartAPI
    participant Backend
    participant Cache

    User->>Frontend: 페이지 접속
    Frontend->>ChartAPI: getMinuteCandles("005930")
    ChartAPI->>Backend: GET /api/chart/005930/minute
    Backend->>Cache: 파일 확인 (20250930.dat)
    Cache-->>Backend: ✅ 파일 존재
    Backend->>Cache: 파일 읽기
    Cache-->>Backend: 120개 캔들 데이터
    Backend-->>ChartAPI: JSON 응답 (0.1초)
    ChartAPI-->>Frontend: ChartCandle[]
    Frontend->>User: 차트 표시
```

Diagram 2: 왼쪽 드래그 (캐시 미스)

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant useInfiniteChartData
    participant ChartAPI
    participant Backend
    participant Cache
    participant KoreaInvestAPI

    User->>Frontend: 왼쪽으로 드래그
    Frontend->>Frontend: viewWindow.startIndex < 20 감지
    Frontend->>useInfiniteChartData: loadPreviousDay()
    useInfiniteChartData->>ChartAPI: getMinuteCandles("005930", "2025-09-29")
    ChartAPI->>Backend: GET /api/chart/005930/minute?date=2025-09-29
    Backend->>Cache: 파일 확인 (20250929.dat)
    Cache-->>Backend: ❌ 파일 없음
    Backend->>KoreaInvestAPI: 분봉 데이터 요청
    KoreaInvestAPI-->>Backend: DataFrame (1~2초)
    Backend->>Backend: 중복 제거
    Backend->>Cache: 파일 저장
    Cache-->>Backend: ✅ 저장 완료
    Backend-->>ChartAPI: JSON 응답
    ChartAPI-->>useInfiniteChartData: ChartCandle[]
    useInfiniteChartData->>useInfiniteChartData: 기존 데이터 앞에 추가
    useInfiniteChartData-->>Frontend: 병합된 데이터
    useInfiniteChartData-->>Frontend: viewWindow 인덱스 조정
    Frontend->>User: 과거 데이터 표시
```

Diagram 3: 연속 탐색 (캐시 히트)

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant useInfiniteChartData
    participant ChartAPI
    participant Backend
    participant Cache

    User->>Frontend: 계속 왼쪽 드래그
    Frontend->>useInfiniteChartData: loadPreviousDay() (2025-09-28)
    useInfiniteChartData->>ChartAPI: getMinuteCandles("005930", "2025-09-28")
    ChartAPI->>Backend: GET /api/chart/005930/minute?date=2025-09-28
    Backend->>Cache: 파일 확인 (20250928.dat)
    Cache-->>Backend: ✅ 파일 존재 (이전에 저장됨)
    Backend->>Cache: 파일 읽기
    Cache-->>Backend: 120개 캔들
    Backend-->>ChartAPI: JSON 응답 (0.1초)
    ChartAPI-->>useInfiniteChartData: ChartCandle[]
    useInfiniteChartData-->>Frontend: 즉시 병합
    Frontend->>User: 빠른 과거 데이터 표시
```

Diagram 4: 메모리 관리

```mermaid
sequenceDiagram
    actor Timer
    participant Frontend
    participant useInfiniteChartData

    Timer->>Frontend: 1분 타이머 트리거
    Frontend->>useInfiniteChartData: trimOldData(5)
    useInfiniteChartData->>useInfiniteChartData: 현재 날짜 기준 5일 이전 데이터 확인
    alt 오래된 데이터 존재
        useInfiniteChartData->>useInfiniteChartData: 데이터 제거
        useInfiniteChartData-->>Frontend: 최적화된 데이터
    else 모두 최신
        useInfiniteChartData-->>Frontend: 변경 없음
    end
```

## 🎯 핵심 함수 요약

### 백엔드

| 함수명                                        | 위치                     | 역할                |
|--------------------------------------------|------------------------|-------------------|
| ChartCacheService.get_minute_candles()     | chart_cache_service.py | 캐시 우선 데이터 조회      |
| ChartCacheService._save_to_cache()         | chart_cache_service.py | JSON 파일 저장        |
| ChartCacheService._load_from_cache()       | chart_cache_service.py | JSON 파일 로드        |
| TradingCalendar.get_previous_trading_day() | trading_calendar.py    | 이전 거래일 계산         |
| TradingCalendar.is_trading_day()           | trading_calendar.py    | 거래일 여부 확인         |
| get_minute_chart_data()                    | chart.py               | API 엔드포인트 (캐시 통합) |

### 프론트엔드

| 함수명                         | 위치                      | 역할              |
|-----------------------------|-------------------------|-----------------|
| ChartAPI.getMinuteCandles() | chart-api.ts            | 백엔드 API 호출      |
| useInfiniteChartData()      | useInfiniteChartData.ts | 무한 스크롤 훅        |
| loadPreviousDay()           | useInfiniteChartData.ts | 이전 날짜 데이터 로드    |
| trimOldData()               | useInfiniteChartData.ts | 메모리 관리          |
| getPreviousTradingDay()     | useInfiniteChartData.ts | 이전 거래일 계산 (프론트) |

## ✅ 구현 체크리스트

### Phase 1: 백엔드 기반

- ChartCacheService 클래스 생성
- TradingCalendar 유틸리티 생성
- kordata/ 디렉토리 생성
- API 엔드포인트에 date 파라미터 추가
- 캐시 통계 API 추가
- 테스트: 캐시 저장/로드 확인

### Phase 2: 프론트엔드 무한 스크롤

- ChartAPI 클래스 생성
- useInfiniteChartData 훅 생성
- RechartsAdapter에 무한 스크롤 통합
- 로딩 UI 추가
- 테스트: 왼쪽 드래그 시 데이터 로드 확인

### Phase 3: 최적화 및 개선

- 메모리 관리 로직 추가
- Debounce 적용
- 에러 처리 개선
- 캐시 무효화 기능 추가
- 성능 테스트
