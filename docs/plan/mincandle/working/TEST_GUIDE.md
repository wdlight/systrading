# 실시간 분봉 캐시 연동 테스트 가이드

**테스트 대상**: WebSocket → 캐시 파일 자동 저장 기능
**테스트 날짜**: 2025-10-19
**테스터**: ___________

---

## ✅ 사전 준비

### 1. Backend 재시작
```bash
cd /home/wide/projects/systrading/backend
./scripts/restart_backend.sh
```

### 2. 로그 파일 준비
```bash
# 새 터미널 창 열기
cd backend
tail -f logs/app.log | grep -E "Persistence|Startup"
```

### 3. Frontend 시작 (별도 터미널)
```bash
cd /home/wide/projects/systrading/stock-trading-ui
npm run dev
```

---

## 🧪 Test Case 1: Handler 연결 확인

### 목표
서버 시작 시 persistence handler가 정상적으로 주입되었는지 확인

### 절차
1. Backend 재시작
2. 로그 확인

### 기대 결과
```
🔗 [Startup] 분봉 Persistence Handler 연결 완료
```

### 실제 결과
- [ ] ✅ 성공: 로그 출력됨
- [ ] ❌ 실패: 로그 없음
- 메모: _______________________

---

## 🧪 Test Case 2: 분봉 캐시 저장 확인

### 목표
1분 경계가 지나면 WebSocket 분봉이 자동으로 캐시에 저장되는지 확인

### 절차
1. 장 시간 대기 (09:00 ~ 15:30)
2. 1분 경과 후 로그 확인
3. 캐시 파일 확인

### 명령어
```bash
# 로그 모니터링
tail -f backend/logs/app.log | grep "Persistence"

# 캐시 파일 모니터링
watch -n 1 'ls -lh backend/kordata/005930/*.json'

# 캐시 파일 내용 확인 (마지막 분봉)
cat backend/kordata/005930/$(date +%Y%m%d).json | jq '.[-1]'
```

### 기대 결과
**로그**:
```
✅ [Persistence] 분봉 캐시 저장 성공: 005930 2025-10-19T14:35:00+09:00 (O:62000 H:62200 L:61900 C:62100 V:1500)
```

**파일**:
- 1분마다 수정 시간 업데이트
- 마지막 분봉이 최신 데이터

### 실제 결과
- [ ] ✅ 성공: 로그 및 파일 정상
- [ ] ❌ 실패: 저장 안 됨
- 파일 수정 시간: _______________________
- 메모: _______________________

---

## 🧪 Test Case 3: Frontend Finalize 이벤트 수신

### 목표
Frontend가 `minute_candle_finalize` WebSocket 메시지를 정상 수신하는지 확인

### 절차
1. http://localhost:9000/trading 접속
2. Chrome DevTools → Console 열기
3. 아래 코드 실행:

```javascript
// WebSocket 메시지 모니터링
const originalOnMessage = WebSocket.prototype.onmessage;
WebSocket.prototype.onmessage = function(event) {
  const data = JSON.parse(event.data);

  if (data.type === 'minute_candle_update') {
    console.log('🔄 Update 수신:', data.stock_code, data.data.timestamp);
  }

  if (data.type === 'minute_candle_finalize') {
    console.log('🎉 Finalize 수신:', data.stock_code, data.data.timestamp, data.data);
  }

  return originalOnMessage.apply(this, arguments);
};
```

4. 삼성전자(005930) 선택
5. 1분 타임프레임 선택
6. 1분 경과 후 Console 확인

### 기대 결과
**Console 출력**:
```
🔄 Update 수신: 005930 2025-10-19T14:34:30+09:00
🔄 Update 수신: 005930 2025-10-19T14:34:45+09:00
🎉 Finalize 수신: 005930 2025-10-19T14:34:00+09:00 {open: 62000, high: 62200, ...}
🔄 Update 수신: 005930 2025-10-19T14:35:05+09:00  (새 분봉 시작)
```

### 실제 결과
- [ ] ✅ 성공: Finalize 메시지 수신됨
- [ ] ❌ 실패: Update만 수신됨
- 메모: _______________________

---

## 🧪 Test Case 4: 차트 자동 업데이트

### 목표
REST API 호출 없이 완성된 분봉이 차트에 자동 추가되는지 확인

### 절차
1. http://localhost:9000/trading 접속
2. 삼성전자 선택, 1분 타임프레임
3. Chrome DevTools → Network 탭 열기
4. 1분 경과 후:
   - Network 탭에서 `/api/chart/` 호출 없는지 확인
   - 차트가 자동 업데이트되는지 확인

### 기대 결과
- Network 탭: `/api/chart/005930/minute/full` 호출 **없음**
- 차트: 새 분봉이 자동으로 추가됨 (REST 호출 없이)

### 실제 결과
- [ ] ✅ 성공: 차트 자동 업데이트, REST 호출 없음
- [ ] ❌ 실패: REST API가 호출됨
- Network 호출 횟수: _______________________
- 메모: _______________________

---

## 🧪 Test Case 5: 5분 공백 시나리오

### 목표
종목 전환 후 돌아왔을 때 누락된 분봉이 캐시에서 정상 로드되는지 확인

### 절차
1. **T=0:00** - 삼성전자 차트 확인
2. **T=0:01** - 하이닉스로 전환 (5분 대기)
3. **T=5:00** - 다시 삼성전자로 전환
4. Network 탭 확인
5. Backend 로그 확인

### 명령어
```bash
# Backend 로그 모니터링
tail -f backend/logs/app.log | grep -E "Persistence|fill_gap"
```

### 기대 결과
**Backend 로그**:
- 5분간 계속 "✅ [Persistence] 분봉 캐시 저장 성공" 출력
- 삼성전자로 복귀 시 `fill_gap` 트리거 **안 됨** (또는 gap이 매우 작음)

**Frontend Network**:
- `/api/chart/005930/minute/full` 1회 호출
- Response에 5분간의 분봉 모두 포함

### 실제 결과
- [ ] ✅ 성공: Gap fill 없이 캐시에서 로드
- [ ] ⚠️ 부분 성공: Gap fill 발생했으나 gap 작음 (< 2분)
- [ ] ❌ 실패: 큰 gap 발생
- Gap 크기: _______ 분
- 메모: _______________________

---

## 🧪 Test Case 6: 메모리 누수 확인

### 목표
종목을 여러 번 전환해도 `finalizedCandles` 메모리 누수가 없는지 확인

### 절차
1. Chrome DevTools → Memory 탭 → Take Heap Snapshot
2. 종목 10회 전환 (삼성전자 ↔ 하이닉스 반복)
3. Take Heap Snapshot 다시
4. 두 스냅샷 비교

### 기대 결과
- Heap 증가량 < 5MB
- `finalizedCandles` 배열이 종목 전환 시 초기화됨

### 실제 결과
- [ ] ✅ 성공: 메모리 누수 없음
- [ ] ❌ 실패: 메모리 계속 증가
- Heap 증가량: _______ MB
- 메모: _______________________

---

## 🧪 Test Case 7: 에러 처리 (선택)

### 목표
캐시 저장 실패 시 로그가 정상 출력되는지 확인

### 절차
1. 캐시 디렉토리 권한 제거:
   ```bash
   chmod 000 backend/kordata/005930/
   ```

2. 1분 경과 후 로그 확인

3. 권한 복구:
   ```bash
   chmod 755 backend/kordata/005930/
   ```

### 기대 결과
**로그**:
```
❌ [Persistence] 분봉 저장 오류: 005930 2025-10-19T14:35:00+09:00 - [Errno 13] Permission denied
```

### 실제 결과
- [ ] ✅ 성공: 에러 로그 정상 출력
- [ ] ❌ 실패: 에러 로그 없음
- 메모: _______________________

---

## 📊 테스트 결과 요약

| Test Case | 상태 | 비고 |
|-----------|------|------|
| 1. Handler 연결 확인 | ⬜ | |
| 2. 분봉 캐시 저장 | ⬜ | |
| 3. Frontend Finalize 수신 | ⬜ | |
| 4. 차트 자동 업데이트 | ⬜ | |
| 5. 5분 공백 시나리오 | ⬜ | |
| 6. 메모리 누수 확인 | ⬜ | |
| 7. 에러 처리 (선택) | ⬜ | |

**전체 통과율**: _____ / 7

---

## 🚨 발견된 이슈

### Issue 1
- **설명**: _______________________
- **재현 방법**: _______________________
- **우선순위**: 🔴 높음 / 🟡 중간 / 🟢 낮음
- **해결 방안**: _______________________

### Issue 2
- **설명**: _______________________
- **재현 방법**: _______________________
- **우선순위**: 🔴 높음 / 🟡 중간 / 🟢 낮음
- **해결 방안**: _______________________

---

## ✅ 최종 승인

- [ ] 모든 핵심 테스트 통과 (1~5번)
- [ ] 로그가 정상적으로 출력됨
- [ ] 캐시 파일이 1분마다 업데이트됨
- [ ] Frontend 차트가 REST 호출 없이 자동 업데이트됨
- [ ] 메모리 누수 없음

**승인자**: _______________________
**승인 날짜**: _______________________
**배포 가능 여부**: ⬜ Yes / ⬜ No

---

**참고 문서**:
- `docs/plan/mincandle/1019.implementation-summary.md` - 구현 완료 보고서
- `docs/plan/mincandle/1019.update.impl.md` - 상세 구현 계획
