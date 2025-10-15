# WebSocket 호가 데이터 수신 문제 해결 시도 기록

**날짜**: 2025-10-15  
**시간**: 12:40  
**문제**: 실시간 호가 데이터(H0STASP0)가 수신되지 않음  
**장 운영 시간**: 09:00-15:30 (현재 12:40 - 정상 운영 시간)

## 📋 문제 상황 요약

- **현상**: 프론트엔드에서 호가 데이터가 0으로 표시되고 실시간 업데이트되지 않음
- **목표**: 1초에 2번 이상 호가 데이터가 자동 업데이트되어야 함
- **현재 상태**: Queue에 호가 구독 요청이 쌓여있지만 처리되지 않음 (`ws_req_queue_size: 4`)

## 🔧 시도해본 해결책들

### 1. 폴링 로직 제거 (완료)
**목적**: 원래 문제였던 잘못된 폴링 방식을 제거하고 WebSocket 구독 방식으로 복원

**수정 파일**: `stock-trading-ui/src/hooks/useOrderBook.ts`
- 147-172번 라인의 `setInterval` 폴링 로직 완전 제거
- WebSocket 구독 방식으로 복원

**결과**: ✅ 성공 - 폴링 로직 제거 완료

### 2. 백엔드 Queue 초기화 문제 해결 (완료)
**문제**: `ws_req_queue`와 `ws_result_queue`가 초기화되지 않음
**원인**: `python ./app/main.py`로 실행하여 `lifespan` 함수가 호출되지 않음

**해결책**:
```bash
# 기존 프로세스 종료
pkill -9 -f "python.*main"
lsof -i :8000  # 포트 사용 프로세스 확인
kill -9 <PID>  # 해당 프로세스 강제 종료

# uvicorn으로 재시작
cd /home/wide/projects/systrading/backend
./vkis/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**결과**: ✅ 성공 - Queue 초기화 완료

### 3. domestic_websocket 프로세스 문제 해결 (완료)
**문제**: `domestic_websocket` 프로세스가 `KoreaInvestAPI` 인스턴스를 받지 못함
**원인**: multiprocessing 경계에서 객체 직렬화 문제

**해결책**:
**수정 파일**: `backend/app/domestic_websocket.py`
```python
# 변경 전
def run_websocket(korea_invest_api, ws_url, ws_req_queue, ws_result_queue):

# 변경 후  
def run_websocket(settings, ws_url, ws_req_queue, ws_result_queue):
    # 프로세스 내에서 API 인스턴스 생성
    from app.core.korea_invest import KoreaInvestAPIService
    korea_invest_service = KoreaInvestAPIService(settings)
    korea_invest_api = korea_invest_service.api_instance
```

**수정 파일**: `backend/app/main.py`
```python
# lifespan 함수에서 settings 전달
websocket_process = Process(
    target=run_websocket,
    args=(settings, ws_url, ws_req_queue, ws_result_queue),  # korea_invest_api 대신 settings
    daemon=True
)
```

**결과**: ✅ 성공 - domestic_websocket 프로세스 정상 실행

### 4. "ALREADY IN USE appkey" 오류 해결 (완료)
**문제**: 한국투자증권 API 서버에서 appkey가 이미 사용 중이라고 판단
**원인**: 동일한 appkey로 여러 연결 시도

**해결책**:
```bash
# 기존 토큰 파일 백업 및 삭제
cd /home/wide/projects/systrading/backend
cp access.tok access.tok.backup
rm access.tok

# 새로운 토큰 생성
./vkis/bin/python -c "
from app.core.korea_invest import KoreaInvestAPIService
from app.core.config import get_settings
settings = get_settings()
korea_invest_service = KoreaInvestAPIService(settings)
print('새로운 토큰 생성 완료')
"
```

**결과**: ✅ 성공 - 새로운 토큰 생성 및 appkey 충돌 해결

### 5. 호가 구독 API 테스트 (완료)
**테스트**: `/api/realtime/subscribe/orderbook?stock_code=005930` 호출

**결과**: 
```json
{
  "success": true,
  "message": "종목 005930 호가 구독 시작",
  "stock_code": "005930"
}
```
✅ 성공 - 호가 구독 요청 정상 처리

### 6. 백엔드 완전 재시작 (완료)
**목적**: Queue 처리 문제 해결을 위한 완전한 재시작

**실행**:
```bash
pkill -9 -f "uvicorn"
sleep 3
cd /home/wide/projects/systrading/backend
./vkis/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**결과**: ✅ 성공 - 백엔드 재시작 완료

## ❌ 현재 남은 문제

### Queue 처리 문제 (미해결)
**현상**: 
- `ws_req_queue_size: 4` - Queue에 호가 구독 요청이 쌓여있음
- `ws_result_queue_size: 0` - 결과 Queue는 비어있음
- domestic_websocket 프로세스가 Queue에서 요청을 읽지 못함

**확인된 사항**:
- ✅ domestic_websocket 프로세스 실행 중 (PINGPONG 메시지 수신 확인)
- ✅ 호가 구독 API 호출 성공
- ✅ Queue 초기화 완료
- ❌ Queue에서 호가 구독 요청 처리되지 않음

## 🔍 추가 확인 필요 사항

1. **domestic_websocket 프로세스 상태**: 실제로 Queue를 모니터링하고 있는지 확인
2. **Queue 연결 문제**: domestic_websocket 프로세스가 올바른 Queue 인스턴스를 사용하고 있는지 확인
3. **코드 로직 문제**: Queue 처리 로직에 버그가 있을 수 있음
4. **WebSocket 연결 상태**: 한국투자증권 WebSocket 연결이 정상인지 확인

## 📊 현재 시스템 상태

- **백엔드**: 정상 실행 중 (포트 8000)
- **Queue**: 초기화 완료, 요청 대기 중
- **WebSocket**: PINGPONG 메시지 수신 중
- **토큰**: 새로운 토큰으로 갱신 완료
- **호가 데이터**: 수신되지 않음 (H0STASP0 메시지 없음)

## 🎯 다음 단계

1. Queue 처리 로직 디버깅
2. domestic_websocket 프로세스 내부 상태 확인
3. WebSocket 연결 상태 상세 분석
4. 호가 구독 요청 처리 과정 추적
