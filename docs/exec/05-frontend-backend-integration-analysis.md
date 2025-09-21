# Phase 4: 프론트엔드-백엔드 통합 분석

## 진행 상황

### ✅ 완료된 작업
1. **백엔드 CORS 문제 해결** - API 호출이 성공적으로 작동
2. **프론트엔드 코드 구조 분석** - 기존 API 클라이언트 및 타입 시스템 파악 
3. **데이터 플로우 분석** - 현재 시스템의 데이터 흐름 이해

### 🔄 현재 작업 중
- **더미 데이터를 실제 API 호출로 교체** - 데이터 구조 매핑 및 변환 작업

## 현재 상태 분석

### 1. 백엔드 API 상태
- **서버**: `simple_server.py` (포트 8000)
- **CORS**: 설정 완료 (localhost:3002 포함)
- **주요 엔드포인트**: 
  - `/api/account/balance` ✅ 200 OK
  - `/api/watchlist` ✅ 200 OK  
  - `/api/market/overview` ✅ 200 OK
  - `/api/trading/conditions` ✅ 200 OK
- **실제 한국투자증권 API**: 연동 완료 (실제 계좌 데이터 반환)

### 2. 프론트엔드 상태
- **서버**: Next.js (포트 3002)
- **API 클라이언트**: `TradingAPIClient` 클래스 구현 완료
- **타입 시스템**: 백엔드 API와 일치하는 TypeScript 타입 정의
- **WebSocket**: 구현되어 있지만 데이터 매핑 필요

### 3. 데이터 구조 비교

#### 백엔드에서 반환하는 WatchlistItem 구조:
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자", 
  "current_price": 78000,
  "change": 1000,
  "change_rate": 1.3,
  "rsi": 45.2,
  "macd": 120.5,
  "macd_signal": 118.3,
  "in_watchlist": true
}
```

#### 프론트엔드 WatchlistItem 타입:
```typescript
interface WatchlistItem {
  stock_code: string;
  stock_name?: string;
  current_price: number;
  profit_rate: number;          // ⚠️ 백엔드: 없음
  avg_price: number | null;     // ⚠️ 백엔드: 없음
  quantity: number;             // ⚠️ 백엔드: 없음
  macd: number;
  macd_signal: number;
  rsi: number;
  trailing_stop_activated: boolean;  // ⚠️ 백엔드: 없음
  trailing_stop_high: number;       // ⚠️ 백엔드: 없음
  volume: number;               // ⚠️ 백엔드: 없음
  change_amount: number;        // ⚠️ 백엔드: change
  change_rate: number;
  yesterday_price: number;      // ⚠️ 백엔드: 없음
  high_price: number;           // ⚠️ 백엔드: 없음
  low_price: number;            // ⚠️ 백엔드: 없음
  updated_at: string;           // ⚠️ 백엔드: 없음
}
```

## 발견된 이슈

### 1. 데이터 구조 불일치
- 프론트엔드가 기대하는 필드들이 백엔드에서 제공되지 않음
- 특히 `profit_rate`, `avg_price`, `quantity` 등 중요 필드 누락
- 워치리스트와 보유종목(포지션) 데이터가 혼재

### 2. 데이터 소스 분리 필요
백엔드에서 두 가지 다른 데이터를 제공해야 함:
- **워치리스트**: 관심종목 (price, technical indicators)
- **포지션**: 보유종목 (profit_rate, avg_price, quantity)

### 3. 실제 PyQt5 시스템과의 연계
- `rsimacd_trading.py`의 `realtime_watchlist_df`와 데이터 구조 맞춰야 함
- 매수/매도 후 워치리스트 업데이트 로직 필요

## 해결 방안

### 1. 백엔드 API 수정
```python
# simple_server.py 수정 필요
@app.get("/api/watchlist")
async def get_watchlist():
    # PyQt5 realtime_watchlist_df 구조와 일치하도록 수정
    return [
        {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "current_price": 78000,
            "profit_rate": 4.0,      # 수익률 추가
            "avg_price": 75000,      # 평균단가 추가  
            "quantity": 10,          # 보유수량 추가
            "macd": 120.5,
            "macd_signal": 118.3, 
            "rsi": 45.2,
            "volume": 1000000,       # 거래량 추가
            "change_amount": 1000,   # change -> change_amount
            "change_rate": 1.3,
            "yesterday_price": 77000,  # 전일종가 추가
            "high_price": 79000,       # 당일고가 추가
            "low_price": 76000,        # 당일저가 추가
            "trailing_stop_activated": false,
            "trailing_stop_high": 0,
            "updated_at": "2025-09-10T22:18:00Z"
        }
    ]
```

### 2. 프론트엔드 useRealtimeData 수정
현재 API 호출이 성공하고 있지만, 데이터 매핑 로직 필요:
```typescript
// 백엔드 응답을 프론트엔드 타입으로 변환하는 로직 추가
const mapBackendToFrontend = (backendData: BackendWatchlistItem[]): WatchlistItem[] => {
  return backendData.map(item => ({
    ...item,
    change_amount: item.change || 0,
    volume: item.volume || 0,
    profit_rate: item.profit_rate || 0,
    avg_price: item.avg_price || null,
    quantity: item.quantity || 0,
    // ... 나머지 필드 매핑
  }));
};
```

### 3. WebSocket 데이터 형식 통일
```typescript
// WebSocket 메시지도 동일한 구조로 변환 필요
interface WatchlistUpdate {
  type: 'watchlist_update';
  data: WatchlistItem[];  // 변환된 데이터
}
```

## 다음 단계

### 1. 백엔드 수정 (우선순위 1)
- [ ] `simple_server.py`의 `/api/watchlist` 엔드포인트 수정
- [ ] PyQt5 `realtime_watchlist_df` 구조 참조하여 완전한 데이터 제공
- [ ] 실제 매매 데이터 (profit_rate, avg_price, quantity) 포함

### 2. 프론트엔드 데이터 매핑 (우선순위 2)  
- [ ] 백엔드 응답을 프론트엔드 타입으로 변환하는 유틸리티 함수 작성
- [ ] `useRealtimeData` 훅에서 데이터 변환 로직 적용
- [ ] WebSocket 메시지 형식도 통일

### 3. 실시간 업데이트 구현 (우선순위 3)
- [ ] WebSocket을 통한 실시간 가격/지표 업데이트
- [ ] 매매 체결 시 워치리스트 즉시 반영
- [ ] UI 상태 관리 최적화

### 4. 에러 처리 및 사용자 경험 개선 (우선순위 4)
- [ ] API 호출 실패 시 폴백 처리
- [ ] 로딩 상태 표시 개선
- [ ] 실시간 연결 상태 표시

## 기술적 세부사항

### 현재 작동 중인 부분
- ✅ CORS 해결
- ✅ API 엔드포인트 호출 성공
- ✅ 실제 한국투자증권 API 연동
- ✅ WebSocket 연결

### 수정 필요한 부분
- ⚠️ 데이터 구조 불일치
- ⚠️ 워치리스트 vs 포지션 데이터 구분
- ⚠️ 실시간 업데이트 데이터 매핑
- ⚠️ 매매 체결 후 데이터 반영

### 예상 소요 시간
- 백엔드 수정: 1-2시간
- 프론트엔드 매핑: 1시간  
- 통합 테스트: 1시간
- **총 예상**: 3-4시간

## 결론

프론트엔드와 백엔드 간의 연결은 이미 성공적으로 구축되었습니다. 주요 이슈는 데이터 구조의 불일치이며, 이는 백엔드에서 PyQt5 시스템과 일치하는 완전한 데이터를 제공함으로써 해결할 수 있습니다. 

다음 단계는 백엔드 API 수정 후 프론트엔드에서 데이터 매핑을 통해 완전한 통합을 달성하는 것입니다.