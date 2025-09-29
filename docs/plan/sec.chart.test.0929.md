# 삼성전자 실시간 차트 구현 테스트 중심 계획

## 🎯 Phase 1: 삼성전자 실제 데이터 검증 및 차트 연동

### 현재 상황 분석
- **Backend**: 한국투자증권 API 연동 완료 (`KoreaInvestAPI.get_daily_price_chart` 메서드 존재)
- **Frontend**: Mock 데이터 기반 차트 컴포넌트 구현됨
- **목표**: 삼성전자(005930) 실제 데이터로 차트 렌더링 테스트

### 1.1 Backend API 테스트 및 검증 🔧

#### 테스트 파일 생성
```python
# backend/tests/test_samsung_chart_data.py (신규)
- 삼성전자(005930) 차트 데이터 API 호출 테스트
- 한국투자증권 API 연결 상태 확인
- 데이터 형식 검증 (OHLCV)
- 에러 처리 시나리오 테스트
```

#### API 엔드포인트 강화
```python
# backend/app/api/stocks.py 수정
- /api/stocks/005930/chart 엔드포인트 강화
- 실제 데이터 반환 확인
- 에러 로깅 개선
- 응답 형식 표준화
```

#### 테스트 스크립트 작성
```python
# backend/test_samsung_manual.py (신규)
- 수동 테스트용 스크립트
- 삼성전자 차트 데이터 직접 호출
- 콘솔에 결과 출력
- API 연결 문제 진단
```

### 1.2 Frontend 실제 데이터 연동 ⚛️

#### API 연동 Hook 개발
```typescript
// src/hooks/useRealChartData.ts (신규)
- 실제 API 호출 로직
- 에러 처리 및 로딩 상태
- 삼성전자 고정 테스트
```

#### Chart 컴포넌트 수정
```typescript
// src/components/trading/KoreanTradingChart.tsx 수정
- Mock 데이터 대신 실제 API 데이터 사용
- 데이터 없을 때 fallback 처리
- 로딩/에러 상태 UI
```

#### 테스트 페이지 생성
```typescript
// src/app/test-chart/page.tsx (신규)
- 삼성전자 전용 테스트 페이지
- 실제 데이터 확인용
- 개발자 디버깅 정보 표시
```

### 1.3 데이터 흐름 검증 🔍

#### 백엔드 테스트
1. 한국투자증권 API 연결 테스트
2. 삼성전자(005930) 일봉 데이터 조회
3. 데이터 형식 검증 (JSON 변환 확인)
4. 에러 케이스 처리 확인

#### 프론트엔드 테스트
1. `/api/stocks/005930/chart` API 호출 성공
2. 차트 데이터 파싱 및 렌더링
3. 에러 상황 처리 확인
4. 로딩 상태 UI 동작 확인

### 1.4 통합 테스트 환경 구축 🧪

#### 테스트 시나리오
```
1. Backend 서버 시작 (포트 8000)
2. 삼성전자 차트 API 호출
3. 응답 데이터 검증
4. Frontend 연동 테스트
5. http://localhost:9000/test-chart 접속
6. 실제 차트 렌더링 확인
```

#### 성공 기준
- ✅ 한국투자증권 API에서 삼성전자 실제 데이터 수신
- ✅ Backend API가 올바른 형식으로 데이터 변환
- ✅ Frontend에서 실제 OHLCV 데이터로 차트 렌더링
- ✅ 에러 발생 시 적절한 fallback 동작

## 🔄 Phase 2: 실시간 업데이트 기반 구축

### 2.1 WebSocket 실시간 데이터 스트리밍
- 삼성전자 실시간 가격 데이터 수신
- 차트 마지막 캔들 업데이트
- WebSocket 연결 안정성 확보

### 2.2 기술적 지표 계산
- RSI, MACD 실시간 계산
- 차트에 지표 오버레이
- 성능 최적화

### 2.3 다종목 확장
- 삼성전자 외 다른 종목 지원
- 종목 선택 UI 개선
- 메모리 관리 최적화

## 📁 구현할 파일 목록

### Backend
```
backend/
├── tests/test_samsung_chart_data.py     # 삼성전자 API 테스트
├── test_samsung_manual.py              # 수동 테스트 스크립트
├── app/api/stocks.py                   # API 엔드포인트 강화
└── app/models/chart_models.py          # 차트 데이터 모델 (신규)
```

### Frontend
```
frontend/
├── src/hooks/useRealChartData.ts       # 실제 API 연동 Hook
├── src/app/test-chart/page.tsx         # 테스트 전용 페이지
├── src/components/trading/
│   ├── KoreanTradingChart.tsx          # 실제 데이터 연동
│   └── ChartErrorBoundary.tsx          # 에러 처리 (신규)
└── src/lib/chartApiClient.ts           # API 클라이언트 (신규)
```

## 🚀 실행 계획

### Step 1: Backend 테스트
1. Backend 서버 시작 (`cd backend && source vkis/bin/activate && python app/main.py`)
2. 수동 테스트 실행 (`python test_samsung_manual.py`)
3. API 엔드포인트 테스트 (`curl http://localhost:8000/api/stocks/005930/chart`)

### Step 2: Frontend 연동
1. Frontend 서버 시작 (`cd stock-trading-ui && npm run dev`)
2. 테스트 페이지 접속 (`http://localhost:9000/test-chart`)
3. 실제 데이터 차트 렌더링 확인

### Step 3: 통합 검증
1. 데이터 정확성 검증 (한국투자증권 데이터와 비교)
2. 성능 측정 (API 응답 시간, 차트 렌더링 속도)
3. 에러 처리 시나리오 테스트

## ⚠️ 주의사항

1. **API 키 관리**: 한국투자증권 API 키가 환경변수에 올바르게 설정되어 있는지 확인
2. **시장 시간**: 한국 증시 개장 시간에 테스트 (9:00-15:30 KST)
3. **API 제한**: 한국투자증권 API 호출 횟수 제한 준수
4. **데이터 형식**: OHLCV 데이터가 올바른 숫자 형식으로 변환되는지 확인

이 계획을 통해 삼성전자 실제 데이터를 기반으로 한 차트 구현이 성공하면, 이후 실시간 업데이트와 다종목 확장으로 진행할 예정입니다.