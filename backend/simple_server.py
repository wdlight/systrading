"""
간단한 FastAPI 서버 - 프론트엔드 연결 테스트용
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import json
import random
import time
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

# 실제 API 클래스 import
try:
    from brokers.korea_investment.ki_api import KoreaInvestAPI
    from brokers.korea_investment.ki_env import KoreaInvestEnv
    import yaml
    REAL_API_AVAILABLE = True
except ImportError as e:
    print(f"Real API import failed: {e}")
    REAL_API_AVAILABLE = False

app = FastAPI()

# 실제 API 인스턴스 초기화
real_api = None
if REAL_API_AVAILABLE:
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            env = KoreaInvestEnv(config)
            base_headers = env.get_base_headers()
            full_config = env.get_full_config()
            
            real_api = KoreaInvestAPI(full_config, base_headers=base_headers)
            print("[OK] Real API initialized successfully")
        else:
            print("[FAIL] config.yaml not found")
    except Exception as e:
        print(f"[FAIL] Real API initialization failed: {e}")
        real_api = None

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", 
        "http://127.0.0.1:3002"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 추가적인 CORS 헤더 설정을 위한 미들웨어
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

app.add_middleware(CustomCORSMiddleware)

# 활성 WebSocket 연결들
active_connections = []

# 실제 매매 조건 설정 (전역 변수로 상태 유지)
trading_conditions_data = {
    "buy_conditions": {
        "rsi_lower": 30,
        "macd_signal": "positive_crossover",
        "amount": 100000,
        "enabled": True
    },
    "sell_conditions": {
        "rsi_upper": 70,
        "macd_signal": "negative_crossover",
        "profit_target": 5.0,
        "stop_loss": 2.0,
        "enabled": True
    },
    "auto_trading_enabled": False
}

@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "message": "Stock Trading API Server",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/hello")
async def hello():
    """간단한 Hello 엔드포인트"""
    return {
        "message": "Hello from Stock Trading Backend! 📈",
        "status": "server is running",
        "timestamp": "2025-09-10",
        "active_connections": len(active_connections)
    }

@app.get("/debug/tokens")
async def debug_tokens():
    """토큰 상태 디버그"""
    try:
        import sys
        import os
        
        # 프로젝트 루트 경로 추가
        project_root = os.path.join(os.path.dirname(__file__), '..')
        sys.path.append(project_root)
        
        from app.core.config import get_settings
        settings = get_settings()
        
        return {
            "config_loaded": True,
            "tokens": {
                "api_approval_key": settings.KI_API_APPROVAL_KEY[:30] + "..." if settings.KI_API_APPROVAL_KEY else "EMPTY",
                "websocket_approval_key": settings.KI_WEBSOCKET_APPROVAL_KEY[:30] + "..." if settings.KI_WEBSOCKET_APPROVAL_KEY else "EMPTY",
                "account_access_token": "Present" if settings.KI_ACCOUNT_ACCESS_TOKEN else "EMPTY",
                "using_url": settings.KI_USING_URL,
            },
            "config_values": {
                "api_key": settings.KI_API_KEY[:10] + "..." if settings.KI_API_KEY else "EMPTY",
                "account_number": settings.KI_ACCOUNT_NUMBER,
                "is_paper_trading": settings.KI_IS_PAPER_TRADING
            }
        }
    except Exception as e:
        return {
            "config_loaded": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.get("/health")
async def health_check():
    """상세 헬스체크"""
    return {
        "status": "healthy",
        "active_connections": len(active_connections)
    }

@app.get("/api/account/balance")
async def get_account_balance():
    """실제 계좌 잔고 데이터 또는 더미 데이터"""
    if real_api:
        try:
            # 실제 API 호출
            print(f"[DEBUG] Calling real_api.get_acct_balance()...")
            result = real_api.get_acct_balance()
            print(f"[DEBUG] real_api.get_acct_balance() result type: {type(result)}")
            if isinstance(result, tuple) and len(result) >= 2:
                print(f"[DEBUG] Account Balance - Total Value: {result[0]}, DataFrame Shape: {result[1].shape if hasattr(result[1], 'shape') else 'N/A'}")
                if hasattr(result[1], 'head'):
                    print(f"[DEBUG] DataFrame Head:\n{result[1].head()}")
            else:
                print(f"[DEBUG] Account Balance - Raw result: {result}")
            
            print(f"[DEBUG] API call returned: {type(result)}, length: {len(result) if result else 'None'}")
            if result and len(result) >= 2:
                total_value, df = result[0], result[1]

                
                positions = []
                total_profit_loss = 0
                
                if df is not None and not df.empty:
                    for idx, row in df.iterrows():
                        stock_code = str(row.get('종목코드', str(idx)))
                        quantity = int(row.get('보유수량', 0))
                        avg_price = int(row.get('매입단가', 0))
                        current_price = int(row.get('현재가', 0))
                        profit_loss = (current_price - avg_price) * quantity if avg_price > 0 else 0
                        profit_rate = float(row.get('수익률', 0.0))
                        
                        total_profit_loss += profit_loss
                        
                        position = {
                            "stock_code": stock_code,
                            "stock_name": str(row.get('종목명', '')),
                            "quantity": quantity,
                            "avg_price": avg_price,
                            "current_price": current_price,
                            "yesterday_price": current_price - int(row.get('전일대비', 0)),
                            "profit_loss": profit_loss,
                            "profit_loss_rate": profit_rate,
                            "profit_rate": profit_rate,
                            "evaluation_amount": current_price * quantity,
                            "change_rate": float(row.get('전일대비 등락률', 0.0))
                        }
                        positions.append(position)
                
                # 실제 데이터 반환
                return {
                    "total_value": int(total_value) if total_value else 0,
                    "total_evaluation_amount": int(total_value) if total_value else 0,
                    "total_profit_loss": total_profit_loss,
                    "total_profit_loss_rate": round((total_profit_loss / (int(total_value) - total_profit_loss)) * 100, 2) if total_value > total_profit_loss else 0.0,
                    "available_cash": max(0, int(total_value) - sum(p["evaluation_amount"] for p in positions)),
                    "positions": positions
                }
        except Exception as e:
            print(f"Real API call failed: {e}")
    
    # 더미 데이터 (API 실패시 또는 사용 불가시)
    return {
        "total_value": 10000000,
        "total_evaluation_amount": 10000000,
        "total_profit_loss": 500000,
        "total_profit_loss_rate": 5.26,
        "available_cash": 2000000,
        "positions": [
            {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "quantity": 10,
                "avg_price": 75000,
                "current_price": 78000,
                "yesterday_price": 77000,
                "profit_loss": 30000,
                "profit_loss_rate": 4.0,
                "profit_rate": 4.0,
                "evaluation_amount": 780000,
                "change_rate": 1.3
            }
        ]
    }

@app.get("/api/trading/conditions")
async def get_trading_conditions():
    """실제 매매 조건 반환"""
    global trading_conditions_data
    
    if real_api:
        try:
            # 실제 API나 서비스에서 매매 조건을 가져올 수 있다면
            # 여기서 처리. 현재는 전역 설정 반환
            return trading_conditions_data.copy()
        except Exception as e:
            print(f"[FAIL] Trading conditions API call failed: {e}")
    
    # 전역 설정 데이터 반환
    return trading_conditions_data.copy()

@app.put("/api/trading/conditions")
async def update_trading_conditions(conditions: dict):
    """매매 조건 업데이트 - 실제 설정에 저장"""
    global trading_conditions_data
    
    try:
        # 입력 검증 및 업데이트
        if "buy_conditions" in conditions:
            buy_conditions = conditions["buy_conditions"]
            if "rsi_lower" in buy_conditions:
                trading_conditions_data["buy_conditions"]["rsi_lower"] = max(0, min(100, int(buy_conditions["rsi_lower"])))
            if "macd_signal" in buy_conditions:
                trading_conditions_data["buy_conditions"]["macd_signal"] = buy_conditions["macd_signal"]
            if "amount" in buy_conditions:
                trading_conditions_data["buy_conditions"]["amount"] = max(1000, int(buy_conditions["amount"]))
            if "enabled" in buy_conditions:
                trading_conditions_data["buy_conditions"]["enabled"] = bool(buy_conditions["enabled"])
        
        if "sell_conditions" in conditions:
            sell_conditions = conditions["sell_conditions"]
            if "rsi_upper" in sell_conditions:
                trading_conditions_data["sell_conditions"]["rsi_upper"] = max(0, min(100, int(sell_conditions["rsi_upper"])))
            if "macd_signal" in sell_conditions:
                trading_conditions_data["sell_conditions"]["macd_signal"] = sell_conditions["macd_signal"]
            if "profit_target" in sell_conditions:
                trading_conditions_data["sell_conditions"]["profit_target"] = max(0.1, float(sell_conditions["profit_target"]))
            if "stop_loss" in sell_conditions:
                trading_conditions_data["sell_conditions"]["stop_loss"] = max(0.1, float(sell_conditions["stop_loss"]))
            if "enabled" in sell_conditions:
                trading_conditions_data["sell_conditions"]["enabled"] = bool(sell_conditions["enabled"])
        
        if "auto_trading_enabled" in conditions:
            trading_conditions_data["auto_trading_enabled"] = bool(conditions["auto_trading_enabled"])
        
        # 설정이 업데이트되었다는 로그
        print(f"[OK] 매매 조건 업데이트: {trading_conditions_data}")
        
        # 실제 구현에서는 파일이나 데이터베이스에 저장
        # save_trading_conditions_to_file(trading_conditions_data)
        
        return {
            "status": "success", 
            "message": "매매 조건이 업데이트되었습니다.",
            "updated_conditions": trading_conditions_data.copy()
        }
        
    except Exception as e:
        print(f"[FAIL] Trading conditions update failed: {e}")
        return {
            "status": "error",
            "message": f"매매 조건 업데이트 실패: {str(e)}"
        }

@app.post("/api/account/refresh")
async def refresh_account_info():
    """계좌 정보 갱신"""
    return {"status": "success", "message": "계좌 정보가 갱신되었습니다."}

def create_watchlist_item_debug(stock_code: str, account_row, chart_df):
    """계좌 데이터 + 차트 데이터로 워치리스트 아이템 생성 (Debug 강화)"""

    print(f"[DEBUG] create_watchlist_item_debug() 시작 - {stock_code}")

    # 계좌 데이터에서 기본 정보 추출
    current_price = int(account_row.get('현재가', 0))
    avg_price = int(account_row.get('매입단가', 0))
    quantity = int(account_row.get('보유수량', 0))
    profit_rate = float(account_row.get('수익률', 0.0))
    stock_name = str(account_row.get('종목명', ''))

    print(f"[DEBUG] 기본 정보 - 현재가: {current_price}, 평단: {avg_price}, 수량: {quantity}, 수익률: {profit_rate}%")

    # 기술지표 계산 또는 더미값
    if chart_df is not None and not chart_df.empty:
        print(f"[DEBUG] 차트 데이터 있음 - 기술지표 계산 시도")

        # RSI 계산 또는 더미값
        if 'RSI' in chart_df.columns:
            rsi = round(float(chart_df['RSI'].iloc[-1]), 2)
            print(f"[DEBUG] RSI 실제값: {rsi}")
        else:
            rsi = round(45.2 + (hash(stock_code) % 50), 2)
            print(f"[DEBUG] RSI 더미값: {rsi}")

        # MACD 계산 또는 더미값
        if 'MACD' in chart_df.columns and 'MACD_signal' in chart_df.columns:
            macd = round(float(chart_df['MACD'].iloc[-1]), 2)
            macd_signal = round(float(chart_df['MACD_signal'].iloc[-1]), 2)
            print(f"[DEBUG] MACD 실제값: {macd}, 시그널: {macd_signal}")
        else:
            macd = round(120.5 + (hash(stock_code) % 200) - 100, 2)
            macd_signal = round(macd - 2.2, 2)
            print(f"[DEBUG] MACD 더미값: {macd}, 시그널: {macd_signal}")
    else:
        print(f"[DEBUG] 차트 데이터 없음 - 모든 지표 더미값 사용")
        rsi = 50.0
        macd = 0.0
        macd_signal = 0.0

    # 워치리스트 아이템 구성
    stock_item = {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "current_price": current_price,
        "profit_rate": profit_rate,
        "avg_price": avg_price,
        "quantity": quantity,
        "macd": macd,
        "macd_signal": macd_signal,
        "rsi": rsi,
        "trailing_stop_activated": False,
        "trailing_stop_high": 0,
        "volume": 1000000 + (hash(stock_code) % 4000000),  # 더미값
        "change_amount": current_price - avg_price if avg_price > 0 else 0,
        "change_rate": profit_rate,
        "yesterday_price": avg_price,
        "high_price": current_price + abs((current_price - avg_price) // 2) if avg_price > 0 else current_price + 500,
        "low_price": current_price - abs((current_price - avg_price) // 2) if avg_price > 0 else current_price - 500,
        "updated_at": datetime.now().isoformat()
    }

    print(f"[DEBUG] create_watchlist_item_debug() 완료 - {stock_code}")
    return stock_item

@app.get("/api/watchlist")
async def get_watchlist():
    """실제 계좌 보유종목 기반 워치리스트 (Debug 강화)"""

    print(f"[DEBUG] === get_watchlist() 시작 ===")
    print(f"[DEBUG] real_api 사용 가능: {real_api is not None}")

    if real_api:
        try:
            print(f"[DEBUG] get_acct_balance() 호출 시작...")
            account_result = real_api.get_acct_balance()

            print(f"[DEBUG] get_acct_balance() 반환값 타입: {type(account_result)}")
            print(f"[DEBUG] get_acct_balance() 반환값 길이: {len(account_result) if account_result else 'None'}")

            if account_result and len(account_result) >= 2:
                total_value, df = account_result[0], account_result[1]

                print(f"[DEBUG] 총 평가금액: {total_value}")
                print(f"[DEBUG] DataFrame 타입: {type(df)}")
                print(f"[DEBUG] DataFrame 형태: {df.shape if df is not None else 'None'}")

                if df is not None and not df.empty:
                    print(f"[DEBUG] DataFrame 컬럼: {list(df.columns)}")
                    print(f"[DEBUG] DataFrame 전체 내용:")
                    print(df.to_string())

                    # 보유수량 > 0 필터링
                    holding_stocks = df[df['보유수량'] > 0]
                    print(f"[DEBUG] 보유종목 필터링 후 개수: {len(holding_stocks)}")
                    print(f"[DEBUG] 보유종목 리스트:")
                    print(holding_stocks.to_string())

                    result = []
                    for idx, row in holding_stocks.iterrows():
                        stock_code = str(row.get('종목코드'))
                        stock_name = str(row.get('종목명'))

                        print(f"\n[DEBUG] --- 종목 {stock_code}({stock_name}) 처리 시작 ---")
                        print(f"[DEBUG] 계좌 데이터: {row.to_dict()}")

                        # 차트 데이터 조회
                        print(f"[DEBUG] get_minute_chart_data({stock_code}) 호출...")
                        chart_df = real_api.get_minute_chart_data(stock_code)

                        print(f"[DEBUG] 차트 데이터 타입: {type(chart_df)}")
                        if chart_df is not None and not chart_df.empty:
                            print(f"[DEBUG] 차트 데이터 형태: {chart_df.shape}")
                            print(f"[DEBUG] 차트 데이터 컬럼: {list(chart_df.columns)}")
                            print(f"[DEBUG] 차트 데이터 마지막 5행:")
                            print(chart_df.tail().to_string())
                        else:
                            print(f"[DEBUG] 차트 데이터 없음 또는 빈 DataFrame")

                        # 워치리스트 아이템 생성
                        stock_item = create_watchlist_item_debug(stock_code, row, chart_df)
                        print(f"[DEBUG] 생성된 워치리스트 아이템: {stock_item}")

                        result.append(stock_item)
                        print(f"[DEBUG] --- 종목 {stock_code} 처리 완료 ---\n")

                    print(f"[DEBUG] 최종 워치리스트 개수: {len(result)}")
                    print(f"[DEBUG] 최종 반환 데이터:")
                    for item in result:
                        print(f"  - {item['stock_code']} ({item['stock_name']}): {item['current_price']}원")

                    return result
                else:
                    print(f"[DEBUG] DataFrame이 None이거나 비어있음")
            else:
                print(f"[DEBUG] account_result가 None이거나 길이가 2 미만")

        except Exception as e:
            print(f"[DEBUG] 예외 발생: {type(e).__name__}: {e}")
            import traceback
            print(f"[DEBUG] 상세 스택트레이스:")
            traceback.print_exc()

    print(f"[DEBUG] 빈 리스트 반환")
    return []

@app.get("/debug/account")
async def debug_account_info():
    """계좌 정보 디버그용 엔드포인트"""

    print(f"[DEBUG] /debug/account 호출됨")

    if not real_api:
        return {"error": "real_api 사용 불가"}

    try:
        print(f"[DEBUG] get_acct_balance() 호출...")
        account_result = real_api.get_acct_balance()

        result = {
            "api_available": True,
            "result_type": str(type(account_result)),
            "result_length": len(account_result) if account_result else 0,
        }

        if account_result and len(account_result) >= 2:
            total_value, df = account_result[0], account_result[1]

            result.update({
                "total_value": total_value,
                "dataframe_type": str(type(df)),
                "dataframe_shape": df.shape if df is not None else None,
                "dataframe_columns": list(df.columns) if df is not None else None,
                "dataframe_data": df.to_dict('records') if df is not None and not df.empty else [],
                "holding_count": len(df[df['보유수량'] > 0]) if df is not None and not df.empty else 0
            })

        print(f"[DEBUG] debug 결과: {result}")
        return result

    except Exception as e:
        print(f"[DEBUG] debug 예외: {e}")
        import traceback
        traceback.print_exc()

        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "api_available": False
        }

@app.get("/api/market/overview")
async def get_market_overview():
    """시장 개요 - 일부 실제 데이터 포함"""
    
    # 기본 시장 지수는 더미 데이터 (별도 API 필요)
    market_data = {
        "market_status": "open",
        "kospi": {
            "current": 2580.45 + random.uniform(-50, 50),
            "change": random.uniform(-30, 30),
            "change_rate": random.uniform(-1.5, 1.5)
        },
        "kosdaq": {
            "current": 850.23 + random.uniform(-20, 20),
            "change": random.uniform(-15, 15),
            "change_rate": random.uniform(-1.0, 1.0)
        },
        "usd_krw": {
            "current": 1340.5 + random.uniform(-10, 10),
            "change": random.uniform(-5, 5),
            "change_rate": random.uniform(-0.5, 0.5)
        }
    }
    
    # 종목별 실제 데이터 가져오기
    top_gainers_stocks = [
        {"stock_code": "005930", "stock_name": "삼성전자"},
        {"stock_code": "000660", "stock_name": "SK하이닉스"}
    ]
    
    top_losers_stocks = [
        {"stock_code": "035720", "stock_name": "카카오"}
    ]
    
    if real_api:
        try:
            # 실제 API에서 주요 종목 데이터 가져오기
            top_gainers = []
            for stock in top_gainers_stocks:
                stock_code = stock["stock_code"]
                stock_name = stock["stock_name"]
                
                df = real_api.get_minute_chart_data(stock_code)
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    current_price = int(latest["종가"])
                    
                    # 전일 대비 계산
                    if len(df) > 1:
                        prev_price = int(df.iloc[-2]["종가"])
                        change_rate = round((current_price - prev_price) / prev_price * 100, 2) if prev_price > 0 else 0.0
                    else:
                        change_rate = round(random.uniform(1.0, 5.0), 2)
                    
                    top_gainers.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "current_price": current_price,
                        "change_rate": abs(change_rate)  # 양수로 표시
                    })
                else:
                    # API 실패시 더미 데이터
                    top_gainers.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "current_price": 78000 if stock_code == "005930" else 125000,
                        "change_rate": round(random.uniform(1.0, 5.0), 2)
                    })
            
            # 하락 종목
            top_losers = []
            for stock in top_losers_stocks:
                stock_code = stock["stock_code"]
                stock_name = stock["stock_name"]
                
                df = real_api.get_minute_chart_data(stock_code)
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    current_price = int(latest["종가"])
                    
                    if len(df) > 1:
                        prev_price = int(df.iloc[-2]["종가"])
                        change_rate = round((current_price - prev_price) / prev_price * 100, 2) if prev_price > 0 else 0.0
                    else:
                        change_rate = round(random.uniform(-4.0, -1.0), 2)
                    
                    top_losers.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "current_price": current_price,
                        "change_rate": min(change_rate, -0.1)  # 음수로 표시
                    })
                else:
                    # API 실패시 더미 데이터
                    top_losers.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "current_price": 45000,
                        "change_rate": round(random.uniform(-4.0, -1.0), 2)
                    })
            
            market_data["top_gainers"] = top_gainers
            market_data["top_losers"] = top_losers
            return market_data
            
        except Exception as e:
            print(f"[FAIL] Market overview API call failed: {e}")
    
    # 더미 데이터 (API 실패시 또는 사용 불가시)
    market_data.update({
        "top_gainers": [
            {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "current_price": 78000 + random.randint(-2000, 3000),
                "change_rate": round(random.uniform(1.0, 5.0), 2)
            },
            {
                "stock_code": "000660", 
                "stock_name": "SK하이닉스",
                "current_price": 130000 + random.randint(-3000, 5000),
                "change_rate": round(random.uniform(1.0, 4.0), 2)
            }
        ],
        "top_losers": [
            {
                "stock_code": "035720",
                "stock_name": "카카오",
                "current_price": 45000 + random.randint(-5000, 1000),
                "change_rate": round(random.uniform(-4.0, -1.0), 2)
            }
        ]
    })
    
    return market_data

@app.get("/api/stocks/{stock_code}/chart")
async def get_stock_chart_data(
    stock_code: str,
    period: str = "D",
    format: str = "frontend"
):
    """
    삼성전자 등 종목의 차트 데이터 조회
    """
    try:
        if not real_api:
            return {"error": "Real API not available"}

        # 차트 데이터 조회 - real_api의 get_daily_price_chart 메소드 사용
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        formatted_start_date = start_date.strftime("%Y%m%d")
        formatted_end_date = end_date.strftime("%Y%m%d")

        # 차트 데이터 조회
        chart_df = real_api.get_daily_price_chart(stock_code, formatted_start_date, formatted_end_date, period)

        if chart_df is None or chart_df.empty:
            return {"output1": {}, "output2": []}

        # DataFrame을 API 응답 형식으로 변환
        chart_data = chart_df.to_dict('records')

        # KIS API 응답 형식에 맞춤
        renamed_data = []
        for item in chart_data:
            renamed_data.append({
                "stck_bsop_date": item.get("일자", ""),
                "stck_oprc": str(item.get("시가", "0")),
                "stck_hgpr": str(item.get("고가", "0")),
                "stck_lwpr": str(item.get("저가", "0")),
                "stck_clpr": str(item.get("종가", "0")),
                "acml_vol": str(item.get("거래량", "0")),
            })

        base_response = {"output1": {}, "output2": renamed_data}

        # format에 따른 응답 처리
        if format == 'frontend':
            return convert_to_frontend_format(stock_code, period, base_response)
        else:
            return base_response

    except Exception as e:
        print(f"Chart data API error: {e}")
        return {"error": f"Chart data retrieval failed: {str(e)}"}

def convert_to_frontend_format(stock_code: str, period: str, chart_data: dict) -> dict:
    """
    KIS API 응답을 프론트엔드 친화적 형식으로 변환
    """
    try:
        output2 = chart_data.get("output2", [])
        converted_data = []

        for item in output2:
            try:
                # 기본 OHLCV 데이터 변환
                open_price = int(item.get("stck_oprc", "0"))
                high_price = int(item.get("stck_hgpr", "0"))
                low_price = int(item.get("stck_lwpr", "0"))
                close_price = int(item.get("stck_clpr", "0"))
                volume = int(item.get("acml_vol", "0"))
                date_str = item.get("stck_bsop_date", "")

                # 날짜 형식 변환 (YYYYMMDD -> ISO format)
                try:
                    if len(date_str) == 8:
                        date_obj = datetime.strptime(date_str, "%Y%m%d")
                        timestamp = date_obj.isoformat()
                    else:
                        timestamp = date_str
                except:
                    timestamp = date_str

                converted_item = {
                    "timestamp": timestamp,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                    "tradingValue": close_price * volume,
                    # 실제 외국인/기관 데이터는 별도 API 필요 (임시값)
                    "foreignBuy": 0,
                    "foreignSell": 0,
                    "institutionalBuy": 0,
                    "institutionalSell": 0,
                    "individualBuy": volume,  # 임시로 개인투자자 매수량을 전체 거래량으로 설정
                    "individualSell": 0
                }

                # 데이터 유효성 검증
                if (low_price <= close_price <= high_price and
                    low_price <= open_price <= high_price and
                    all(price > 0 for price in [open_price, high_price, low_price, close_price]) and
                    volume >= 0):
                    converted_data.append(converted_item)

            except (ValueError, TypeError) as e:
                continue

        # 날짜순 정렬 (오래된 데이터부터)
        converted_data.sort(key=lambda x: x['timestamp'])

        # 통계 정보 계산
        total_volume = sum(item['volume'] for item in converted_data)
        avg_price = sum(item['close'] for item in converted_data) / len(converted_data) if converted_data else 0

        return {
            "success": True,
            "message": "차트 데이터 조회 성공",
            "data": converted_data,
            "metadata": {
                "stock_code": stock_code,
                "period": period,
                "count": len(converted_data),
                "total_volume": total_volume,
                "average_price": round(avg_price, 2),
                "date_range": {
                    "start": converted_data[0]['timestamp'] if converted_data else None,
                    "end": converted_data[-1]['timestamp'] if converted_data else None
                },
                "last_updated": datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"데이터 변환 실패: {str(e)}",
            "data": [],
            "metadata": {
                "stock_code": stock_code,
                "period": period,
                "count": 0,
                "last_updated": datetime.now().isoformat()
            }
        }

@app.get("/api/stocks/{stock_code}/price")
async def get_stock_current_price(stock_code: str):
    """
    종목의 실시간 현재가 정보 조회
    """
    try:
        if not real_api:
            return {"error": "Real API not available"}

        # 현재가 조회
        try:
            current_price_data = real_api.get_current_price(stock_code)

            if current_price_data is None:
                return {"error": f"Failed to get current price for {stock_code}"}

            # 응답 데이터 구조화
            response_data = {
                "success": True,
                "stock_code": stock_code,
                "current_price": int(current_price_data.get("stck_prpr", "0")),  # 현재가
                "change_amount": int(current_price_data.get("prdy_vrss", "0")),  # 전일대비
                "change_rate": float(current_price_data.get("prdy_ctrt", "0.0")),  # 등락률
                "volume": int(current_price_data.get("acml_vol", "0")),  # 누적거래량
                "trading_value": int(current_price_data.get("acml_tr_pbmn", "0")),  # 누적거래대금
                "high_price": int(current_price_data.get("stck_hgpr", "0")),  # 최고가
                "low_price": int(current_price_data.get("stck_lwpr", "0")),  # 최저가
                "open_price": int(current_price_data.get("stck_oprc", "0")),  # 시가
                "previous_close": int(current_price_data.get("stck_sdpr", "0")),  # 전일종가
                "market_cap": int(current_price_data.get("mktm", "0")),  # 시가총액
                "timestamp": datetime.now().isoformat(),
                "market_status": current_price_data.get("mksc_shrn_iscd", ""),  # 시장구분
            }

            return response_data

        except Exception as api_error:
            print(f"Current price API error: {api_error}")
            return {"error": f"API call failed: {str(api_error)}"}

    except Exception as e:
        print(f"Current price endpoint error: {e}")
        return {"error": f"Current price retrieval failed: {str(e)}"}

@app.get("/api/stocks/{stock_code}/quote")
async def get_stock_quote_info(stock_code: str):
    """
    종목의 상세 시세 정보 조회 (현재가 + 추가 정보)
    """
    try:
        if not real_api:
            return {"error": "Real API not available"}

        # 현재가와 차트 데이터를 결합해서 상세 정보 제공
        current_price_result = await get_stock_current_price(stock_code)

        if not current_price_result.get("success"):
            return current_price_result

        # 최근 차트 데이터도 함께 조회 (1일치)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)  # 최근 5일

        formatted_start_date = start_date.strftime("%Y%m%d")
        formatted_end_date = end_date.strftime("%Y%m%d")

        chart_df = real_api.get_daily_price_chart(stock_code, formatted_start_date, formatted_end_date, 'D')

        recent_candles = []
        if chart_df is not None and not chart_df.empty:
            recent_data = chart_df.tail(5).to_dict('records')  # 최근 5일
            for item in recent_data:
                recent_candles.append({
                    "date": item.get("일자", ""),
                    "open": int(item.get("시가", "0")),
                    "high": int(item.get("고가", "0")),
                    "low": int(item.get("저가", "0")),
                    "close": int(item.get("종가", "0")),
                    "volume": int(item.get("거래량", "0")),
                })

        # 종합 정보 구성
        quote_data = {
            **current_price_result,
            "recent_candles": recent_candles,
            "volatility": 0.0,  # 변동성 (계산 필요시 추가)
            "avg_volume_5d": sum(c["volume"] for c in recent_candles) / len(recent_candles) if recent_candles else 0,
            "price_range_5d": {
                "high": max(c["high"] for c in recent_candles) if recent_candles else 0,
                "low": min(c["low"] for c in recent_candles) if recent_candles else 0,
            },
            "last_updated": datetime.now().isoformat()
        }

        return quote_data

    except Exception as e:
        print(f"Quote info error: {e}")
        return {"error": f"Quote info retrieval failed: {str(e)}"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결"""
    client_host = websocket.client.host if websocket.client else "unknown"
    try:
        await websocket.accept()
        active_connections.append(websocket)
        print(f"WebSocket 연결됨: {client_host} - 활성 연결 수: {len(active_connections)}")
        
        # 연결 성공 메시지 전송
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket 연결이 성공했습니다.",
            "server_time": int(time.time())
        }))
        
        # 주기적으로 실시간 데이터 전송 (보유종목 기반)
        iteration = 0
        while True:
            iteration += 1
            print(f"\n[DEBUG] === WebSocket 전송 #{iteration} ({client_host}) ===")

            # 연결 상태 확인
            if websocket.client_state.name != "CONNECTED":
                print(f"[DEBUG] WebSocket 연결 상태 이상: {websocket.client_state.name}")
                break

            # 실시간 데이터도 보유종목 기반으로 생성
            realtime_data = []

            if real_api:
                try:
                    print(f"[DEBUG] WebSocket에서 get_acct_balance() 호출...")
                    account_result = real_api.get_acct_balance()

                    print(f"[DEBUG] WebSocket account_result 타입: {type(account_result)}")

                    if account_result and len(account_result) >= 2:
                        total_value, df = account_result[0], account_result[1]
                        print(f"[DEBUG] WebSocket 총 평가금액: {total_value}")

                        if df is not None and not df.empty:
                            holding_stocks = df[df['보유수량'] > 0]
                            print(f"[DEBUG] WebSocket 보유종목 수: {len(holding_stocks)}")

                            for idx, row in holding_stocks.iterrows():
                                stock_code = str(row.get('종목코드'))
                                print(f"[DEBUG] WebSocket 실시간 데이터 생성: {stock_code}")

                                # 실제 계좌 데이터 사용 (랜덤 변동 제거)
                                current_price = int(row.get('현재가', 0))
                                avg_price = int(row.get('매입단가', 0))
                                quantity = int(row.get('보유수량', 0))
                                profit_rate = float(row.get('수익률', 0.0))
                                change_amount = int(row.get('전일대비', 0))
                                change_rate = float(row.get('전일대비 등락률', 0.0))

                                # 차트 데이터에서 기술지표 조회 시도
                                try:
                                    chart_df = real_api.get_minute_chart_data(stock_code)
                                    if chart_df is not None and not chart_df.empty:
                                        # RSI 계산 또는 더미값
                                        if 'RSI' in chart_df.columns:
                                            rsi = round(float(chart_df['RSI'].iloc[-1]), 2)
                                        else:
                                            rsi = 50.0

                                        # MACD 계산 또는 더미값
                                        if 'MACD' in chart_df.columns and 'MACD_signal' in chart_df.columns:
                                            macd = round(float(chart_df['MACD'].iloc[-1]), 2)
                                            macd_signal = round(float(chart_df['MACD_signal'].iloc[-1]), 2)
                                        else:
                                            macd = 0.0
                                            macd_signal = 0.0

                                        # 거래량
                                        if '거래량' in chart_df.columns:
                                            volume = int(chart_df['거래량'].iloc[-1])
                                        else:
                                            volume = 0

                                        # 고가/저가
                                        if '고가' in chart_df.columns and '저가' in chart_df.columns:
                                            high_price = int(chart_df['고가'].iloc[-1])
                                            low_price = int(chart_df['저가'].iloc[-1])
                                        else:
                                            high_price = current_price
                                            low_price = current_price
                                    else:
                                        # 차트 데이터 없을 때 기본값
                                        rsi = 50.0
                                        macd = 0.0
                                        macd_signal = 0.0
                                        volume = 0
                                        high_price = current_price
                                        low_price = current_price
                                except Exception as chart_error:
                                    print(f"[DEBUG] {stock_code} 차트 데이터 조회 실패: {chart_error}")
                                    rsi = 50.0
                                    macd = 0.0
                                    macd_signal = 0.0
                                    volume = 0
                                    high_price = current_price
                                    low_price = current_price

                                realtime_item = {
                                    "stock_code": stock_code,
                                    "stock_name": str(row.get('종목명', '')),
                                    "current_price": current_price,
                                    "profit_rate": profit_rate,
                                    "avg_price": avg_price,
                                    "quantity": quantity,
                                    "macd": macd,
                                    "macd_signal": macd_signal,
                                    "rsi": rsi,
                                    "trailing_stop_activated": False,
                                    "trailing_stop_high": 0,
                                    "volume": volume,
                                    "change_amount": change_amount,
                                    "change_rate": change_rate,
                                    "yesterday_price": current_price - change_amount if change_amount != 0 else current_price,
                                    "high_price": high_price,
                                    "low_price": low_price,
                                    "updated_at": f"2025-09-17T{time.strftime('%H:%M:%S')}Z"
                                }

                                realtime_data.append(realtime_item)
                                print(f"[DEBUG] {stock_code} 실시간 데이터: {current_price}원 (수익률: {profit_rate}%)")
                        else:
                            print(f"[DEBUG] WebSocket DataFrame 없음 - 빈 실시간 데이터")
                    else:
                        print(f"[DEBUG] WebSocket account_result 문제")

                except Exception as e:
                    print(f"[DEBUG] WebSocket 계좌 조회 실패: {e}")

            print(f"[DEBUG] WebSocket 전송할 실시간 데이터 개수: {len(realtime_data)}")

            data = {
                "type": "watchlist_update",
                "data": realtime_data,
                "timestamp": int(time.time())
            }

            try:
                await websocket.send_text(json.dumps(data))
                print(f"[DEBUG] WebSocket 데이터 전송 성공 ({client_host}): {len(realtime_data)}개 종목")
                await asyncio.sleep(2)  # 2초마다 데이터 전송
            except Exception as send_error:
                print(f"[DEBUG] WebSocket 전송 오류 ({client_host}): {send_error}")
                break
            
    except WebSocketDisconnect as e:
        if websocket in active_connections:
            active_connections.remove(websocket)
        print(f"WebSocket 정상 연결 해제: {client_host} (code: {e.code}) - 활성 연결 수: {len(active_connections)}")
    except Exception as e:
        if websocket in active_connections:
            active_connections.remove(websocket)
        print(f"WebSocket 예외 발생 ({client_host}): {type(e).__name__}: {e}")
        print(f"활성 연결 수: {len(active_connections)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )