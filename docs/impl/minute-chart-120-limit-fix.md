# 분봉 차트 120개 제한 해결

## 🐛 문제 분석

### 원인
한국투자증권 API는 1분봉 조회 시 **한 번에 최대 120개**만 반환합니다.
- 9:00 ~ 15:30 = 390분
- 120개 제한으로는 약 2시간 분량만 표시 가능

### 영향
- 장 시작(9:00)부터 현재까지 전체 분봉을 볼 수 없음
- 최근 120분(2시간) 데이터만 표시

---

## ✅ 해결 방법

### 개선된 로직
`brokers/korea_investment/ki_api.py`의 `get_minute_chart_data` 메서드를 개선하여 **여러 번 호출**로 전체 데이터 수집

#### 주요 변경사항

1. **파라미터 추가**
   ```python
   def get_minute_chart_data(self, stock_code, start_time=None, max_count=None):
       """
       Args:
           stock_code: 종목 코드
           start_time: 시작 시간 (HHMMSS, 기본값: 090000)
           max_count: 최대 조회 개수 (기본값: 무제한)
       """
   ```

2. **반복 호출 로직**
   ```python
   while iteration < max_iterations:
       # 1. 현재 end_time부터 과거로 120개 조회
       params = {
           'FID_INPUT_HOUR_1': end_time,
           ...
       }

       # 2. 데이터 수집
       df_batch = fetch_api(params)
       all_data.append(df_batch)

       # 3. 시작 시간에 도달했는지 체크
       if oldest_time <= start_time:
           break

       # 4. 다음 배치를 위한 end_time 업데이트
       end_time = oldest_time - 1분
   ```

3. **데이터 병합 및 정렬**
   ```python
   final_df = pd.concat(all_data)
   final_df = final_df[final_df['시간'] >= start_time]  # 필터링
   final_df = final_df[::-1].reset_index(drop=True)    # 과거→최신 정렬
   ```

---

## 🔄 동작 흐름

### 예시: 14:00에 조회하는 경우

```
현재 시간: 14:00 (840분)
장 시작: 09:00 (540분)
필요 데이터: 300분 (5시간)

[Batch 1] 14:00 → 12:00 (120분)  ✅
[Batch 2] 12:00 → 10:00 (120분)  ✅
[Batch 3] 10:00 → 09:00 (60분)   ✅

총 300분 데이터 수집 완료!
```

### 로그 출력
```
📊 분봉 데이터 수집 시작: 005930, 090000 ~ 140000
📦 Batch 1: 120개 수집 (마지막 시간: 120000)
📦 Batch 2: 120개 수집 (마지막 시간: 100000)
📦 Batch 3: 60개 수집 (마지막 시간: 090000)
✅ 시작 시간 090000에 도달
✅ 총 300개 분봉 데이터 수집 완료
```

---

## 🚀 성능 최적화

### 1. API 호출 제한
- 한국투자증권: **초당 최대 20건**
- 대기 시간: 50ms (`time.sleep(0.05)`)

### 2. 무한 루프 방지
- 최대 반복 횟수: 10회 (1200분 = 20시간)
- 실제로는 2~4회면 충분 (9:00~15:30)

### 3. 조기 종료 조건
- 시작 시간에 도달
- 데이터가 없음
- API 오류 발생
- 최대 개수 도달

---

## 📊 예상 결과

### Before (개선 전)
```
조회 시간: 14:00
수집 데이터: 120개 (12:00~14:00)
커버리지: 40% (300분 중 120분)
```

### After (개선 후)
```
조회 시간: 14:00
수집 데이터: 300개 (09:00~14:00)
커버리지: 100% (장 시작부터 전체)
```

---

## 🧪 테스트 방법

### 1. Backend 테스트

#### 직접 호출 테스트
```python
# Python 인터프리터에서
from brokers.korea_investment.ki_api import KoreaInvestAPI
from brokers.korea_investment.ki_env import KoreaInvestEnv

env = KoreaInvestEnv()
api = KoreaInvestAPI(env)

# 전체 데이터 조회 (9시부터)
df = api.get_minute_chart_data('005930')
print(f"수집된 데이터: {len(df)}개")
print(f"시작 시간: {df.iloc[0]['시간']}")
print(f"종료 시간: {df.iloc[-1]['시간']}")
```

#### API 엔드포인트 테스트
```bash
# 정규장 전체 데이터
curl "http://localhost:8000/api/chart/005930/minute?regular_hours_only=true"

# 응답 예시
[
  {"timestamp": "2025-01-15T09:00:00", "open": 71000, ...},  # 첫 번째 (9:00)
  {"timestamp": "2025-01-15T09:01:00", "open": 71100, ...},
  ...
  {"timestamp": "2025-01-15T14:00:00", "open": 72000, ...}   # 마지막 (현재)
]
```

### 2. Frontend 테스트

#### 브라우저에서 확인
```
1. http://localhost:9000/test-chart 접속
2. "1분" 타임프레임 선택
3. 차트 확인:
   - 9:00부터 현재까지 모든 캔들 표시
   - 상태 카드: "XXX candles" (120개 이상)
```

---

## ⚠️ 주의사항

### 1. API 호출 비용
- 배치당 1회 API 호출
- 평균 2~4회 호출 (장 중)
- 비용 증가 가능성 있음

### 2. 응답 시간
- 기존: ~200ms (1회 호출)
- 개선 후: ~800ms (4회 호출)
- 사용자 대기 시간 증가

### 3. 오류 처리
- 중간에 API 오류 발생 시: 수집된 데이터까지만 반환
- 네트워크 불안정: 일부 데이터 누락 가능성

---

## 🔧 추가 개선 사항 (선택)

### 1. 캐싱 구현
```python
# Redis 캐싱으로 반복 조회 최적화
cache_key = f"minute_chart:{stock_code}:{date}"
if redis.exists(cache_key):
    return redis.get(cache_key)
```

### 2. 백그라운드 갱신
```python
# 1분마다 백그라운드에서 최신 데이터만 추가
@app.on_event("startup")
async def start_background_updater():
    asyncio.create_task(update_minute_data())
```

### 3. WebSocket 스트리밍
```python
# 실시간으로 1분봉 추가 (120개 제한 우회)
@app.websocket("/ws/minute_chart/{stock_code}")
async def minute_chart_stream(websocket, stock_code):
    # 매 1분마다 새 캔들 전송
```

---

## 📝 관련 파일

- **수정**: `brokers/korea_investment/ki_api.py`
  - `get_minute_chart_data()` 메서드 개선
- **영향 없음**:
  - `backend/app/core/korea_invest.py` (래퍼만 호출)
  - `backend/app/services/trading_service.py` (필터링만 수행)
  - `backend/app/api/chart.py` (엔드포인트)

---

## ✅ 체크리스트

### 구현
- [x] `ki_api.py` 개선 (여러 번 호출 로직)
- [x] 파라미터 추가 (start_time, max_count)
- [x] 로그 추가 (디버깅용)
- [x] 무한 루프 방지
- [x] API 호출 간격 준수

### 테스트
- [ ] Backend 직접 호출 테스트
- [ ] API 엔드포인트 테스트
- [ ] Frontend 차트 확인
- [ ] 9시~15시 전체 데이터 확인
- [ ] 성능 측정 (응답 시간)

---

**작성일**: 2025-09-30
**버전**: 1.0.0
**상태**: ✅ 구현 완료 - 테스트 필요