# 분봉 차트 일일 리셋 및 거래시간 관리 구현 완료

## ✅ 구현 완료 사항

### 1️⃣ Backend 구현 (Python/FastAPI)

#### A. 거래시간 유틸리티
**파일**: `backend/app/utils/trading_hours.py`

**주요 기능**:
- `TradingSession` Enum: 시간대 구분 (정규장, 시간외 종가, 시간외 단일가, 장 외)
- `TradingHoursManager` 클래스:
  - `is_regular_hours()`: 정규 장 시간 체크 (9:00~15:30)
  - `is_trading_hours()`: 거래 시간 체크 (시간외 포함 옵션)
  - `get_session()`: 현재 거래 세션 반환
  - `get_time_until_reset()`: 리셋까지 남은 시간

#### B. Service 레이어 수정
**파일**: `backend/app/services/trading_service.py`

**변경사항**:
- `get_minute_chart_data()` 메서드 수정
- 파라미터 추가:
  - `target_date`: 특정 날짜 조회
  - `include_extended_hours`: 시간외 거래 포함
  - `regular_hours_only`: 정규 장만 필터링
- 필터링 로직 구현: 날짜 + 거래시간 기반 데이터 필터링

#### C. API 엔드포인트 수정
**파일**: `backend/app/api/chart.py`

**변경사항**:
- `/api/chart/{stock_code}/minute` 엔드포인트 개선
- 쿼리 파라미터 추가:
  - `date`: 조회 날짜 (YYYY-MM-DD)
  - `include_extended_hours`: 시간외 거래 포함 (기본: false)
  - `regular_hours_only`: 정규 장만 (기본: true)

**API 사용 예시**:
```bash
# 정규장만 (9:00~15:30)
GET /api/chart/005930/minute?regular_hours_only=true

# 시간외 포함 (8:30~16:00)
GET /api/chart/005930/minute?include_extended_hours=true

# 특정 날짜
GET /api/chart/005930/minute?date=2025-01-15
```

---

### 2️⃣ Frontend 구현 (Next.js/React)

#### A. 거래시간 유틸리티
**파일**: `stock-trading-ui/src/lib/utils/tradingHours.ts`

**주요 기능**:
- `TradingSession` Enum: TypeScript 버전
- `TradingHoursManager` 클래스:
  - 거래 세션 판별
  - 리셋 시간 계산
  - 시간 범위 검증

#### B. useTradingHours Hook
**파일**: `stock-trading-ui/src/hooks/useTradingHours.ts`

**제공 기능**:
- `currentSession`: 현재 거래 세션
- `isMarketOpen`: 장 개장 여부
- `formatTimeUntilReset()`: 리셋까지 남은 시간 (포맷팅)
- `sessionDisplayName`: 세션 표시명

**사용 예시**:
```typescript
const { currentSession, isMarketOpen, formatTimeUntilReset } = useTradingHours();
```

#### C. useRealChartData Hook 개선
**파일**: `stock-trading-ui/src/hooks/useRealChartData.ts`

**추가 옵션**:
- `includeExtendedHours`: 시간외 거래 포함
- `regularHoursOnly`: 정규 장만
- `targetDate`: 특정 날짜 조회

#### D. test-chart 페이지 UI 개선
**파일**: `stock-trading-ui/src/app/test-chart/page.tsx`

**추가된 기능**:
1. **거래시간 상태 표시**
   - 장 진행 중/장 마감 Badge
   - 현재 세션 표시 (정규장, 시간외 등)
   - 다음 리셋까지 카운트다운

2. **시간 필터링 옵션 카드** (분봉일 때만 표시)
   - "정규장만 (9:00~15:30)" 체크박스
   - "시간외 포함 (8:30~16:00)" 체크박스
   - 현재 필터링 상태 Badge

3. **자동 리셋 메커니즘**
   - 매일 0시 자동 데이터 갱신
   - 다음 리셋 시간 표시

---

## 🔄 동작 흐름

### 데이터 조회 흐름
```
1. Frontend: useRealChartData Hook 호출
   - includeExtendedHours: false
   - regularHoursOnly: true

2. Frontend → Backend API 요청
   GET /api/chart/005930/minute?regular_hours_only=true

3. Backend: API 엔드포인트
   - 쿼리 파라미터 파싱
   - TradingService 호출

4. Backend: TradingService
   - 원본 데이터 조회 (korea_invest_service)
   - TradingHoursManager로 각 캔들 필터링
   - 9:00~15:30 데이터만 반환

5. Frontend: 필터링된 데이터 표시
   - 차트 렌더링
   - 메타데이터 업데이트
```

### 자동 리셋 흐름
```
1. 페이지 로드 시 useEffect 실행
2. 다음 0시까지 시간 계산
3. setTimeout으로 0시에 refetch() 예약
4. 0시 도달 시 자동으로 데이터 갱신
5. 24시간마다 반복 (setInterval)
```

---

## 🧪 테스트 가이드

### Backend 테스트

#### 1. 기본 API 호출 (정규장만)
```bash
curl "http://localhost:8000/api/chart/005930/minute?regular_hours_only=true"
```

**예상 결과**:
- 9:00~15:30 사이 데이터만 반환
- 120개 제한 없음 (당일 전체 분봉)

#### 2. 시간외 거래 포함
```bash
curl "http://localhost:8000/api/chart/005930/minute?include_extended_hours=true&regular_hours_only=false"
```

**예상 결과**:
- 8:30~16:00 사이 데이터 반환

#### 3. 특정 날짜 조회
```bash
curl "http://localhost:8000/api/chart/005930/minute?date=2025-01-15"
```

**예상 결과**:
- 2025-01-15의 정규장 데이터만

#### 4. Backend 서버 시작
```bash
cd backend
source vkis/bin/activate  # 가상환경 활성화 필수!
python app/main.py
```

---

### Frontend 테스트

#### 1. 개발 서버 시작
```bash
cd stock-trading-ui
npm run dev  # 또는 ./scripts/start-server.sh
```

#### 2. 테스트 페이지 접속
```
http://localhost:9000/test-chart
```

#### 3. 테스트 시나리오

**시나리오 1: 정규장 시간 필터링**
1. "정규장만 (9:00~15:30)" 체크박스 활성화
2. 차트 데이터 확인
3. ✅ 9:00 이전 데이터 없음
4. ✅ 15:30 이후 데이터 없음

**시나리오 2: 시간외 거래 포함**
1. "시간외 포함 (8:30~16:00)" 체크박스 활성화
2. 차트 데이터 확인
3. ✅ 8:30~9:00 데이터 포함
4. ✅ 15:30~16:00 데이터 포함

**시나리오 3: 거래시간 상태 표시**
1. 현재 시간에 따른 Badge 확인
   - 9:00~15:30: "장 진행 중" (녹색)
   - 그 외: "장 마감" (회색)
2. 세션 표시명 확인
   - "정규장", "시간외 종가", "시간외 단일가", "장 외 시간"

**시나리오 4: 자동 리셋 카운트다운**
1. "다음 리셋: X시간 Y분 Z초" 표시 확인
2. 1초마다 업데이트 확인

**시나리오 5: 자동 갱신**
1. "Auto Refresh" 버튼 활성화
2. ✅ 분봉일 때: 장 시간에만 자동 갱신
3. ✅ 일봉 이상: 항상 자동 갱신

---

## 📊 예상 결과

### Before (구현 전)
| 항목 | 상태 |
|------|------|
| 캔들 개수 | 120개 제한 |
| 시간 필터링 | ❌ 없음 |
| 일일 리셋 | ❌ 없음 |
| 시간외 거래 | ❌ 제어 불가 |
| 장 상태 표시 | ❌ 없음 |

### After (구현 후)
| 항목 | 상태 |
|------|------|
| 캔들 개수 | 당일 전체 (최대 390개) |
| 시간 필터링 | ✅ 9:00~15:30 정규장 |
| 일일 리셋 | ✅ 매일 0시 자동 |
| 시간외 거래 | ✅ 옵션 제공 (8:30~16:00) |
| 장 상태 표시 | ✅ 실시간 표시 + 세션명 |

---

## 🐛 트러블슈팅

### 1. Backend 에러: ModuleNotFoundError
**문제**: `ModuleNotFoundError: No module named 'app.utils.trading_hours'`

**해결**:
```bash
cd backend
# 가상환경 활성화 확인
source vkis/bin/activate
# 패키지 재설치
pip install -r requirements.txt
```

### 2. Frontend 에러: Module not found
**문제**: `Module not found: Can't resolve '@/lib/utils/tradingHours'`

**해결**:
```bash
cd stock-trading-ui
# 의존성 재설치
npm install
# 개발 서버 재시작
npm run dev
```

### 3. 데이터가 필터링되지 않음
**문제**: 모든 시간대 데이터가 표시됨

**원인**: 타임스탬프 파싱 실패

**해결**: 로그 확인
```bash
# Backend 로그
tail -f backend/logs/app.log

# Frontend 콘솔
# 브라우저 개발자 도구 → Console
```

### 4. 자동 리셋이 작동하지 않음
**문제**: 0시에 데이터가 갱신되지 않음

**원인**: 페이지가 닫혀있거나 브라우저가 슬립 모드

**해결**:
- 페이지를 열어둔 상태 유지
- 또는 페이지 재접속 시 자동 로드

---

## 📝 API 문서

### GET /api/chart/{stock_code}/minute

**Description**: 분봉 차트 데이터 조회 (거래시간 필터링 옵션 제공)

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| stock_code | string | ✅ | - | 종목 코드 (예: 005930) |
| date | string | ❌ | 오늘 | 조회 날짜 (YYYY-MM-DD) |
| include_extended_hours | boolean | ❌ | false | 시간외 거래 포함 (8:30~16:00) |
| regular_hours_only | boolean | ❌ | true | 정규 장만 (9:00~15:30) |

**Response**:
```json
[
  {
    "timestamp": "2025-01-15T09:00:00",
    "open": 71000,
    "high": 71200,
    "low": 70900,
    "close": 71100,
    "volume": 123456
  },
  ...
]
```

**Status Codes**:
- 200: 성공
- 400: 잘못된 날짜 형식
- 404: 차트 데이터 없음
- 500: 서버 오류

---

## 🚀 다음 단계 (선택사항)

### 1. 휴장일 처리
- 주말/공휴일 자동 감지
- 휴장일에는 데이터 조회 안 함

### 2. 데이터 캐싱
- Redis 캐싱으로 성능 개선
- 캐시 만료 시간 설정

### 3. 과거 데이터 조회
- 날짜 선택 UI (DatePicker)
- 과거 특정 날짜 분봉 조회

### 4. 알림 기능
- 장 시작 10분 전 알림
- 장 마감 알림

### 5. 장 마감 요약
- 15:30 이후 당일 거래 요약 표시
- 거래량, 가격 범위 등 통계

---

## 📚 참고 자료

- [한국거래소 거래시간](https://www.krx.co.kr/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Next.js 공식 문서](https://nextjs.org/docs)
- [Trading Hours Specification](https://en.wikipedia.org/wiki/Trading_hours)

---

**작성일**: 2025-09-30
**버전**: 1.0.0
**상태**: ✅ 구현 완료 - 테스트 중