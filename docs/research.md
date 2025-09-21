# 주식 자동매매 시스템 구조 분석 완료

## 📊 현재 프로젝트 구조

### 🔧 **레거시 구조** (기존 파일들)
- `rsimacd_trading.py` (26,909 lines): 메인 트레이딩 로직, PyQt5 GUI 포함
- `utils.py` (49,289 lines): KoreaInvestAPI, TokenManager 등 핵심 유틸리티
- `kismain.ui`: PyQt5 UI 정의 파일

### 🏗️ **새로운 모듈화 구조** (진행 중)
```
📁 brokers/          # 증권사 API 추상화
├── factory.py       # 브로커 팩토리 패턴
├── korea_investment/ # 한국투자증권 API
└── ls_securities/   # LS증권 API (TODO)

📁 core/             # 핵심 비즈니스 로직
├── interfaces/      # 추상 인터페이스 정의
├── trading_engine.py # RSI/MACD 트레이딩 엔진
└── order_processor.py # 주문 처리 로직

📁 services/         # 비즈니스 서비스 계층
├── account_service.py
└── trading_service.py

📁 ui/               # 사용자 인터페이스
├── qt/             # PyQt5 UI
├── web/            # 웹 UI
└── mobile/         # 모바일 UI

📁 stock-trading-ui/ # Next.js 웹 인터페이스
```

### 🚨 **핵심 문제 (CLAUDE.md 기반)**
- **수익률 0.0% 표시 이슈**: 매수 시 평균단가가 None으로 초기화되어 수익률 계산 불가
- **타이밍 문제**: 계좌조회(2초 주기) vs 실시간 가격 업데이트
- **데이터 플로우**: 매수 주문 → 체결 완료 → 계좌조회 → 평균단가 업데이트

### ⚡ **기술 스택**
- **Backend**: Python, PyQt5, pandas, talib, loguru
- **API**: 한국투자증권 OpenAPI
- **Frontend**: Next.js, TypeScript, shadcn/ui
- **Data**: pandas DataFrame 기반 실시간 데이터 관리

### 🔄 **데이터 흐름**
1. **실시간 가격 수신** → WebSocket 연결
2. **RSI/MACD 계산** → talib 라이브러리
3. **매수/매도 시그널** → 조건 검증 후 주문 실행
4. **계좌 업데이트** → 2초 주기 API 호출
5. **UI 업데이트** → PyQt5 테이블 모델

## 🎯 개선 방향
1. **즉시 수정**: `rsimacd_trading.py:475` - 평균단가 초기값을 현재가로 설정
2. **구조 개선**: 레거시 코드를 새로운 모듈 구조로 점진적 마이그레이션
3. **UI 통합**: PyQt5와 Next.js 웹 UI 연동
4. **테스트 추가**: 핵심 로직에 대한 단위 테스트 구현

## 📋 상세 분석

### 파일 구조 상세
```
D:\stocktrading\0908.claude-init\
├── 📄 rsimacd_trading.py       # 메인 트레이딩 애플리케이션
├── 📄 utils.py                 # API 및 유틸리티 함수
├── 📄 main.py                  # 새로운 진입점 (모듈화된 구조)
├── 📄 config.yaml              # 설정 파일 (API 키, URL 등)
├── 📄 kismain.ui               # PyQt5 UI 정의
├── 📁 brokers/                 # 증권사 API 추상화
│   ├── 📄 factory.py           # 브로커 팩토리
│   ├── 📁 korea_investment/    # 한국투자증권 구현
│   └── 📁 ls_securities/       # LS증권 구현 (TODO)
├── 📁 core/                    # 핵심 비즈니스 로직
│   ├── 📁 interfaces/          # 추상 인터페이스
│   ├── 📄 trading_engine.py    # RSI/MACD 전략 엔진
│   └── 📄 order_processor.py   # 주문 처리
├── 📁 services/                # 서비스 계층
├── 📁 ui/                      # UI 계층
│   ├── 📁 qt/                  # PyQt5 구현
│   ├── 📁 web/                 # 웹 UI
│   └── 📁 mobile/              # 모바일 UI
├── 📁 stock-trading-ui/        # Next.js 웹 앱
├── 📁 data/                    # 데이터 파일
├── 📁 docs/                    # 문서
├── 📁 tests/                   # 테스트 파일
└── 📁 legacy/                  # 레거시 파일들
```

### 아키텍처 패턴
- **팩토리 패턴**: `brokers/factory.py`로 다양한 증권사 API 지원
- **인터페이스 분리**: `core/interfaces/`로 추상화 계층 구현
- **서비스 계층**: `services/`로 비즈니스 로직 분리
- **멀티 UI 지원**: PyQt5, Web, Mobile UI 동시 지원

### 데이터 관리
- **실시간 데이터**: `realtime_watchlist_df` pandas DataFrame
- **계좌 정보**: `account_info_df` pandas DataFrame  
- **타이머 기반 업데이트**: 
  - `timer1`: 10초마다 설정 저장
  - `timer2`: 2초마다 계좌조회
  - `timer3`: 0.05초마다 TR 결과 처리
  - `timer4`: 2초마다 등락률 상위 조회

### 프로세스 아키텍처
- **메인 프로세스**: PyQt5 GUI 및 실시간 데이터 처리
- **주문 처리 프로세스**: `send_tr_process()` - 별도 프로세스에서 주문 실행
- **프로세스 간 통신**: `Queue` 기반 메시지 전달

### 보안 고려사항
- API 키 및 토큰이 `config.yaml`에 평문 저장
- 토큰 만료 시 자동 갱신 로직 포함
- 백업 토큰 관리 (`token_backup/` 디렉토리)

### 성능 특성
- 실시간 데이터 처리: WebSocket 기반
- 지표 계산: talib 라이브러리 사용
- UI 업데이트: PyQt5 모델/뷰 패턴
- 메모리 사용: pandas DataFrame 기반 인메모리 처리