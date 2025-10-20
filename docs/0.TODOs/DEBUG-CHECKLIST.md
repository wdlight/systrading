# 🔍 실시간 차트 업데이트 디버그 체크리스트

## 브라우저 Console에서 확인할 항목

### ✅ 1단계: 구독 성공 확인
```
✅ [useRealtimeMinuteCandles] 종목 구독 완료: 005930
```
- **있음** → 2단계로
- **없음** → WebSocket 연결 또는 구독 실패

---

### ✅ 2단계: 데이터 수신 확인
```
🔄 [UPDATE] 분봉 업데이트 메시지 수신
✅ [UPDATE] 분봉 업데이트 처리: 005930 2025-10-20T...
```
- **있음** → 3단계로
- **없음** → Backend가 데이터 브로드캐스트 안 함

---

### ✅ 3단계: 상태 업데이트 확인
```
📊 [RealtimeCandlestickChart] 실시간 분봉 상태: {
  currentCandle: "2025-10-20T09:46:30+09:00",  ← NULL이 아니어야 함!
  finalizedCount: 0,
  ...
}
```

**중요:** 이 로그가 **매 초마다** 나와야 합니다!
- **매 초 나옴** → currentCandle이 업데이트되고 있음 → 4단계로
- **한 번만 나옴** → 컴포넌트 리렌더링 안 됨 → React 문제

---

### ✅ 4단계: useMemo 실행 확인
```
🔄 [Chart] 차트 데이터 병합 시작
🔄 [Chart] 진행 중 분봉 병합: { currentMinute: "...", lastMinute: "..." }
🔄 [Chart] 동일 분봉 업데이트: ...
✅ [Chart] 최종 차트 데이터: 91개 분봉
```

**중요:** 이 로그도 **매 초마다** 나와야 합니다!
- **매 초 나옴** → useMemo가 정상 실행 중 → 5단계로
- **안 나옴** → useMemo 의존성 문제 또는 메모이제이션 차단

---

### ✅ 5단계: 차트 컴포넌트로 전달 확인

Console에서 다음 명령어 실행:
```javascript
// React DevTools 없이 확인
document.querySelector('[data-chart]') // 차트 엘리먼트가 있는지
```

또는 **React DevTools** 설치 후:
1. Components 탭
2. `RealtimeCandlestickChart` 선택
3. Props 확인: `chartData.length` 값 확인

---

## 🚨 시나리오별 해결 방법

### 시나리오 A: 1단계 실패 (구독 안 됨)
**증상:** "종목 구독 완료" 로그 없음

**해결:**
```bash
cd stock-trading-ui
rm -rf .next
pkill -f "next dev"
npm run dev
```

---

### 시나리오 B: 2단계 실패 (데이터 안 옴)
**증상:** UPDATE 메시지 수신 안 됨

**원인:** Backend가 분봉 데이터를 브로드캐스트하지 않음

**확인:**
1. Backend 로그 확인: `tail -f backend/logs/app.log`
2. 현재 시간이 장 시간(09:00-15:30)인지 확인
3. Backend가 체결 데이터를 받고 있는지 확인

---

### 시나리오 C: 3단계 실패 (로그 한 번만 나옴)
**증상:**
- "실시간 분봉 상태" 로그가 초기 1회만 출력
- currentCandle이 계속 null

**원인:** 컴포넌트가 리렌더링되지 않음

**디버그:**
```javascript
// Console에서 실행
// useRealtimeMinuteCandles가 반환하는 값 강제 확인
```

**해결:**
- 부모 컴포넌트에서 props가 변경되지 않는 경우
- 차트 페이지 전체 새로고침 (Ctrl+Shift+R)

---

### 시나리오 D: 3단계 성공했지만 4단계 실패
**증상:**
- "실시간 분봉 상태" 로그는 계속 나옴
- "차트 데이터 병합 시작" 로그는 안 나옴

**원인:** useMemo가 메모이제이션되어 재실행 안 됨

**즉시 확인:**
Console에서 실행:
```javascript
// currentCandle, finalizedCandles 값 확인
console.log('Debug:', {
  currentCandle: window.currentCandle, // 이건 안 될 수 있음
  // React DevTools 필요
});
```

**해결:**
useMemo 의존성 배열 확인 또는 useMemo 제거 테스트

---

### 시나리오 E: 모든 로그 정상인데 차트 안 그려짐
**증상:**
- 모든 로그 정상 출력
- finalChartData에 데이터 있음
- 하지만 차트 화면에 안 보임

**원인:**
1. 차트 라이브러리(Recharts) 렌더링 문제
2. CSS 문제로 차트가 숨겨짐
3. 차트 데이터 포맷 불일치

**확인:**
```javascript
// Console에서
document.querySelector('svg') // 차트 SVG가 있는지
document.querySelectorAll('.recharts-wrapper') // Recharts 컴포넌트
```

---

## 📊 빠른 진단 스크립트

Console에 붙여넣기:
```javascript
console.log('=== 차트 디버그 정보 ===');
console.log('1. WebSocket 연결:', typeof wsManager !== 'undefined' ? wsManager.isConnected() : '❌ wsManager 없음');
console.log('2. 차트 엘리먼트:', document.querySelector('[data-chart]') ? '✅ 있음' : '❌ 없음');
console.log('3. SVG 엘리먼트:', document.querySelector('svg') ? '✅ 있음' : '❌ 없음');

// 5초마다 currentCandle 체크
let checkCount = 0;
const interval = setInterval(() => {
  console.log(`[${++checkCount}초] currentCandle 상태 체크 중...`);
  // React DevTools 없이는 확인 어려움
  if (checkCount >= 5) {
    clearInterval(interval);
    console.log('✅ 5초 모니터링 완료. Console 로그를 확인하세요.');
  }
}, 1000);
```

---

## 🎯 다음 단계

위 체크리스트를 확인하고 **실패한 단계 번호**를 알려주세요:
- 1단계 실패? → WebSocket 구독 문제
- 2단계 실패? → Backend 데이터 문제
- 3단계 실패? → React 리렌더링 문제
- 4단계 실패? → useMemo 문제
- 5단계 실패? → 차트 렌더링 문제

**실패한 단계와 해당 로그를 공유해주시면 정확한 해결책을 제시하겠습니다!**
