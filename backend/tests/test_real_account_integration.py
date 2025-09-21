"""
실제 계좌 API를 사용한 통합 테스트
실제 access token과 approval key가 필요합니다.
"""

import pytest
import os
import yaml
import pandas as pd
from unittest.mock import patch
from fastapi.testclient import TestClient

# 테스트 대상 모듈 import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simple_server import app


@pytest.mark.integration
class TestRealAccountBalanceAPI:
    """실제 계좌 API를 사용한 계좌 잔고 테스트"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    @pytest.fixture(scope="class") 
    def ki_env_setup(self):
        """KoreaInvestEnv를 사용한 초기 설정"""
        try:
            # config.yaml 파일 확인
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
            if not os.path.exists(config_path):
                pytest.skip("config.yaml 파일이 없습니다. 실제 API 테스트를 건너뜁니다.")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # KoreaInvestEnv에 맞는 설정 변환
            ki_config = {
                'api_key': config.get('KI_API_KEY'),
                'api_secret_key': config.get('KI_SECRET_KEY'), 
                'stock_account_number': config.get('KI_ACCOUNT_NUMBER'),
                'url': config.get('KI_USING_URL', 'https://openapi.koreainvestment.com:9443'),
                'paper_url': 'https://openapivts.koreainvestment.com:29443',
                'is_paper_trading': config.get('KI_IS_PAPER_TRADING', False),
                'custtype': 'P',
                'my_agent': config.get('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            }
            
            # 모의투자 설정이 있는 경우 추가
            if ki_config['is_paper_trading']:
                ki_config['paper_api_key'] = config.get('KI_PAPER_API_KEY', ki_config['api_key'])
                ki_config['paper_api_secret_key'] = config.get('KI_PAPER_SECRET_KEY', ki_config['api_secret_key'])
            
            # 필수 설정 확인
            required_keys = ['api_key', 'api_secret_key', 'stock_account_number']
            missing_keys = [key for key in required_keys if not ki_config.get(key)]
            
            if missing_keys:
                pytest.skip(f"필수 설정이 누락되었습니다: {missing_keys}")
            
            # KoreaInvestEnv 초기화 및 토큰 자동 발급
            try:
                sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
                from brokers.korea_investment.ki_env import KoreaInvestEnv
                
                print(f"\n🔧 KoreaInvestEnv 초기화 시작...")
                print(f"📊 계좌번호: {ki_config['stock_account_number']}")
                print(f"🔑 API Key: {ki_config['api_key'][:10]}...")
                print(f"🌐 URL: {ki_config.get('url' if not ki_config['is_paper_trading'] else 'paper_url')}")
                print(f"📝 모의투자: {ki_config['is_paper_trading']}")
                
                ki_env = KoreaInvestEnv(ki_config)
                
                # 설정된 토큰들 확인
                full_config = ki_env.get_full_config()
                base_headers = ki_env.get_base_headers()
                
                print(f"✅ 토큰 발급 완료")
                print(f"🔐 Access Token: {'Present' if base_headers.get('authorization') else 'Missing'}")
                print(f"🔌 WebSocket Key: {'Present' if full_config.get('websocket_approval_key') else 'Missing'}")
                
                return ki_env, ki_config
                
            except ImportError as e:
                pytest.skip(f"KoreaInvestEnv 모듈을 찾을 수 없습니다: {e}")
            except Exception as e:
                pytest.skip(f"KoreaInvestEnv 초기화 실패: {e}")
            
        except Exception as e:
            pytest.skip(f"설정 파일 읽기 오류: {e}")
    
    @pytest.fixture(scope="class")
    def real_api_available(self, ki_env_setup):
        """실제 API 사용 가능 여부 확인 (KoreaInvestEnv 기반)"""
        ki_env, ki_config = ki_env_setup
        
        # 토큰이 정상적으로 발급되었는지 확인
        base_headers = ki_env.get_base_headers()
        full_config = ki_env.get_full_config()
        
        if not base_headers.get('authorization'):
            pytest.skip("Access Token이 발급되지 않았습니다.")
        
        if not full_config.get('websocket_approval_key'):
            print("⚠️  WebSocket 승인키가 없지만 계좌 조회는 가능합니다.")
        
        return True
    
    def test_real_account_balance_basic(self, client, real_api_available):
        """실제 API를 사용한 기본 계좌 잔고 조회 테스트"""
        import json
        
        print(f"\n{'='*60}")
        print(f"🔍 [REQUEST] GET /api/account/balance")
        print(f"{'='*60}")
        
        # 실제 API 호출
        response = client.get("/api/account/balance")
        
        print(f"\n📤 [REQUEST INFO]")
        print(f"- URL: /api/account/balance")
        print(f"- Method: GET")
        print(f"- Headers: {dict(response.request.headers) if hasattr(response.request, 'headers') else 'N/A'}")
        
        print(f"\n📥 [RESPONSE INFO]")
        print(f"- Status Code: {response.status_code}")
        print(f"- Headers: {dict(response.headers)}")
        print(f"- Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\n📋 [RESPONSE BODY - FULL JSON]")
        print(f"Raw JSON Response:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        print(f"\n🔬 [RESPONSE DATA ANALYSIS]")
        print(f"Response Keys: {list(data.keys())}")
        
        # 기본 구조 검증
        assert "total_value" in data
        assert "total_evaluation_amount" in data
        assert "total_profit_loss" in data
        assert "total_profit_loss_rate" in data
        assert "available_cash" in data
        assert "positions" in data
        
        # 데이터 타입 검증
        assert isinstance(data["total_value"], (int, float))
        assert isinstance(data["total_evaluation_amount"], (int, float))
        assert isinstance(data["total_profit_loss"], (int, float))
        assert isinstance(data["total_profit_loss_rate"], (int, float))
        assert isinstance(data["available_cash"], (int, float))
        assert isinstance(data["positions"], list)
        
        print(f"\n📊 [계좌 정보 요약]")
        print(f"총 자산: {data['total_value']:,}원")
        print(f"총 평가금액: {data['total_evaluation_amount']:,}원")
        print(f"총 손익: {data['total_profit_loss']:,}원")
        print(f"수익률: {data['total_profit_loss_rate']}%")
        print(f"사용 가능 현금: {data['available_cash']:,}원")
        print(f"보유 종목 수: {len(data['positions'])}개")
        
        print(f"\n📈 [보유 종목 상세 정보]")
        if len(data['positions']) > 0:
            for i, position in enumerate(data['positions']):
                print(f"[{i+1}] {position}")
        else:
            print("보유 종목 없음")
            
        print(f"\n{'='*60}")
        print(f"✅ TEST COMPLETED")
        print(f"{'='*60}")
    
    def test_real_positions_structure(self, client, real_api_available):
        """실제 보유 종목 데이터 구조 테스트"""
        import json
        
        print(f"\n{'='*60}")
        print(f"🔍 [REQUEST] GET /api/account/balance - Positions Structure Test")
        print(f"{'='*60}")
        
        response = client.get("/api/account/balance")
        
        print(f"\n📤 [REQUEST INFO]")
        print(f"- URL: /api/account/balance")
        print(f"- Method: GET")
        
        print(f"\n📥 [RESPONSE INFO]")
        print(f"- Status Code: {response.status_code}")
        print(f"- Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        assert response.status_code == 200
        
        data = response.json()
        positions = data["positions"]
        
        print(f"\n📋 [POSITIONS DATA - FULL JSON]")
        print(f"Total Positions Count: {len(positions)}")
        print(json.dumps(positions, ensure_ascii=False, indent=2))
        
        if len(positions) > 0:
            # 첫 번째 포지션 구조 검증
            first_position = positions[0]
            
            print(f"\n🔬 [FIRST POSITION STRUCTURE ANALYSIS]")
            print(f"Available Fields: {list(first_position.keys())}")
            
            required_fields = [
                "stock_code", "stock_name", "quantity", "avg_price",
                "current_price", "yesterday_price", "profit_loss",
                "profit_loss_rate", "evaluation_amount"
            ]
            
            print(f"Required Fields: {required_fields}")
            missing_fields = [field for field in required_fields if field not in first_position]
            print(f"Missing Fields: {missing_fields if missing_fields else 'None'}")
            
            for field in required_fields:
                assert field in first_position, f"필수 필드 '{field}'가 누락되었습니다"
            
            # 데이터 타입 및 값 검증
            assert isinstance(first_position["stock_code"], str)
            assert len(first_position["stock_code"]) == 6  # 종목코드는 6자리
            assert isinstance(first_position["stock_name"], str)
            assert len(first_position["stock_name"]) > 0
            assert isinstance(first_position["quantity"], int)
            assert first_position["quantity"] > 0
            assert isinstance(first_position["avg_price"], (int, float))
            assert first_position["avg_price"] > 0
            assert isinstance(first_position["current_price"], (int, float))
            assert first_position["current_price"] > 0
            
            print(f"\n📊 [첫 번째 보유 종목 상세]")
            print(f"종목코드: {first_position['stock_code']}")
            print(f"종목명: {first_position['stock_name']}")
            print(f"보유수량: {first_position['quantity']}주")
            print(f"평균단가: {first_position['avg_price']:,}원")
            print(f"현재가: {first_position['current_price']:,}원")
            print(f"손익: {first_position['profit_loss']:,}원")
            print(f"수익률: {first_position['profit_loss_rate']}%")
            
            print(f"\n🔍 [DATA TYPES VALIDATION]")
            for field, value in first_position.items():
                print(f"- {field}: {type(value).__name__} = {value}")
        else:
            print("\n[보유 종목 없음]")
            
        print(f"\n{'='*60}")
        print(f"✅ POSITIONS STRUCTURE TEST COMPLETED")
        print(f"{'='*60}")
    
    def test_real_profit_loss_calculation(self, client, real_api_available):
        """실제 손익 계산 정확성 테스트"""
        import json
        
        print(f"\n{'='*60}")
        print(f"🔍 [REQUEST] GET /api/account/balance - Profit/Loss Calculation Test")
        print(f"{'='*60}")
        
        response = client.get("/api/account/balance")
        
        print(f"\n📤 [REQUEST INFO]")
        print(f"- URL: /api/account/balance")
        print(f"- Method: GET")
        
        print(f"\n📥 [RESPONSE INFO]")
        print(f"- Status Code: {response.status_code}")
        print(f"- Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        assert response.status_code == 200
        
        data = response.json()
        positions = data["positions"]
        
        print(f"\n📋 [FULL RESPONSE DATA FOR CALCULATION]")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        if len(positions) > 0:
            # 각 종목의 손익 계산 검증
            total_calculated_profit_loss = 0
            
            print(f"\n🧮 [PROFIT/LOSS CALCULATION ANALYSIS]")
            print(f"Total Positions for Calculation: {len(positions)}")
            
            for i, position in enumerate(positions):
                stock_code = position["stock_code"]
                quantity = position["quantity"]
                avg_price = position["avg_price"]
                current_price = position["current_price"]
                profit_loss = position["profit_loss"]
                
                # 손익 계산 공식: (현재가 - 평균단가) * 보유수량
                expected_profit_loss = (current_price - avg_price) * quantity
                
                print(f"\n[{i+1}] {stock_code} - {position['stock_name']}")
                print(f"  📊 Position Data: {json.dumps(position, ensure_ascii=False, indent=4)}")
                print(f"  🧮 Calculation:")
                print(f"    - Formula: (현재가 - 평균단가) × 보유수량")
                print(f"    - ({current_price:,} - {avg_price:,}) × {quantity:,}")
                print(f"    - = {current_price - avg_price:,} × {quantity:,}")
                print(f"    - = {expected_profit_loss:,}원")
                print(f"  ✅ API Response: {profit_loss:,}원")
                print(f"  📏 Difference: {abs(profit_loss - expected_profit_loss)}원")
                
                # 허용 오차 (1원 이내)
                assert abs(profit_loss - expected_profit_loss) <= 1, \
                    f"종목 {stock_code} 손익 계산 오류: 예상 {expected_profit_loss}, 실제 {profit_loss}"
                
                total_calculated_profit_loss += profit_loss
            
            # 전체 손익 검증 (허용 오차 10원 이내)
            total_profit_loss = data["total_profit_loss"]
            
            print(f"\n💰 [전체 손익 검증]")
            print(f"  🧮 계산된 총 손익: {total_calculated_profit_loss:,}원")
            print(f"  ✅ API 총 손익: {total_profit_loss:,}원")
            print(f"  📏 차이: {abs(total_profit_loss - total_calculated_profit_loss)}원")
            print(f"  ✔️ 허용 오차: 10원 이내")
            
            assert abs(total_profit_loss - total_calculated_profit_loss) <= 10, \
                f"전체 손익 계산 오류: 예상 {total_calculated_profit_loss}, 실제 {total_profit_loss}"
        else:
            print(f"\n📋 [보유 종목 없음 - 손익 계산 불가]")
            
        print(f"\n{'='*60}")
        print(f"✅ PROFIT/LOSS CALCULATION TEST COMPLETED")
        print(f"{'='*60}")


@pytest.mark.integration
class TestRealWatchlistAPI:
    """실제 API를 사용한 워치리스트 테스트"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def real_api_available(self):
        """실제 API 사용 가능 여부 확인 (계좌 테스트와 동일)"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
            if not os.path.exists(config_path):
                pytest.skip("config.yaml 파일이 없습니다.")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            required_keys = ['KI_API_KEY', 'KI_SECRET_KEY', 'KI_ACCOUNT_NUMBER']
            missing_keys = [key for key in required_keys if not config.get(key)]
            
            if missing_keys:
                pytest.skip(f"필수 설정이 누락되었습니다: {missing_keys}")
            
            return True
            
        except Exception as e:
            pytest.skip(f"실제 API 설정 확인 중 오류: {e}")
    
    def test_real_watchlist_basic(self, client, real_api_available):
        """실제 API를 사용한 기본 워치리스트 조회 테스트"""
        response = client.get("/api/watchlist")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2  # 기본적으로 삼성전자, SK하이닉스 포함
        
        # 기본 종목들 확인
        stock_codes = [item["stock_code"] for item in data]
        assert "005930" in stock_codes  # 삼성전자
        assert "000660" in stock_codes  # SK하이닉스
        
        print(f"\n[워치리스트 종목 수]: {len(data)}개")
        for item in data:
            print(f"  {item['stock_code']} {item['stock_name']}: {item['current_price']:,}원")
    
    def test_real_watchlist_data_structure(self, client, real_api_available):
        """실제 워치리스트 데이터 구조 테스트"""
        response = client.get("/api/watchlist")
        assert response.status_code == 200
        
        data = response.json()
        
        if len(data) > 0:
            first_item = data[0]
            
            required_fields = [
                "stock_code", "stock_name", "current_price", "profit_rate",
                "avg_price", "quantity", "macd", "macd_signal", "rsi",
                "volume", "change_amount", "change_rate", "updated_at"
            ]
            
            for field in required_fields:
                assert field in first_item, f"필수 필드 '{field}'가 누락되었습니다"
            
            # 기술적 지표 범위 검증
            rsi = first_item["rsi"]
            if rsi is not None and not pd.isna(rsi):
                assert 0 <= rsi <= 100, f"RSI 값이 범위를 벗어남: {rsi}"
            
            print(f"\n[{first_item['stock_code']}] {first_item['stock_name']}")
            print(f"  현재가: {first_item['current_price']:,}원")
            print(f"  MACD: {first_item['macd']}")
            print(f"  RSI: {first_item['rsi']}")
            print(f"  거래량: {first_item['volume']:,}")


@pytest.mark.integration
class TestRealTradingConditionsAPI:
    """실제 매매 조건 API 테스트"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_real_trading_conditions_get_and_update(self, client):
        """실제 매매 조건 조회 및 업데이트 테스트"""
        # 현재 설정 조회
        response = client.get("/api/trading/conditions")
        assert response.status_code == 200
        
        original_conditions = response.json()
        print(f"\n[현재 매매 조건]")
        print(f"매수 RSI 하한: {original_conditions['buy_conditions']['rsi_lower']}")
        print(f"매도 RSI 상한: {original_conditions['sell_conditions']['rsi_upper']}")
        print(f"자동매매 활성화: {original_conditions['auto_trading_enabled']}")
        
        # 설정 변경
        new_conditions = {
            "buy_conditions": {
                "rsi_lower": 25,
                "amount": 200000
            },
            "sell_conditions": {
                "rsi_upper": 75,
                "profit_target": 8.0
            },
            "auto_trading_enabled": not original_conditions["auto_trading_enabled"]
        }
        
        response = client.put("/api/trading/conditions", json=new_conditions)
        assert response.status_code == 200
        
        update_result = response.json()
        assert update_result["status"] == "success"
        
        # 변경된 설정 확인
        response = client.get("/api/trading/conditions")
        assert response.status_code == 200
        
        updated_conditions = response.json()
        assert updated_conditions["buy_conditions"]["rsi_lower"] == 25
        assert updated_conditions["buy_conditions"]["amount"] == 200000
        assert updated_conditions["sell_conditions"]["rsi_upper"] == 75
        assert updated_conditions["sell_conditions"]["profit_target"] == 8.0
        assert updated_conditions["auto_trading_enabled"] != original_conditions["auto_trading_enabled"]
        
        print(f"\n[변경된 매매 조건]")
        print(f"매수 RSI 하한: {updated_conditions['buy_conditions']['rsi_lower']}")
        print(f"매도 RSI 상한: {updated_conditions['sell_conditions']['rsi_upper']}")
        print(f"자동매매 활성화: {updated_conditions['auto_trading_enabled']}")
        
        # 원래 설정으로 복원
        response = client.put("/api/trading/conditions", json=original_conditions)
        assert response.status_code == 200
        print("\n[설정을 원래대로 복원했습니다]")


@pytest.mark.integration  
class TestRealMarketOverviewAPI:
    """실제 시장 개요 API 테스트"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_real_market_overview(self, client):
        """실제 시장 개요 데이터 테스트"""
        response = client.get("/api/market/overview")
        assert response.status_code == 200
        
        data = response.json()
        
        # 기본 구조 검증
        required_fields = ["market_status", "kospi", "kosdaq", "usd_krw", "top_gainers", "top_losers"]
        for field in required_fields:
            assert field in data
        
        # 지수 데이터 구조 검증
        for index_name in ["kospi", "kosdaq", "usd_krw"]:
            index_data = data[index_name]
            assert "current" in index_data
            assert "change" in index_data
            assert "change_rate" in index_data
            assert isinstance(index_data["current"], (int, float))
        
        print(f"\n[시장 개요]")
        print(f"시장 상태: {data['market_status']}")
        print(f"KOSPI: {data['kospi']['current']:.2f} ({data['kospi']['change']:+.2f}, {data['kospi']['change_rate']:+.2f}%)")
        print(f"KOSDAQ: {data['kosdaq']['current']:.2f} ({data['kosdaq']['change']:+.2f}, {data['kosdaq']['change_rate']:+.2f}%)")
        print(f"USD/KRW: {data['usd_krw']['current']:.2f}")
        
        # 상승/하락 종목
        if data["top_gainers"]:
            print(f"\n[상승 종목 ({len(data['top_gainers'])}개)]")
            for gainer in data["top_gainers"]:
                print(f"  {gainer['stock_code']} {gainer['stock_name']}: +{gainer['change_rate']:.2f}%")
        
        if data["top_losers"]:
            print(f"\n[하락 종목 ({len(data['top_losers'])}개)]")
            for loser in data["top_losers"]:
                print(f"  {loser['stock_code']} {loser['stock_name']}: {loser['change_rate']:.2f}%")


# 실제 API 테스트 실행을 위한 헬퍼 함수
def check_real_api_prerequisites():
    """실제 API 테스트 실행 전 사전 조건 확인"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    
    if not os.path.exists(config_path):
        print("❌ config.yaml 파일이 없습니다.")
        print("📋 다음 형식으로 config.yaml 파일을 생성해주세요:")
        print("""
KI_API_KEY: "your_api_key"
KI_SECRET_KEY: "your_secret_key"  
KI_ACCOUNT_NUMBER: "your_account_number"
KI_API_APPROVAL_KEY: "your_approval_key"
KI_ACCOUNT_ACCESS_TOKEN: "your_access_token"
KI_WEBSOCKET_APPROVAL_KEY: "your_websocket_key"
KI_USING_URL: "https://openapi.koreainvestment.com:9443"
KI_IS_PAPER_TRADING: false
        """)
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        required_keys = [
            'KI_API_KEY', 'KI_SECRET_KEY', 'KI_ACCOUNT_NUMBER',
            'KI_API_APPROVAL_KEY', 'KI_ACCOUNT_ACCESS_TOKEN'
        ]
        
        missing_keys = [key for key in required_keys if not config.get(key)]
        
        if missing_keys:
            print(f"❌ 필수 설정이 누락되었습니다: {missing_keys}")
            return False
        
        print("✅ 실제 API 테스트 실행 가능")
        print(f"📊 계좌번호: {config['KI_ACCOUNT_NUMBER']}")
        print(f"🌐 API URL: {config.get('KI_USING_URL', 'Default')}")
        print(f"📝 모의투자: {config.get('KI_IS_PAPER_TRADING', False)}")
        return True
        
    except Exception as e:
        print(f"❌ config.yaml 파일 읽기 오류: {e}")
        return False


if __name__ == "__main__":
    # 사전 조건 확인
    if check_real_api_prerequisites():
        print("\n🚀 실제 API 테스트를 실행할 수 있습니다!")
        print("다음 명령으로 테스트를 실행하세요:")
        print("python -m pytest tests/test_real_account_integration.py -v -s")
    else:
        print("\n❌ 실제 API 테스트를 실행할 수 없습니다.")
        print("위의 안내에 따라 설정을 완료한 후 다시 시도하세요.")