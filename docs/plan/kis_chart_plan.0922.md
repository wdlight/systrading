# 한국투자증권 API 캔들차트 구현 계획서

## 📋 프로젝트 개요

**목적**: 한국투자증권 OpenAPI를 활용한 국내주식 캔들차트 시스템 구축  
**기간**: 2-3주 예상  
**기술 스택**: Python, Plotly/Matplotlib, pandas, requests  

---

## 🔧 1단계: 환경 설정 및 기본 구조

### 1.1 필수 환경 변수 설정

```bash
# .env 파일 생성
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACCESS_TOKEN=your_access_token_here
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
```

### 1.2 필요한 Python 패키지

```bash
pip install requests pandas plotly matplotlib python-dotenv
```

### 1.3 프로젝트 구조

```
kis_chart/
├── config/
│   ├── __init__.py
│   └── settings.py          # API 설정
├── api/
│   ├── __init__.py
│   ├── kis_client.py        # API 클라이언트
│   └── data_models.py       # 데이터 모델
├── chart/
│   ├── __init__.py
│   ├── candlestick.py       # 캔들차트 생성
│   └── indicators.py       # 기술지표
├── utils/
│   ├── __init__.py
│   └── helpers.py          # 유틸리티 함수
├── main.py                 # 메인 실행 파일
├── requirements.txt
└── README.md
```

---

## 🚀 2단계: API 클라이언트 구현

### 2.1 핵심 API 정보

**주요 API: 국내주식기간별시세(일_주_월_년)**
- **TR ID**: `FHKST03010100`
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`
- **Method**: GET
- **최대 조회**: 100건

### 2.2 API 클라이언트 구현 계획

```python
# api/kis_client.py 구현 예시
class KISClient:
    def __init__(self):
        self.base_url = os.getenv('KIS_BASE_URL')
        self.app_key = os.getenv('KIS_APP_KEY')
        self.app_secret = os.getenv('KIS_APP_SECRET')
        self.access_token = os.getenv('KIS_ACCESS_TOKEN')
    
    def get_candle_data(self, stock_code, start_date, end_date, period='D'):
        """캔들 데이터 조회"""
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {self.access_token}',
            'appkey': self.app_key,
            'appsecret': self.app_secret,
            'tr_id': 'FHKST03010100'
        }
        
        params = {
            'fid_cond_mrkt_div_code': 'J',      # 주식시장
            'fid_input_iscd': stock_code,        # 종목코드
            'fid_input_date_1': start_date,      # 시작일
            'fid_input_date_2': end_date,        # 종료일
            'fid_period_div_code': period,       # D=일, W=주, M=월, Y=년
            'fid_org_adj_prc': '0'              # 수정주가 미반영
        }
        
        # API 호출 로직 구현
```

### 2.3 요청/응답 데이터 구조

**요청 파라미터**:
- `fid_cond_mrkt_div_code`: "J" (주식시장)
- `fid_input_iscd`: 종목코드 (예: "005930")
- `fid_input_date_1`: 시작일자 (YYYYMMDD)
- `fid_input_date_2`: 종료일자 (YYYYMMDD)
- `fid_period_div_code`: 기간구분 (D/W/M/Y)
- `fid_org_adj_prc`: 수정주가 반영여부 ("0"/"1")

**응답 데이터 (OHLCV)**:
- `stck_bsop_date`: 영업일자 (날짜)
- `stck_oprc`: 시가 (Open)
- `stck_hgpr`: 고가 (High)
- `stck_lwpr`: 저가 (Low)
- `stck_clpr`: 종가 (Close)
- `acml_vol`: 누적거래량 (Volume)

---

## 📊 3단계: 데이터 처리 및 모델링

### 3.1 데이터 모델 정의

```python
# api/data_models.py
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class CandleData:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
@dataclass
class StockInfo:
    code: str
    name: str
    market: str
```

### 3.2 데이터 변환 로직

```python
def convert_api_response_to_candle_data(response_data) -> List[CandleData]:
    """API 응답을 CandleData 리스트로 변환"""
    candles = []
    for item in response_data['output2']:
        candle = CandleData(
            date=datetime.strptime(item['stck_bsop_date'], '%Y%m%d'),
            open=float(item['stck_oprc']),
            high=float(item['stck_hgpr']),
            low=float(item['stck_lwpr']),
            close=float(item['stck_clpr']),
            volume=int(item['acml_vol'])
        )
        candles.append(candle)
    return candles
```

---

## 🎨 4단계: 캔들스틱 차트 구현

### 4.1 차트 라이브러리 선택: Plotly

**장점**:
- 인터랙티브 차트 지원
- 웹 브라우저에서 바로 표시
- 확대/축소, 팬, 호버 정보 제공
- 거래량 서브차트 쉽게 구현

### 4.2 캔들스틱 차트 구현

```python
# chart/candlestick.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class CandlestickChart:
    def __init__(self, title="Stock Chart"):
        self.title = title
    
    def create_chart(self, candle_data: List[CandleData], stock_name: str):
        """캔들스틱 + 거래량 차트 생성"""
        # 서브플롯 생성 (캔들차트 + 거래량)
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=[f'{stock_name} 주가', '거래량'],
            row_heights=[0.7, 0.3]
        )
        
        # 캔들스틱 차트
        fig.add_trace(
            go.Candlestick(
                x=[d.date for d in candle_data],
                open=[d.open for d in candle_data],
                high=[d.high for d in candle_data],
                low=[d.low for d in candle_data],
                close=[d.close for d in candle_data],
                name="OHLC"
            ),
            row=1, col=1
        )
        
        # 거래량 차트
        fig.add_trace(
            go.Bar(
                x=[d.date for d in candle_data],
                y=[d.volume for d in candle_data],
                name="Volume",
                marker_color='rgba(158, 185, 243, 0.8)'
            ),
            row=2, col=1
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=self.title,
            yaxis_title="Price (KRW)",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            height=800
        )
        
        return fig
```

### 4.3 기술지표 추가 계획

```python
# chart/indicators.py
def add_moving_averages(fig, candle_data, periods=[5, 20, 60]):
    """이동평균선 추가"""
    for period in periods:
        ma_values = calculate_moving_average(candle_data, period)
        fig.add_trace(
            go.Scatter(
                x=[d.date for d in candle_data],
                y=ma_values,
                name=f'MA{period}',
                line=dict(width=2)
            )
        )

def calculate_moving_average(candle_data, period):
    """단순이동평균 계산"""
    # 구현 예정
    pass
```

---

## ⚡ 5단계: 실시간 데이터 (선택사항)

### 5.1 당일 분봉 API

**보조 API: 주식당일분봉조회**
- **TR ID**: `FHKST03010200`
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice`
- **용도**: 당일 실시간 분봉 데이터 (최대 30건)

### 5.2 실시간 업데이트 로직

```python
def get_intraday_data(self, stock_code, time_interval='1'):
    """당일 분봉 데이터 조회"""
    headers = self._get_headers('FHKST03010200')
    params = {
        'fid_cond_mrkt_div_code': 'J',
        'fid_input_iscd': stock_code,
        'fid_input_hour_1': '083000',  # 시작시간
        'fid_etc_cls_code': ''
    }
    # 구현 예정
```

---

## 🎯 6단계: 메인 애플리케이션

### 6.1 사용자 인터페이스

```python
# main.py
def main():
    print("=== 한국투자증권 캔들차트 시스템 ===")
    
    # 1. 종목코드 입력
    stock_code = input("종목코드를 입력하세요 (예: 005930): ")
    
    # 2. 기간 선택
    period = input("조회기간을 선택하세요 (D/W/M/Y): ").upper()
    start_date = input("시작일을 입력하세요 (YYYYMMDD): ")
    end_date = input("종료일을 입력하세요 (YYYYMMDD): ")
    
    # 3. 데이터 조회 및 차트 생성
    client = KISClient()
    chart = CandlestickChart()
    
    try:
        # API 호출
        candle_data = client.get_candle_data(stock_code, start_date, end_date, period)
        
        # 차트 생성
        fig = chart.create_chart(candle_data, f"종목코드: {stock_code}")
        
        # 브라우저에서 차트 표시
        fig.show()
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
```

### 6.2 고급 기능 계획

1. **종목 검색**: 종목명으로 코드 찾기
2. **즐겨찾기**: 자주 보는 종목 저장
3. **알림 기능**: 가격 알림 설정
4. **포트폴리오**: 여러 종목 동시 모니터링
5. **백테스팅**: 투자 전략 테스트

---

## ⚠️ 7단계: 에러 처리 및 최적화

### 7.1 에러 처리 전략

```python
class KISAPIError(Exception):
    """KIS API 관련 에러"""
    pass

class TokenExpiredError(KISAPIError):
    """토큰 만료 에러"""
    pass

class RateLimitError(KISAPIError):
    """API 호출 한도 초과 에러"""
    pass

def handle_api_errors(func):
    """API 에러 처리 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise TokenExpiredError("Access token이 만료되었습니다.")
            elif e.response.status_code == 429:
                raise RateLimitError("API 호출 한도를 초과했습니다.")
            else:
                raise KISAPIError(f"API 에러: {e}")
        except Exception as e:
            raise KISAPIError(f"알 수 없는 에러: {e}")
    return wrapper
```

### 7.2 성능 최적화

1. **데이터 캐싱**: 중복 API 호출 방지
2. **배치 처리**: 여러 종목 동시 조회
3. **비동기 처리**: aiohttp 활용
4. **데이터 압축**: 메모리 사용량 최적화

---

## 📚 8단계: 테스팅 및 문서화

### 8.1 테스트 계획

```python
# tests/test_kis_client.py
import unittest
from unittest.mock import patch, Mock

class TestKISClient(unittest.TestCase):
    def setUp(self):
        self.client = KISClient()
    
    @patch('requests.get')
    def test_get_candle_data_success(self, mock_get):
        # 성공 케이스 테스트
        mock_response = Mock()
        mock_response.json.return_value = {
            'rt_cd': '0',
            'output2': [
                {
                    'stck_bsop_date': '20240101',
                    'stck_oprc': '75000',
                    'stck_hgpr': '76000',
                    'stck_lwpr': '74500',
                    'stck_clpr': '75500',
                    'acml_vol': '1000000'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = self.client.get_candle_data('005930', '20240101', '20240131')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
```

### 8.2 문서화 계획

1. **API 문서**: Sphinx 또는 mkdocs 사용
2. **사용자 가이드**: 설치부터 사용법까지
3. **개발자 가이드**: 코드 구조 및 확장 방법
4. **FAQ**: 자주 묻는 질문과 해결책

---

## 🚀 9단계: 배포 및 운영

### 9.1 배포 옵션

1. **로컬 실행**: Python 스크립트로 실행
2. **웹 애플리케이션**: Streamlit 또는 Flask 사용
3. **데스크톱 앱**: PyQt 또는 tkinter 사용
4. **클라우드**: AWS, GCP, Heroku 배포

### 9.2 모니터링 및 로깅

```python
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kis_chart.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

---

## 📝 10단계: 향후 개선 계획

### 10.1 단기 목표 (1개월)
- [x] 기본 캔들차트 구현
- [ ] 이동평균선 추가
- [ ] 거래량 차트 완성
- [ ] 에러 처리 강화

### 10.2 중기 목표 (3개월)
- [ ] 실시간 데이터 연동
- [ ] 다양한 기술지표 추가
- [ ] 웹 인터페이스 구현
- [ ] 포트폴리오 기능

### 10.3 장기 목표 (6개월)
- [ ] 머신러닝 예측 모델
- [ ] 자동매매 시스템 연동
- [ ] 모바일 앱 개발
- [ ] 커뮤니티 기능

---

## 📋 체크리스트

### 환경 설정
- [ ] Python 3.8+ 설치 확인
- [ ] 필수 패키지 설치
- [ ] KIS API 키 발급 및 설정
- [ ] 프로젝트 구조 생성

### 개발 진행
- [ ] API 클라이언트 구현
- [ ] 데이터 모델 정의
- [ ] 캔들차트 기본 구현
- [ ] 테스트 코드 작성

### 배포 준비
- [ ] 문서화 완료
- [ ] 에러 처리 구현
- [ ] 성능 최적화
- [ ] 사용자 테스트

---

## 🔗 참고 자료

1. **한국투자증권 OpenAPI 문서**: [공식 문서](https://apiportal.koreainvestment.com/)
2. **Plotly 문서**: [Plotly Python](https://plotly.com/python/)
3. **pandas 문서**: [pandas 가이드](https://pandas.pydata.org/)
4. **Python 모범 사례**: PEP 8, 타입 힌팅

---

**마지막 업데이트**: 2025년 1월 27일  
**문서 버전**: 1.0  
**작성자**: Claude Assistant