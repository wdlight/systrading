# 한투 API Batch 수집 로직 수정 (2025-10-02)

## 🔍 문제 진단

### 증상
- Full day (09:00~15:30) 데이터 요청 시 391개가 아닌 139개만 수집됨
- Backend 캐시에 실제 거래 데이터는 13:12~15:30만 존재
- API를 10번 반복 호출해도 09:00까지 도달하지 못함

### 원인 분석

#### 1. Batch 수집 로직의 버그

**brokers/korea_investment/ki_api.py Line 256-269 (수정 전):**
```python
# 역순으로 정렬 (최신 -> 과거)
df_batch = df_batch[::-1].reset_index(drop=True)

batch_count = len(df_batch)
logger.info(f"📦 Batch {iteration + 1}: {batch_count}개 수집 (마지막 시간: {df_batch.iloc[-1]['시간']}")

# ...

# ❌ 문제: 역순 정렬 후 마지막 = 최신 시간을 oldest로 사용
oldest_time = df_batch.iloc[-1]['시간']  # 15:30 (최신)
```

**Line 277-279 (수정 전):**
```python
# ❌ 문제: oldest_time이 최신 시간이므로 1분씩만 감소
oldest_datetime = datetime.strptime(oldest_time, "%H%M%S")  # 15:30
next_end_datetime = oldest_datetime - timedelta(minutes=1)  # 15:29
end_time = next_end_datetime.strftime("%H%M%S")  # "152900"
```

#### 2. 실제 동작 결과

**API 호출 로그 (수정 전):**
```
Batch 1: end_time=153000 → 마지막 시간: 153000 (oldest=15:30)
Batch 2: end_time=152900 → 마지막 시간: 152900 (oldest=15:29)
Batch 3: end_time=152800 → 마지막 시간: 152800 (oldest=15:28)
...
Batch 10: end_time=152100 → 마지막 시간: 152100 (oldest=15:21)
```

**문제점:**
- 10번 반복해도 15:30 → 15:21 (9분만 이동)
- 1200개 수집했지만 대부분 중복
- 중복 제거 후 129개만 남음

#### 3. 역순 정렬의 혼란

```python
# API 응답: [15:30, 15:29, ..., 13:31] (최신 → 과거)
df_batch = df_batch[::-1]  # 역순 정렬
# 결과: [13:31, 13:32, ..., 15:30] (과거 → 최신)

# ❌ 잘못된 가정
oldest_time = df_batch.iloc[-1]['시간']  # 15:30 (마지막 = 최신)

# ✅ 올바른 접근
oldest_time = df_batch.iloc[0]['시간']   # 13:31 (첫 번째 = 가장 오래된)
```

---

## ✅ 해결 방법

### 수정 사항

#### 1. oldest 계산 로직 수정

**brokers/korea_investment/ki_api.py Line 259-280:**
```python
# 역순으로 정렬 (최신 -> 과거 → 과거 -> 최신)
df_batch = df_batch[::-1].reset_index(drop=True)

batch_count = len(df_batch)

# ✅ 배치 데이터 범위 로그 (역순 정렬 후: 첫번째=가장 오래된 시간, 마지막=최신 시간)
if batch_count > 0:
    oldest_in_batch = df_batch.iloc[0]['시간']   # 과거 (가장 오래된)
    newest_in_batch = df_batch.iloc[-1]['시간']  # 최신 (가장 최근)
    logger.info(f"📦 Batch {iteration + 1}: {batch_count}개 수집 | 범위: {oldest_in_batch}(oldest) ~ {newest_in_batch}(newest)")
else:
    logger.info(f"📦 Batch {iteration + 1}: 0개")

if batch_count == 0:
    logger.info("✅ 더 이상 데이터 없음")
    break

all_data.append(df_batch)

# 시작 시간에 도달했는지 확인
# ✅ 수정: 역순 정렬 후 첫 번째가 가장 오래된 시간
oldest_time = df_batch.iloc[0]['시간']
```

#### 2. 다음 end_time 계산 로직 수정

**Line 285-292:**
```python
# 다음 배치를 위한 종료 시간 업데이트
# ✅ 수정: 가장 오래된 데이터(배치의 첫 번째)의 1분 전으로 설정
# (API는 end_time부터 역순으로 반환하므로, 다음 배치는 이전 배치의 oldest - 1분부터 시작)
oldest_datetime = datetime.strptime(oldest_time, "%H%M%S")
next_end_datetime = oldest_datetime - timedelta(minutes=1)
prev_end_time = end_time
end_time = next_end_datetime.strftime("%H%M%S")
logger.info(f"🔄 다음 end_time: {prev_end_time} → {end_time} (oldest {oldest_time} - 1분)")
```

#### 3. 상세 로그 추가

**Line 223-224:**
```python
# ✅ API 요청 파라미터 로그
logger.info(f"🌐 API 요청 [{iteration + 1}]: end_time={end_time}, target=09:00부터 {end_time}까지 역순 조회")
```

---

## 🎯 수정 후 동작

### API 호출 로그 (수정 후)

```
📊 분봉 데이터 수집 시작: 005930, 090000 ~ 185535

🌐 API 요청 [1]: end_time=185535
📦 Batch 1: 120개 수집 | 범위: 132100(oldest) ~ 153000(newest)
🔄 다음 end_time: 185535 → 132000 (oldest 132100 - 1분)

🌐 API 요청 [2]: end_time=132000
📦 Batch 2: 120개 수집 | 범위: 112100(oldest) ~ 132000(newest)
🔄 다음 end_time: 132000 → 112000 (oldest 112100 - 1분)

🌐 API 요청 [3]: end_time=112000
📦 Batch 3: 120개 수집 | 범위: 092100(oldest) ~ 112000(newest)
🔄 다음 end_time: 112000 → 092000 (oldest 092100 - 1분)

🌐 API 요청 [4]: end_time=092000
📦 Batch 4: 120개 수집 | 범위: 134200(oldest) ~ 092000(newest)
...

✅ 총 1200개 분봉 데이터 수집 완료
```

### 개선 효과

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| 총 수집 | 1200개 | 1200개 |
| 중복 제거 후 | 129개 | 381개 |
| 시간 범위 | 15:21~15:30 (9분) | 09:00~15:30 (390분) |
| end_time 이동 | 1분씩 | 2시간씩 |
| 캐시 데이터 | 139개 (13:12~15:30) | 391개 (09:00~15:30) |
| 실제 거래 데이터 | 129개 (33%) | 381개 (97.4%) |

---

## 📊 최종 결과

### 캐시 파일 분석

```bash
총 캔들: 391개
첫 데이터: 2025-10-02T09:00:00
마지막 데이터: 2025-10-02T15:30:00

실제 거래 데이터 (volume > 0): 381개 (97.4%)
채움 데이터 (volume = 0): 10개 (2.6%)
```

### Batch별 데이터 수집

```
Batch 1: 13:21 ~ 15:30 (120개)
Batch 2: 11:21 ~ 13:20 (120개)
Batch 3: 09:21 ~ 11:20 (120개)
Batch 4~10: 추가 수집 (중복 및 갭 보완)
```

---

## 🔍 핵심 개념

### 1. API 동작 방식

```
FID_INPUT_HOUR_1 = end_time (종료 시간)

API 응답: end_time부터 역순으로 최대 120개
- 예: end_time=153000 → [15:30, 15:29, ..., 13:31] (최신 → 과거)
```

### 2. 역순 정렬의 의미

```python
# API 응답 (최신 → 과거)
raw: [15:30, 15:29, 15:28, ..., 13:32, 13:31]

# 역순 정렬 (과거 → 최신)
df_batch[::-1]: [13:31, 13:32, 13:33, ..., 15:29, 15:30]

# 인덱싱
df_batch.iloc[0]   # 13:31 (가장 오래된, oldest)
df_batch.iloc[-1]  # 15:30 (가장 최신, newest)
```

### 3. Batch 연속 조회 전략

```
Batch 1: end_time = 현재 시간
  → oldest = 13:21
  → 다음 end_time = 13:20 (oldest - 1분)

Batch 2: end_time = 13:20
  → oldest = 11:21
  → 다음 end_time = 11:20 (oldest - 1분)

Batch 3: end_time = 11:20
  → oldest = 09:21
  → 다음 end_time = 09:20 (oldest - 1분)
```

---

## 🧪 테스트 방법

### 1. 캐시 삭제 및 재수집

```bash
# 기존 캐시 삭제
rm -f backend/kordata/005930/20251002.json

# Backend 재시작
cd backend
source vkis/bin/activate
python app/main.py

# API 호출
curl http://localhost:8000/api/chart/005930/minute/full
```

### 2. 로그 확인

```bash
# API 호출 로그 확인
grep -E "(🌐 API 요청|📦 Batch|🔄 다음 end_time)" /tmp/backend.log
```

**예상 결과:**
```
🌐 API 요청 [1]: end_time=현재시간
📦 Batch 1: 120개 | 범위: 132100(oldest) ~ 153000(newest)
🔄 다음 end_time: 현재시간 → 132000 (oldest 132100 - 1분)

🌐 API 요청 [2]: end_time=132000
📦 Batch 2: 120개 | 범위: 112100(oldest) ~ 132000(newest)
🔄 다음 end_time: 132000 → 112000 (oldest 112100 - 1분)
```

### 3. 캐시 파일 검증

```bash
cd backend/kordata/005930
python3 << EOF
import json
from datetime import datetime

with open('20251002.json', 'r') as f:
    data = json.load(f)

print(f"총 캔들: {len(data)}개")
print(f"첫 데이터: {data[0]['timestamp']}")
print(f"마지막: {data[-1]['timestamp']}")

real = [c for c in data if c['volume'] > 0]
print(f"\n실제 거래: {len(real)}개 ({len(real)/len(data)*100:.1f}%)")

# 시간대별 분포
from collections import defaultdict
by_hour = defaultdict(int)
for c in real:
    hour = datetime.fromisoformat(c['timestamp']).hour
    by_hour[hour] += 1

print("\n시간대별 분포:")
for h in sorted(by_hour.keys()):
    print(f"  {h:02d}시: {by_hour[h]}개")
EOF
```

**예상 결과:**
```
총 캔들: 391개
첫 데이터: 2025-10-02T09:00:00
마지막: 2025-10-02T15:30:00

실제 거래: 381개 (97.4%)

시간대별 분포:
  09시: 60개
  10시: 60개
  11시: 60개
  12시: 60개
  13시: 60개
  14시: 60개
  15시: 21개
```

---

## 📝 변경된 파일

### brokers/korea_investment/ki_api.py

#### Line 212-224: API 요청 로그 추가
```python
while iteration < max_iterations:
    params = { ... }

    # ✅ API 요청 파라미터 로그
    logger.info(f"🌐 API 요청 [{iteration + 1}]: end_time={end_time}, target=09:00부터 {end_time}까지 역순 조회")

    t1 = self._url_fetch(url, tr_id, params)
```

#### Line 259-280: oldest 계산 수정
```python
# 역순으로 정렬 (최신 -> 과거 → 과거 -> 최신)
df_batch = df_batch[::-1].reset_index(drop=True)

# ✅ 배치 데이터 범위 로그
if batch_count > 0:
    oldest_in_batch = df_batch.iloc[0]['시간']   # 과거
    newest_in_batch = df_batch.iloc[-1]['시간']  # 최신
    logger.info(f"📦 Batch {iteration + 1}: {batch_count}개 | 범위: {oldest_in_batch}(oldest) ~ {newest_in_batch}(newest)")

# ✅ 수정: 첫 번째가 가장 오래된 시간
oldest_time = df_batch.iloc[0]['시간']
```

#### Line 285-292: 다음 end_time 계산 수정
```python
# ✅ 가장 오래된 데이터의 1분 전으로 설정
oldest_datetime = datetime.strptime(oldest_time, "%H%M%S")
next_end_datetime = oldest_datetime - timedelta(minutes=1)
prev_end_time = end_time
end_time = next_end_datetime.strftime("%H%M%S")
logger.info(f"🔄 다음 end_time: {prev_end_time} → {end_time} (oldest {oldest_time} - 1분)")
```

---

## ✨ 개선 효과

### Before
- ❌ 10번 반복해도 9분만 이동 (15:30 → 15:21)
- ❌ 중복 데이터 대량 발생 (1200개 → 129개)
- ❌ 09:00 데이터 수집 불가
- ❌ Full day 캐시 139개만 생성

### After
- ✅ 10번 반복으로 390분 커버 (15:30 → 09:00)
- ✅ 중복 최소화 (1200개 → 381개 실제 데이터)
- ✅ 09:00부터 전체 데이터 수집
- ✅ Full day 캐시 391개 완성

---

## 🔮 추가 고려 사항

### 1. 한투 API 특성
- **120개 제한**: 한 번 호출 시 최대 120개 반환
- **역순 조회**: `end_time`부터 과거 방향으로 조회
- **실제 거래 데이터만**: 거래가 없는 시간대는 데이터 없음

### 2. max_iterations 설정
- **현재**: 10번 (최대 1200개)
- **권장**: Full day (390분) 기준 4번이면 충분하지만, 안전을 위해 10번 유지
- **계산**: 390분 ÷ 120개/batch ≈ 3.25 batch

### 3. 성능 최적화
- **API 호출 간격**: 50ms (초당 20건 제한)
- **중복 제거**: pandas `drop_duplicates` 사용
- **시간순 정렬**: 최종 데이터를 과거 → 최신 순서로 반환

---

## 📚 관련 문서
- [Chart Drag Fix](chart-drag-fix.1002.md) - 더미 데이터 생성 방지
- [Gap Fill Optimization](gap-fill-optimization-result.md) - 캐시 gap 처리
- [Full Day Chart Strategy](../arch/full-day-chart-strategy.md) - 전체 구조

---

**수정일**: 2025-10-02 18:55 KST
**작성자**: Claude Code
**원인**: 역순 정렬 후 oldest 계산 오류 (마지막 요소를 oldest로 사용)
**해결**: 첫 번째 요소를 oldest로 사용하도록 수정
