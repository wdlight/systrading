# 실제 계좌 API 테스트 가이드

## 📋 개요
`TestRealAccountBalanceAPI` 등 실제 한국투자증권 API를 사용하는 통합 테스트를 안전하게 실행하는 방법을 설명합니다.

**🚀 NEW**: `KoreaInvestEnv` 클래스를 활용하여 토큰을 자동으로 발급받고 관리합니다!

## ⚠️ 주의사항
- **실제 API 호출**: 실제 한국투자증권 서버에 API 요청을 보냅니다
- **계좌 정보 조회**: 실제 계좌 잔고와 보유 종목 정보를 조회합니다
- **매매는 하지 않음**: 조회만 하며 실제 주문은 실행하지 않습니다
- **API 사용량 제한**: 과도한 호출을 피하세요

## 🔧 설정 준비

### 방법 1: 자동 설정 도우미 (권장)

**1단계: 자동 설정 실행**
```bash
cd backend
python setup_config.py
```

이 도구는:
- 대화형으로 API 키 정보를 입력받습니다
- `KoreaInvestEnv`를 사용하여 토큰을 자동 발급받습니다
- `config.yaml` 파일을 자동으로 생성합니다
- 설정 검증까지 한 번에 처리합니다

**2단계: 설정 확인**
```bash
python run_real_tests.py --check
```

### 방법 2: 수동 설정

**1. 최소 설정으로 config.yaml 생성**
```yaml
# 기본 필수 설정 (KoreaInvestEnv 호환)
KI_API_KEY: "your_api_key"
KI_SECRET_KEY: "your_secret_key"  
KI_ACCOUNT_NUMBER: "your_account_number"
KI_USING_URL: "https://openapi.koreainvestment.com:9443"
KI_IS_PAPER_TRADING: false  # true: 모의투자, false: 실계좌

# 선택사항 (KoreaInvestEnv가 자동 발급)
# KI_API_APPROVAL_KEY: "approval_key"  # 자동 발급됨
# KI_ACCOUNT_ACCESS_TOKEN: "access_token"  # 자동 발급됨
# KI_WEBSOCKET_APPROVAL_KEY: "websocket_key"  # 자동 발급됨

# 모의투자용 (KI_IS_PAPER_TRADING: true인 경우)
# KI_PAPER_API_KEY: "paper_api_key"  # 없으면 KI_API_KEY 사용
# KI_PAPER_SECRET_KEY: "paper_secret_key"  # 없으면 KI_SECRET_KEY 사용
```

### 2. KoreaInvestEnv의 장점

**🔄 자동 토큰 관리**
- Access Token 자동 발급 및 갱신
- WebSocket 승인키 자동 발급
- 토큰 만료 감지 및 재발급

**💾 토큰 캐싱**
- 발급받은 토큰을 파일에 저장
- 재실행시 기존 토큰 재사용
- 만료된 토큰만 선별적으로 재발급

**🔒 안전한 관리**
- 토큰 파일 암호화 저장
- 만료 시간 추적
- 오류 발생시 자동 복구

### 3. 필요한 정보 (간소화됨)

**최소 필수 정보 (3개만!)**
- **KI_API_KEY**: 한국투자증권 API Key
- **KI_SECRET_KEY**: 한국투자증권 Secret Key
- **KI_ACCOUNT_NUMBER**: 계좌번호 (8자리)

**자동 처리되는 것들**
- ✅ API 승인키 (KI_API_APPROVAL_KEY)
- ✅ 계좌 접근 토큰 (KI_ACCOUNT_ACCESS_TOKEN)
- ✅ WebSocket 승인키 (KI_WEBSOCKET_APPROVAL_KEY)
- ✅ 토큰 만료 관리 및 자동 재발급

### 4. 모의투자 vs 실계좌
- `KI_IS_PAPER_TRADING: true` → 모의투자 계좌 사용 (안전)
- `KI_IS_PAPER_TRADING: false` → 실계좌 사용 (주의 필요)

## 🚀 실행 방법

### 방법 1: 편리한 스크립트 사용 (권장)

```bash
cd backend

# 설정 확인만
python run_real_tests.py --check

# 모든 실제 API 테스트 실행
python run_real_tests.py

# 특정 테스트 클래스만 실행
python run_real_tests.py --class TestRealAccountBalanceAPI
```

### 방법 2: 직접 pytest 명령 사용

```bash
cd backend

# 모든 실제 API 테스트
python -m pytest tests/test_real_account_integration.py -m integration -v -s

# 계좌 잔고 테스트만
python -m pytest tests/test_real_account_integration.py::TestRealAccountBalanceAPI -v -s

# 워치리스트 테스트만
python -m pytest tests/test_real_account_integration.py::TestRealWatchlistAPI -v -s
```

## 📊 테스트 클래스별 설명

### 1. TestRealAccountBalanceAPI
**실제 계좌 잔고 조회 테스트**

- `test_real_account_balance_basic`: 기본 계좌 정보 조회
- `test_real_positions_structure`: 보유 종목 데이터 구조 검증
- `test_real_profit_loss_calculation`: 손익 계산 정확성 검증

**출력 예시:**
```
[실제 계좌 정보]
총 자산: 10,000,000원
총 평가금액: 8,500,000원  
총 손익: 500,000원
수익률: 6.25%
사용 가능 현금: 1,500,000원
보유 종목 수: 3개

[첫 번째 보유 종목]
종목코드: 005930
종목명: 삼성전자
보유수량: 10주
평균단가: 75,000원
현재가: 78,000원
손익: 30,000원
수익률: 4.0%
```

### 2. TestRealWatchlistAPI
**실제 워치리스트 조회 테스트**

- `test_real_watchlist_basic`: 기본 워치리스트 조회
- `test_real_watchlist_data_structure`: 데이터 구조 및 기술적 지표 검증

**출력 예시:**
```
[워치리스트 종목 수]: 2개
  005930 삼성전자: 78,000원
  000660 SK하이닉스: 130,000원

[005930] 삼성전자
  현재가: 78,000원
  MACD: 120.5
  RSI: 45.2
  거래량: 1,500,000
```

### 3. TestRealTradingConditionsAPI
**매매 조건 API 테스트**

- `test_real_trading_conditions_get_and_update`: 조회 및 업데이트 테스트

**기능:**
- 현재 매매 조건 조회
- 설정 변경 테스트
- 원래 설정으로 복원

### 4. TestRealMarketOverviewAPI
**실제 시장 개요 테스트**

- `test_real_market_overview`: 시장 지수 및 상승/하락 종목 조회

**출력 예시:**
```
[시장 개요]
시장 상태: open
KOSPI: 2,580.45 (+15.23, +0.59%)
KOSDAQ: 850.23 (-5.67, -0.66%)
USD/KRW: 1,340.50

[상승 종목 (2개)]
  005930 삼성전자: +2.04%
  000660 SK하이닉스: +1.85%
```

## 🛡️ 안전 기능

### 1. 설정 검증
- 필수 API 키 누락 확인
- config.yaml 파일 존재 확인
- 잘못된 설정 값 감지

### 2. 실계좌 모드 경고
```
⚠️  실계좌 모드에서 테스트를 실행하려고 합니다.
   실제 API 호출이 발생하지만, 매매 테스트는 포함되지 않습니다.
   계속하시겠습니까? (y/N):
```

### 3. 자동 스킵 기능
- config.yaml 없으면 자동으로 테스트 스킵
- API 키 누락시 자동으로 테스트 스킵
- 오류 발생시 명확한 안내 메시지

## 🔍 트러블슈팅

### 문제 1: "config.yaml 파일이 없습니다"
**해결:** `backend/config.yaml` 파일을 위의 형식으로 생성

### 문제 2: "필수 설정이 누락되었습니다"
**해결:** config.yaml에 모든 필수 키를 올바르게 입력

### 문제 3: "API 호출 실패"
**해결책:**
1. API 키가 올바른지 확인
2. 계좌번호가 정확한지 확인  
3. 접근 토큰이 유효한지 확인
4. 네트워크 연결 상태 확인

### 문제 4: "권한 오류"
**해결:** API 승인키가 올바르고 해당 기능에 대한 권한이 있는지 확인

## 📈 테스트 결과 해석

### 성공 예시
```
tests/test_real_account_integration.py::TestRealAccountBalanceAPI::test_real_account_balance_basic PASSED [100%]
✅ 모든 실제 API 테스트가 성공했습니다!
```

### 실패 예시
```
tests/test_real_account_integration.py::TestRealAccountBalanceAPI::test_real_account_balance_basic FAILED [100%]
❌ 일부 실제 API 테스트가 실패했습니다.
```

## 💡 사용 팁

### 1. 점진적 테스트
```bash
# 1단계: 설정 확인
python run_real_tests.py --check

# 2단계: 계좌 잔고만 테스트 
python run_real_tests.py --class TestRealAccountBalanceAPI

# 3단계: 모든 테스트
python run_real_tests.py
```

### 2. 모의투자로 먼저 테스트
실계좌 테스트 전에 `KI_IS_PAPER_TRADING: true`로 설정하여 모의투자 환경에서 먼저 테스트해보세요.

### 3. API 사용량 제한 고려
한국투자증권 API는 사용량 제한이 있으므로 과도한 반복 테스트는 피하세요.

## 🔒 보안 주의사항

1. **config.yaml 파일 보안**
   - Git에 커밋하지 마세요 (.gitignore에 추가)
   - 파일 권한을 적절히 설정하세요

2. **API 키 관리**
   - API 키를 코드에 직접 하드코딩하지 마세요
   - 주기적으로 API 키를 재발급하세요

3. **테스트 환경 분리**
   - 개발/테스트 환경과 운영 환경을 분리하세요
   - 가능하면 모의투자 계좌를 사용하세요

---

## 📞 문의사항

테스트 관련 문의사항이 있으시면:
1. 테스트 로그를 확인하세요
2. config.yaml 설정을 다시 확인하세요  
3. 한국투자증권 API 문서를 참조하세요