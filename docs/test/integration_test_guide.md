# 삼성전자 실시간 차트 통합 테스트 가이드

## 🚀 테스트 환경 설정

### 1. Backend 서버 시작

```bash
# 터미널 1: Backend 서버
cd backend
source vkis/bin/activate  # 가상환경 활성화 (중요!)
python app/main.py        # 서버 시작 (포트 8000)
```

**확인 사항:**
- ✅ 가상환경이 활성화되었는지 확인 (`which python` → vkis/bin/python)
- ✅ 한국투자증권 API 설정이 환경변수에 있는지 확인
- ✅ 서버가 `http://localhost:8000`에서 실행 중인지 확인

### 2. Frontend 서버 시작

```bash
# 터미널 2: Frontend 서버
cd stock-trading-ui
npm run dev               # 서버 시작 (포트 9000)
```

**확인 사항:**
- ✅ 서버가 `http://localhost:9000`에서 실행 중인지 확인
- ✅ 빌드 에러가 없는지 확인

## 🧪 테스트 시나리오

### Step 1: Backend API 수동 테스트

```bash
# 터미널 3: Backend 테스트
cd backend
source vkis/bin/activate
python test_samsung_manual.py
```

**예상 결과:**
```
🔍 삼성전자 차트 데이터 테스트 시작
✅ API 연결 성공!
📊 삼성전자(005930) 차트 데이터 조회 중...
✅ 차트 데이터 조회 성공!
📋 응답 데이터 구조:
   - Type: <class 'dict'>
   - Keys: ['output1', 'output2']
📈 차트 데이터 (output2):
   - Type: <class 'list'>
   - Length: 100+
```

**에러 발생 시:**
- API 키 설정 확인
- 네트워크 연결 확인
- 한국투자증권 서버 상태 확인

### Step 2: API 엔드포인트 테스트

```bash
# API 호출 테스트
curl "http://localhost:8000/api/stocks/005930/chart?format=frontend" | jq
```

**예상 응답:**
```json
{
  "success": true,
  "message": "차트 데이터 조회 성공",
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00",
      "open": 71000,
      "high": 72000,
      "low": 70500,
      "close": 71500,
      "volume": 1000000
    }
  ],
  "metadata": {
    "stock_code": "005930",
    "count": 100,
    "average_price": 71250.5
  }
}
```

### Step 3: 테스트 페이지 확인

**접속:** http://localhost:9000/test-chart

**확인 사항:**
1. ✅ **연결 상태**: API Connection = Connected (녹색)
2. ✅ **데이터 개수**: Chart Data = 100+ candles
3. ✅ **마지막 업데이트**: 최근 시간으로 표시
4. ✅ **데이터 유효성**: Data Validity = Valid (녹색)
5. ✅ **차트 렌더링**: 삼성전자 차트가 올바르게 표시
6. ✅ **실시간 지표**: Live 상태 표시 (녹색)

**에러 발생 시:**
- 빨간색 상태 표시 확인
- 에러 메시지 확인
- 브라우저 개발자 도구 콘솔 확인

### Step 4: 한국 거래 페이지 확인

**접속:** http://localhost:9000/korean-trading

**확인 사항:**
1. ✅ **차트 영역**: 중앙 패널에 실시간 차트 표시
2. ✅ **Live 지표**: 차트 상단 좌측에 "실시간" 녹색 배지
3. ✅ **연결 상태**: 차트 제목 옆에 Live/Offline 상태
4. ✅ **자동 새로고침**: 30초마다 데이터 업데이트
5. ✅ **종목 변경**: 왼쪽 종목 리스트에서 다른 종목 선택 시 차트 변경

### Step 5: 성능 및 안정성 테스트

#### 5.1 네트워크 끊김 시뮬레이션
1. Backend 서버 종료
2. Frontend에서 "Offline" 상태 확인
3. 에러 메시지 표시 확인
4. Backend 서버 재시작
5. "Connected" 상태로 복구 확인

#### 5.2 자동 새로고침 테스트
1. 테스트 페이지에서 "Auto Refresh" 활성화
2. 30초마다 데이터 업데이트 확인
3. "Last Updated" 시간 변경 확인
4. 네트워크 트래픽 모니터링

#### 5.3 여러 종목 테스트
```bash
# 다른 종목 테스트
curl "http://localhost:8000/api/stocks/000660/chart?format=frontend" # SK하이닉스
curl "http://localhost:8000/api/stocks/035420/chart?format=frontend" # 네이버
```

## 🐛 문제 해결

### 가장 흔한 문제들

#### 1. "Cannot connect to backend server"
**원인:** Backend 서버가 실행되지 않음
**해결:**
```bash
cd backend
source vkis/bin/activate
python app/main.py
```

#### 2. "API가 연결되지 않았습니다"
**원인:** 한국투자증권 API 설정 문제
**해결:**
```bash
# 환경변수 확인
echo $KI_API_KEY
echo $KI_SECRET_KEY

# 설정 파일 확인
cat backend/.env
```

#### 3. "차트 데이터가 없습니다"
**원인:**
- 장마감 시간 (15:30 이후)
- 주말/공휴일
- API 호출 제한

**해결:**
- 장시간에 테스트
- API 호출 간격 조정
- Mock 데이터로 대체 테스트

#### 4. Frontend 빌드 에러
**원인:** 타입스크립트 에러 또는 의존성 문제
**해결:**
```bash
cd stock-trading-ui
npm install
npm run build
```

#### 5. "Request timeout"
**원인:** API 응답 시간 초과
**해결:**
- 네트워크 연결 확인
- Backend 로그 확인
- Timeout 설정 증가

### 로그 확인

#### Backend 로그
```bash
# Backend 터미널에서 실시간 로그 확인
tail -f logs/app.log
```

#### Frontend 로그
```bash
# 브라우저 개발자 도구 > Console
# 또는 터미널에서 Frontend 서버 로그 확인
```

#### API 호출 로그
```bash
# 요청/응답 상세 로그
curl -v "http://localhost:8000/api/stocks/005930/chart?format=frontend"
```

## ✅ 성공 기준

### 최소 요구사항
- [ ] Backend 서버가 에러 없이 시작됨
- [ ] Frontend 서버가 에러 없이 시작됨
- [ ] 삼성전자 차트 데이터 API 호출 성공
- [ ] 테스트 페이지에서 실제 차트 렌더링
- [ ] 한국 거래 페이지에서 실시간 차트 표시

### 추가 목표
- [ ] 자동 새로고침 기능 동작
- [ ] 여러 종목 차트 데이터 조회 성공
- [ ] 네트워크 오류 시 적절한 에러 처리
- [ ] 성능 최적화 (API 응답 시간 < 2초)
- [ ] 메모리 누수 없음 (장시간 실행 시)

## 📊 성능 메트릭

### 측정 항목
1. **API 응답 시간**: < 2초
2. **차트 렌더링 시간**: < 1초
3. **메모리 사용량**: < 100MB 증가
4. **네트워크 트래픽**: 자동 새로고침 시 적절한 간격

### 모니터링 도구
```bash
# API 응답 시간 측정
time curl "http://localhost:8000/api/stocks/005930/chart?format=frontend"

# 메모리 사용량 모니터링
ps aux | grep python

# 네트워크 트래픽 모니터링
netstat -i
```

## 🎯 다음 단계

### Phase 2 계획
1. **실시간 WebSocket 연동**: 가격 변동 실시간 반영
2. **기술적 지표 실시간 계산**: RSI, MACD 실시간 업데이트
3. **다종목 동시 모니터링**: 여러 종목 동시 추적
4. **성능 최적화**: 캐싱, 압축, 최적화

### 확장 기능
1. **알림 시스템**: 가격 목표 달성 시 알림
2. **히스토리 차트**: 과거 데이터 조회
3. **비교 차트**: 여러 종목 비교
4. **내보내기**: 차트 이미지/데이터 내보내기

---

**💡 팁**: 이 테스트는 한국 주식 장시간(09:00-15:30 KST)에 실행하는 것이 가장 좋습니다. 장마감 후에는 실시간 데이터 대신 마지막 거래일 데이터가 표시될 수 있습니다.