Dynamic Watchlist Management Plan v2
Phase 1: WatchlistService 동적 로딩 구조 확립

✅ 목표: 계좌 데이터 기반의 워치리스트 자동 관리

1.1 기본 구조 개선

 get_acct_balance() 호출하여 보유 종목 DataFrame 확보

 보유수량 > 0 종목만 추출 → holding_stocks 리스트 생성

 _update_watchlist_from_holdings(holding_stocks, account_df) 구현

1.2 Diff 기반 업데이트

 기존 워치리스트와 신규 보유 종목 비교

 added, removed, updated 세 가지 결과 도출

 내부 메모리 저장소(DataFrame/Dict) 갱신

 변경 사항 있으면 _broadcast_watchlist_change() 호출

Phase 2: 매매 이벤트 연동

✅ 목표: 매수/매도 시 즉시 워치리스트 반영

2.1 Trading API 확장

 POST /execute-buy/{stock_code}

 POST /execute-sell/{stock_code}

 응답 구조에 success, message, stock_code, qty 포함

2.2 Optimistic Update 적용

 매수 시 → 즉시 워치리스트에 추가 후, sync_with_account()로 보정

 매도 시 → 보유량 0이면 즉시 제거, 이후 sync_with_account()로 재확인

 handle_trade_event(stock_code, trade_type) → 공통 처리 엔트리 포인트

Phase 3: WebSocket 실시간 전송

✅ 목표: 워치리스트 변경 사항을 클라이언트에 즉시 반영

3.1 메시지 구조 세분화
{
  "type": "watchlist_changed",
  "changes": {
    "added": ["005930"],
    "removed": ["000660"],
    "updated": []
  },
  "full_list": [...],
  "timestamp": 1694823489
}


 broadcast_watchlist_change() 수정 → diff + full list 함께 전송

 다중 연결 환경 고려 → asyncio.Queue 또는 broadcast manager 적용

3.2 WebSocket 이벤트 타입

 watchlist_changed 추가

 기존 가격 업데이트 이벤트와 혼동되지 않도록 별도 분기 처리

Phase 4: 주기적 계좌 동기화

✅ 목표: 계좌 상태와 워치리스트 간 100% 동기화

4.1 동기화 태스크 설계

 async def periodic_sync(interval=30) 구현

 30초 주기로 get_acct_balance() 호출

 동기화 중 이벤트 발생 시 → Lock 사용으로 충돌 방지

4.2 에러/지연 대응

 API 실패 시 → exponential backoff (30s → 60s → 120s)

 동기화 실패 시 → 마지막 워치리스트 유지 + 로그 기록

Phase 5: Frontend 반영

✅ 목표: 클라이언트에서 실시간 워치리스트 UI 자동 업데이트

5.1 WebSocket 처리

 WS_MESSAGE_TYPES.WATCHLIST_CHANGED 등록

 수신 시 notifyListeners(type, data) 호출

5.2 상태 관리 최적화

 단순 setWatchlist([...data]) → 성능 저하 가능

 변경 타입별 업데이트 적용:

switch (change.type) {
  case "added":
    setWatchlist(prev => [...prev, ...change.added]);
    break;
  case "removed":
    setWatchlist(prev => prev.filter(s => !change.removed.includes(s)));
    break;
  case "updated":
    // 보유수량/평단가 변경 시 반영
}

5.3 연결 안정성

 WebSocket 끊김 시 자동 reconnect

 reconnect 후 초기 get_acct_balance() 호출 → 최신 상태 보정

Phase 6: 테스트 & 검증

✅ 목표: 주요 시나리오에서 동작 보장

6.1 단위 테스트

 WatchlistService: diff 계산 검증

 Trading API: optimistic update + 동기화 결과 확인

6.2 시뮬레이션 테스트

 Mock KoreaInvestService 작성 (가짜 계좌 상태 주입 가능)

 매수/매도 시나리오 검증:

신규 매수 → watchlist 추가됨?

전량 매도 → 제거됨?

부분 매도 → 수량 갱신됨?

6.3 E2E 테스트

 WebSocket 메시지 정상 수신 여부

 다중 클라이언트 동시 연결 시 broadcast 정상 동작

 WS 끊김 후 재연결 시 watchlist 복원

📈 예상 효과 (재정리)

✅ 보유 종목과 워치리스트 100% 동기화

✅ 매수/매도 시 즉시 UI 반영 (Optimistic update + 보정)

✅ 실시간 WebSocket 반영으로 사용자 경험 강화

✅ 안정적인 복구 및 에러 대응 구조 확보