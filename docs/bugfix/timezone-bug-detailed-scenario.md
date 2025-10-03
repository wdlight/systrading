# Timezone 버그 상세 시나리오

## 🐛 버그 발생 시나리오

### 📅 **상황 설정**

```
날짜: 2025년 10월 4일 (금요일)
시간: 오전 2시 00분 (KST)
위치: 대한민국 서울
사용자: 주식 트레이더가 새벽에 전날 거래 결과를 확인하려고 차트 앱 접속
```

---

## 🔍 **버그 발생 과정 (Step-by-Step)**

### **Step 1: 사용자가 "오늘" 차트 조회**

사용자가 브라우저에서 차트 페이지 접속:
```
URL: http://localhost:9000/trading
시간: 2025-10-04 02:00:00 (금요일 새벽 2시)
```

---

### **Step 2: JavaScript 코드 실행 (수정 전)**

#### **코드 실행 위치**: `useRealChartData.ts:87` (수정 전)

```typescript
// 수정 전 코드
const isToday = !targetDate || targetDate === new Date().toISOString().split('T')[0];
```

#### **JavaScript 내부 동작**:

```javascript
// 1. 현재 시간 객체 생성
const now = new Date();
// → 브라우저가 로컬 타임존(KST)으로 객체 생성
// → 내부값: 2025-10-04 02:00:00 KST

// 2. ISO 문자열 변환 (UTC 기준!)
now.toISOString();
// → "2025-10-03T17:00:00.000Z"
// → ⚠️ 주의: UTC는 KST보다 9시간 느림!
// → KST 10월 4일 02:00 = UTC 10월 3일 17:00

// 3. 날짜 부분만 추출
const utcDate = now.toISOString().split('T')[0];
// → "2025-10-03"  ❌ 목요일!
```

---

### **Step 3: "오늘" 판단 (잘못된 결과)**

#### **시나리오 A: 명시적 날짜 지정 (사용자가 날짜 선택)**

```typescript
// 사용자가 캘린더에서 "2025-10-04" 선택
const targetDate = "2025-10-04"; // 금요일

// 코드 실행
const utcToday = new Date().toISOString().split('T')[0]; // "2025-10-03"
const isToday = targetDate === utcToday;
// → "2025-10-04" === "2025-10-03"
// → false ❌

// 결과: 금요일을 선택했는데 "과거 날짜"로 인식!
```

#### **시나리오 B: 날짜 지정 없음 (기본값으로 오늘 조회)**

```typescript
// targetDate가 undefined (기본값)
const targetDate = undefined;

// 코드 실행
const isToday = !targetDate || targetDate === new Date().toISOString().split('T')[0];
// → true || (undefined === "2025-10-03")
// → true ✅ (논리 OR의 첫 번째 조건이 true)

// 하지만 문제는...
// 어딘가에서 "오늘 날짜"를 계산할 때 UTC 사용!
```

---

### **Step 4: API 호출 (잘못된 엔드포인트)**

#### **수정 전 코드 흐름**:

```typescript
// useRealChartData.ts:87-89
const isToday = !targetDate || targetDate === new Date().toISOString().split('T')[0];
const endpoint = isToday ? 'minute/full' : 'minute';
```

#### **API 호출 결과**:

**Case 1**: 명시적으로 "2025-10-04" 선택
```javascript
isToday = false  // ❌ (10-04 !== 10-03)
endpoint = 'minute'  // 과거 데이터용 API

// API 호출:
GET /api/chart/005930/minute?date=2025-10-04

// 백엔드 응답:
// - 2025-10-04의 실제 거래 데이터만 반환 (gap-fill 없음)
// - 새벽 2시에는 거래 데이터가 없으므로 빈 배열 또는 전날 데이터 반환
// → 사용자는 "오늘 차트"를 보고 싶었는데 빈 화면 또는 어제 데이터 표시!
```

**Case 2**: useHistoricalChartData에서 "오늘" 계산
```typescript
// useHistoricalChartData.ts:111 (수정 전)
const today = new Date().toISOString().split('T')[0];
// → "2025-10-03"  ❌

// API 호출:
GET /api/chart/005930/minute?date=2025-10-03

// 결과:
// - 사용자는 금요일(10-04) 데이터를 원함
// - 앱은 목요일(10-03) 데이터를 조회
// → 하루 전 차트가 표시됨! ❌
```

---

## 🔴 **버그 증상 (사용자 관점)**

### **증상 1: 차트가 업데이트되지 않음**

```
사용자 행동:
- 금요일 새벽 2시에 앱 접속
- "오늘" 차트 조회

기대 결과:
- 금요일 09:00~15:30 시간대 표시 (gap-fill)
- 현재는 02:00이므로 09:00~15:30 모두 미래 → 전일 종가로 채워짐

실제 결과 (버그):
- 목요일 차트가 표시됨
- 또는 빈 화면 (금요일 데이터를 요청했지만 과거 API로 조회했으므로)
```

### **증상 2: 날짜 선택 시 잘못된 데이터**

```
사용자 행동:
- 금요일 새벽 2시에 앱 접속
- 캘린더에서 "2025-10-04" (금요일) 선택

기대 결과:
- 금요일 차트 표시 (gap-fill 포함)

실제 결과 (버그):
- "/minute" 엔드포인트 호출 (과거 데이터용)
- gap-fill 없이 실제 거래 데이터만 조회
- 새벽 2시에는 거래가 없으므로 빈 배열 반환
- 화면에 아무것도 표시 안됨!
```

### **증상 3: 과거 데이터 로딩 오류**

```
사용자 행동:
- 금요일 새벽 2시에 앱 접속
- 차트를 좌측으로 드래그 (과거 데이터 로드)

기대 결과:
- 목요일(10-03), 수요일(10-02) 데이터 로드

실제 결과 (버그):
- useHistoricalChartData가 "오늘"을 10-03으로 계산
- 10-02, 10-01 데이터를 로드 (하루씩 밀림)
- 사용자는 10-03 데이터를 원했는데 10-02 데이터 표시
```

---

## ✅ **수정 후 동작 (KST 기준)**

### **Step 1: KST 기준 날짜 계산**

```typescript
// lib/utils/datetime.ts
export function getKSTToday(): string {
  const now = new Date();
  const kstOffset = 9 * 60; // 9시간 = 540분
  const kstTime = new Date(now.getTime() + kstOffset * 60 * 1000);
  return kstTime.toISOString().split('T')[0];
}
```

### **Step 2: 실행 결과**

```javascript
// 한국 시간: 2025-10-04 02:00
const now = new Date(); // KST 2025-10-04 02:00

// KST 변환
const kstOffset = 9 * 60 * 60 * 1000; // 9시간을 밀리초로
const kstTime = new Date(now.getTime() + kstOffset);
// → UTC 기준 2025-10-04 11:00 (실제 KST 2025-10-04 20:00이지만 날짜만 필요)

kstTime.toISOString().split('T')[0];
// → "2025-10-04" ✅ 금요일!
```

### **Step 3: 정확한 API 호출**

```typescript
// useRealChartData.ts (수정 후)
const todayKST = getKSTToday(); // "2025-10-04"
const checkDate = targetDate || todayKST;
const isTodayKST = isKSTToday(checkDate);
// → true ✅

const endpoint = isTodayKST ? 'minute/full' : 'minute';
// → 'minute/full' ✅

// API 호출:
GET /api/chart/005930/minute/full?date=2025-10-04

// 백엔드 응답:
// - 금요일 09:00~15:30 전체 시간대 데이터 (391개 캔들)
// - 현재(02:00) 이후는 전일 종가로 gap-fill
// → 사용자가 원하는 "오늘" 차트 정상 표시! ✅
```

---

## 📊 **버그 영향 범위**

### **시간대별 버그 발생률**

| 시간대 (KST) | UTC 날짜 | KST 날짜 | 날짜 일치? | 버그 발생? |
|-------------|---------|---------|-----------|-----------|
| 00:00 ~ 08:59 | 전날 | 당일 | ❌ 불일치 | ✅ **발생** |
| 09:00 ~ 23:59 | 당일 | 당일 | ✅ 일치 | ❌ 정상 |

**버그 발생 확률**: 9시간 / 24시간 = **37.5%**

### **영향받는 사용자**

1. **새벽 트레이더**: 전날 거래 결과 확인하려는 사용자
2. **해외 거주자**: 시차로 인해 새벽 시간대에 접속하는 사용자
3. **자동화 시스템**: cron 작업 등이 자정~오전 9시에 실행되는 경우

---

## 🎯 **수정 효과**

### **Before (UTC 기준)**
```
자정~오전 9시: 하루 전 차트 표시 ❌
오전 9시~자정: 정상 표시 ✅
```

### **After (KST 기준)**
```
자정~오전 9시: 정상 표시 ✅
오전 9시~자정: 정상 표시 ✅
```

**24시간 내내 정확한 "오늘" 차트 제공!** ✅
