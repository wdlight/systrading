# PRD v1.1 - 통합 자산관리 및 자동매매 플랫폼

## 1. 제품 개요

### 1.1 비전
"50대 투자자를 위한 쉽고 안전한 자산관리 자동화 플랫폼 - 복잡한 투자를 단순하게"

### 1.2 미션
- 흩어진 자산의 통합 관리로 투자 현황 한눈에 파악
- 기술적 지표 기반 위험/기회 평가로 안전한 투자 지원
- 맞춤형 자동매매로 전문가 수준의 투자 전략 실행

### 1.3 핵심 가치
- **단순성**: 50대도 쉽게 사용할 수 있는 직관적 UI
- **안전성**: 검증된 지표 기반 리스크 관리
- **확장성**: 개인 투자자부터 전문가까지 성장 가능한 플랫폼
- **맞춤형**: SI 형태의 커스텀 전략 구현 가능

## 2. 타겟 사용자

### Primary Persona - 개인 투자자
- **박안정 (52세, 자영업/은퇴 준비)**
  - 자산 규모: 3-10억원
  - 투자 경험: 있으나 체계적 관리 부족
  - 니즈: 안전한 자산 보존 + 적정 수익
  - Pain Point: 복잡한 차트 분석 어려움, 시간 부족
  - 원하는 것: "위험한지 안전한지만 알려주세요"

### Secondary Persona - 전문 투자자
- **김시스템 (45세, 전업 투자자)**
  - 자산 규모: 10억원 이상
  - 투자 경험: 고급, 자체 매매 전략 보유
  - 니즈: 자동화된 시스템 트레이딩
  - Pain Point: 아이디어는 있으나 구현 능력 부족
  - 원하는 것: "내 전략을 코드로 만들어 자동 실행"

## 3. MVP 핵심 기능 (1차 구현)

### 3.1 계좌 연동 및 실시간 차트
**구현 범위**
- 한국투자증권 단일 연동
- 실시간 계좌 정보 조회
  - 보유 종목 리스트
  - 매입가/현재가/수익률
  - 계좌 잔고
- 종목별 실시간 차트
  - 분/일/주/월 봉
  - 거래량 표시
  - 기본 보조지표 (이동평균선)

### 3.2 기본 매매 기능
- 시장가/지정가 주문
- 매수/매도 주문
- 주문 내역 조회
- 체결 내역 확인

### 3.3 위험도/기회 평가 시스템
**평가 지표**
```
위험도 점수 (1-10):
- RSI > 70: 과매수 위험 (+3점)
- MACD 데드크로스: 하락 신호 (+2점)
- 20일 이평선 이탈: 단기 약세 (+2점)
- 거래량 급감: 유동성 위험 (+1점)
- 52주 최고가 대비 -20%: 조정 구간 (+2점)

기회 점수 (1-10):
- RSI < 30: 과매도 기회 (+3점)
- MACD 골든크로스: 상승 신호 (+2점)
- 20일 이평선 돌파: 단기 강세 (+2점)
- 거래량 급증: 관심 증가 (+2점)
- 52주 최저가 대비 +10%: 반등 신호 (+1점)
```

**시각화**
- 신호등 시스템 (빨강/노랑/초록)
- 이모티콘 활용 (😰 위험 / 😐 보통 / 😊 기회)
- 간단한 텍스트 설명 ("지금은 매수 신중", "반등 가능성 있음")

### 3.4 기본 자동매매 전략 (3-4개)

**전략 1: 안전 우선 전략**
```python
조건:
- RSI < 30 시 분할 매수 (3회)
- RSI > 70 시 분할 매도 (3회)
- 손실 -5% 시 전량 매도
```

**전략 2: 추세 추종 전략**
```python
조건:
- 5일 이평선 > 20일 이평선 돌파 시 매수
- 5일 이평선 < 20일 이평선 하향 돌파 시 매도
- Trailing Stop 3% 적용
```

**전략 3: 변동성 돌파 전략**
```python
조건:
- 당일 시가 > 전일 고가 시 매수
- 당일 종가 기준 익일 시가 매도
- 일일 최대 거래 1회 제한
```

**전략 4: MACD 시그널 전략**
```python
조건:
- MACD 골든크로스 시 매수
- MACD 데드크로스 시 매도
- 최대 보유 기간 20일
```

## 4. 기술 아키텍처

### 4.1 개발 환경 (로컬 → 클라우드)

**Phase 1: 로컬 개발**
```
Local Machine
├── Backend (Python FastAPI)
├── Database (SQLite → PostgreSQL)
├── Redis (로컬 캐싱)
└── Flutter 개발 환경
```

**Phase 2: Supabase 배포**
```
Supabase
├── PostgreSQL (데이터베이스)
├── Edge Functions (API)
├── Realtime (웹소켓)
└── Storage (차트 캐싱)

widelight.studio
└── Flutter Web/Mobile 배포
```

### 4.2 기술 스택

**Backend**
```python
# 핵심 라이브러리
- FastAPI: REST API 서버
- mojito2: 한국투자증권 API 래퍼
- pandas/numpy: 데이터 처리
- ta-lib: 기술적 지표 계산
- apscheduler: 자동매매 스케줄러
- websocket: 실시간 데이터
```

**Frontend (Flutter)**
```dart
dependencies:
  - fl_chart: 차트 라이브러리
  - provider/riverpod: 상태 관리
  - dio: HTTP 클라이언트
  - web_socket_channel: 실시간 통신
  - flutter_local_notifications: 알림
```

**Database Schema (기본)**
```sql
-- 사용자
users (id, email, name, created_at)

-- 증권사 연결
broker_accounts (id, user_id, broker_type, account_no, api_key, secret_key)

-- 보유 종목
holdings (id, account_id, symbol, quantity, avg_price, current_price)

-- 자동매매 설정
auto_trade_settings (id, user_id, symbol, strategy_id, is_active, params)

-- 거래 내역
trade_history (id, account_id, symbol, type, quantity, price, executed_at)

-- 위험도 평가
risk_assessments (id, symbol, risk_score, opportunity_score, indicators, assessed_at)
```

## 5. 확장 가능한 아키텍처 설계

### 5.1 증권사 API 추상화
```python
# 인터페이스 정의로 확장성 확보
class BrokerInterface:
    def get_account_info()
    def get_holdings()
    def place_order()
    def get_market_data()

class KoreaInvestment(BrokerInterface):
    # 한국투자증권 구현

class FutureBroker(BrokerInterface):
    # 향후 다른 증권사 추가 용이
```

### 5.2 전략 플러그인 시스템
```python
# 기본 전략 클래스
class BaseStrategy:
    def analyze(self, data)
    def generate_signal(self)
    def execute(self)

# 커스텀 전략 동적 로딩
class CustomStrategy(BaseStrategy):
    # SI 프로젝트로 추가 가능
```

## 6. UI/UX 설계 원칙 (50대 친화적)

### 6.1 디자인 가이드라인
- **글자 크기**: 최소 16pt, 중요 정보 18pt
- **색상**: 고대비, 색맹 친화적 팔레트
- **버튼**: 최소 48x48dp 터치 영역
- **아이콘**: 직관적 + 텍스트 라벨 병행
- **레이아웃**: 단순, 최대 3depth

### 6.2 핵심 화면 구성
```
1. 메인 대시보드
   - 전체 자산 요약 (크고 명확한 숫자)
   - 오늘의 손익 (색상으로 구분)
   - 위험 종목 TOP 3 (빨간색 경고)
   - 기회 종목 TOP 3 (초록색 하이라이트)

2. 종목 상세
   - 실시간 차트 (확대/축소 쉽게)
   - 위험도 신호등
   - 간단한 매수/매도 버튼
   - 자동매매 ON/OFF 토글

3. 자동매매 설정
   - 전략 선택 (카드 형식)
   - 쉬운 설명과 예시
   - 시뮬레이션 결과 미리보기
```

## 7. 개발 로드맵 (수정)

### Phase 0: 환경 설정 (1주)
- [ ] 개발 환경 구축
- [ ] 한국투자증권 API 키 발급
- [ ] 기본 프로젝트 구조 설정

### Phase 1: MVP Core (4주)
- [ ] Week 1: 한투 API 연동 및 계좌 조회
- [ ] Week 2: 실시간 차트 및 기본 매매
- [ ] Week 3: 기술 지표 계산 및 위험도 평가
- [ ] Week 4: Flutter 기본 UI 구현

### Phase 2: 자동매매 (3주)
- [ ] Week 5: 기본 전략 4개 구현
- [ ] Week 6: 자동매매 엔진 및 스케줄러
- [ ] Week 7: 테스트 및 안정화

### Phase 3: 배포 및 개선 (2주)
- [ ] Week 8: Supabase 마이그레이션
- [ ] Week 9: 실사용자 테스트 및 피드백
- [ ] Week 10: 버그 수정 및 최적화

### Phase 4: 확장 (향후)
- [ ] 백테스팅 기능
- [ ] 추가 증권사 연동
- [ ] 커스텀 전략 빌더
- [ ] 알림 채널 확장 (Telegram, 카톡)

## 8. SI 프로젝트 운영 방안

### 8.1 커스텀 전략 개발 프로세스
```
1. 요구사항 수집 (1-2일)
   - 고객 인터뷰
   - 매매 로직 문서화
   
2. 전략 구현 (3-5일)
   - Python 코드 작성
   - 단위 테스트
   
3. 백테스팅 (2-3일)
   - 과거 데이터 검증
   - 성과 리포트
   
4. 배포 및 모니터링 (1일)
   - 고객 계정 적용
   - 실시간 모니터링 설정

총 소요 기간: 7-11일
예상 단가: 300-500만원/전략
```

## 9. 리스크 관리

| 리스크 | 대응 방안 | 우선순위 |
|--------|-----------|----------|
| API 호출 제한 | 캐싱 전략, 호출 최적화 | 높음 |
| 자동매매 오작동 | 일일 한도 설정, 긴급정지 | 높음 |
| 50대 사용성 | 사용자 테스트, 지속 개선 | 중간 |
| 증권사 API 변경 | 추상화 레이어, 버전 관리 | 중간 |

## 10. TODO List (백로그)

### Near Term
- [ ] 백테스팅 엔진 설계
- [ ] 알림 시스템 (Telegram bot)
- [ ] 웹 대시보드 버전

### Long Term
- [ ] AI 기반 종목 추천
- [ ] 포트폴리오 최적화
- [ ] 세금 최적화 매매
- [ ] 해외 주식 지원

---

## 문서 정보
- 버전: v1.1
- 작성일: 2025-01-26
- 작성자: Asset Management Platform Team
- 다음 리뷰: 2025-02-01