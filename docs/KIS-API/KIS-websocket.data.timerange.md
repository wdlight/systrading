# KIS WebSocket 데이터 타임라인 및 로깅 시스템

## 개요
한국투자증권 WebSocket을 통해 수신되는 실시간 데이터의 타임라인과 로깅 시스템에 대한 문서입니다.

## WebSocket 메시지 타입별 데이터 흐름

### 1. 호가 데이터 (H0STASP0)
- **TR_ID**: H0STASP0
- **데이터 형식**: 종목코드^매수10호가^...^매수1호가^매도1호가^...^매도10호가^매수10호가수량^...^매도10호가수량
- **업데이트 주기**: 실시간 (변동 시)
- **장 시간**: 09:00 ~ 15:30 (정규장), 08:30 ~ 09:00 (시간외 종가), 15:30 ~ 16:00 (시간외 단일가)

### 2. 체결 데이터 (H0STCNI0)
- **TR_ID**: H0STCNI0
- **데이터 형식**: 주문체결통보 데이터
- **업데이트 주기**: 체결 발생 시
- **장 시간**: 09:00 ~ 15:30 (정규장), 08:30 ~ 09:00 (시간외 종가), 15:30 ~ 16:00 (시간외 단일가)

### 3. 지수 데이터 (H0STISE0)
- **TR_ID**: H0STISE0
- **데이터 형식**: 실시간 지수 정보
- **업데이트 주기**: 2초마다
- **장 시간**: 09:00 ~ 15:30

## 로깅 시스템

### 샘플링 로깅 방식
데이터가 많을 경우 로그 스팸을 방지하기 위해 샘플링 로깅을 사용합니다:

1. **시간 기반 샘플링**: 1분마다 로그 출력
2. **카운트 기반 샘플링**: 100개 메시지마다 로그 출력
3. **첫 번째 메시지**: 항상 로그 출력

### 로그 레벨별 분류
- **INFO**: 호가 데이터, 지수 업데이트, 계좌 업데이트, 거래 상태, 주문 업데이트, 시장 상태
- **DEBUG**: 가격 업데이트, 워치리스트 업데이트 (빈번한 메시지)
- **WARNING**: 연결 상태 (중요한 상태 변화)

### 로그 형식
```
📡 WebSocket [backend] orderbook_update (1번째) @ 18:16:54.804
{
  "type": "orderbook_update",
  "stock_code": "005930",
  "data": {
    "asks": [...],
    "bids": [...],
    "timestamp": "2025-10-14T18:16:54.804981"
  }
}
```

## 장 시간 외 처리

### 장 시간 체크 로직
```python
from app.utils.trading_hours import TradingHoursManager

# 정규장 시간 체크
if TradingHoursManager.is_trading_hours(current_time, include_extended=True):
    # 정상 데이터 처리
else:
    # 장 시간 외 처리
```

### 장 시간 외 상태 메시지
```json
{
  "type": "market_status_update",
  "data": {
    "status": "closed",
    "session": "closed",
    "message": "장 시간 외입니다. 다음 거래일 09:00에 다시 시작됩니다.",
    "next_open": "2025-10-15T09:00:00",
    "last_data_timestamp": "2025-10-14T15:30:00"
  }
}
```

## 통계 및 모니터링

### WebSocket 통계 API
- **GET** `/monitoring/websocket-stats`: 메시지 통계 조회
- **POST** `/monitoring/websocket-stats/reset`: 통계 초기화

### 통계 정보 예시
```json
{
  "success": true,
  "data": {
    "total_messages": 1250,
    "message_types": 5,
    "timestamp": "2025-10-14T18:16:54.804981",
    "details": {
      "orderbook_update": {
        "total_count": 800,
        "last_log_count": 700,
        "time_since_last_log": 45.2,
        "buffer_size": 10
      },
      "price_update": {
        "total_count": 400,
        "last_log_count": 300,
        "time_since_last_log": 12.5,
        "buffer_size": 8
      }
    }
  }
}
```

## 성능 최적화

### 배치 처리
- 메시지를 10개씩 묶어서 처리
- 배치 타임아웃: 0.001초
- 병렬 처리로 성능 향상

### 선택적 브로드캐스트
- 종목별 구독자에게만 전송
- 불필요한 네트워크 트래픽 감소
- 구독자 수 추적

### 백프레셔 처리
- Queue 크기 모니터링
- 임계치 초과 시 처리 지연
- Circuit Breaker 패턴 적용

## 문제 해결

### 장 시간 외 에러 방지
1. **API 호출 제한**: 장 시간 외 KIS API 호출 방지
2. **마지막 데이터 유지**: 장 시간 외에도 마지막 데이터 제공
3. **상태 메시지**: 명확한 장 시간 외 안내

### 로그 관리
1. **자동 샘플링**: 과도한 로그 방지
2. **통계 주기적 출력**: 5분마다 통계 로그
3. **버퍼 관리**: 최근 10개 메시지 저장

### 연결 관리
1. **자동 재연결**: 연결 끊김 시 자동 복구
2. **하트비트**: 30초마다 연결 상태 확인
3. **구독자 정리**: 비활성 구독자 자동 제거

## 설정값

### 샘플링 설정
- `sample_interval_seconds`: 60초 (1분)
- `sample_count_threshold`: 100개
- `max_log_size`: 1000자

### 성능 설정
- `batch_size`: 10개
- `batch_timeout`: 0.001초
- `heartbeat_interval`: 30초

### 통계 설정
- `stats_log_interval`: 300초 (5분)
- `buffer_size`: 10개
- `max_connections`: 100개
