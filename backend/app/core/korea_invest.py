"""
한국투자증권 API 서비스
기존 utils.py의 KoreaInvestAPI를 FastAPI와 통합
"""

import sys
import os
import pandas as pd
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from utils.logger import logger

# 상위 디렉토리의 utils.py 임포트를 위한 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from brokers.korea_investment.ki_api import KoreaInvestAPI
    from brokers.korea_investment.ki_env import KoreaInvestEnv
except ImportError as e:
    logger.error(f"brokers.korea_investment 모듈 임포트 실패: {e}")
    # 임시 더미 클래스들
    class KoreaInvestAPI:
        def __init__(self, *args, **kwargs):
            pass
    class KoreaInvestEnv:
        def __init__(self, *args, **kwargs):
            pass


class KoreaInvestAPIService:
    """한국투자증권 API 서비스 래퍼 클래스"""
    
    def __init__(self, settings):
        self.settings = settings
        self.api_instance = None
        self.is_connected = False
        self.last_error = None
        
        # 비동기 실행을 위한 executor
        self.executor = None
        
        self._initialize_api()
    
    def _initialize_api(self):
        """API 인스턴스 초기화"""
        try:
            # 기존 config.yaml 형태의 설정을 dict로 변환
            config = {
                'api_key': self.settings.KI_API_KEY,
                'api_secret_key': self.settings.KI_SECRET_KEY,
                'stock_account_number': self.settings.KI_ACCOUNT_NUMBER,
                'htsid': self.settings.KI_HTSID,
                'custtype': self.settings.KI_CUSTTYPE,
                'is_paper_trading': self.settings.KI_IS_PAPER_TRADING,
                'my_agent': self.settings.KI_USER_AGENT,
                'url': self.settings.KI_API_URL,
                'websocket_url': self.settings.KI_WEBSOCKET_URL,
                'paper_url': self.settings.KI_PAPER_URL,
                'paper_websocket_url': self.settings.KI_PAPER_WEBSOCKET_URL,
                'api_approval_key': self.settings.KI_API_APPROVAL_KEY,
                'access_tocken': self.settings.KI_ACCESS_TOKEN,
                'websocket_approval_key': self.settings.KI_WEBSOCKET_APPROVAL_KEY,
                'using_url': self.settings.KI_USING_URL,
                'account_access_token': self.settings.KI_ACCOUNT_ACCESS_TOKEN
            }
            
            # 환경 설정 초기화
            env_cls = KoreaInvestEnv(config)
            base_headers = env_cls.get_base_headers()
            full_config = env_cls.get_full_config()
            
            # API 인스턴스 생성
            self.api_instance = KoreaInvestAPI(full_config, base_headers=base_headers)
            self.is_connected = True
            
            logger.info("한국투자증권 API 서비스가 초기화되었습니다.")
            
        except Exception as e:
            self.last_error = str(e)
            self.is_connected = False
            logger.error(f"한국투자증권 API 초기화 실패: {e}")
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """동기 함수를 비동기로 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    async def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """계좌 잔고 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            # 동기 함수를 비동기로 실행
            result = await self._run_in_executor(self.api_instance.get_acct_balance)
            
            if result and len(result) >= 2:
                total_value, df = result[0], result[1]
                
                # DataFrame을 JSON 직렬화 가능한 형태로 변환
                positions = []
                total_unrealized_pnl = 0
                total_invested_amount = 0
                
                if isinstance(df, pd.DataFrame) and not df.empty:
                    for idx, row in df.iterrows():
                        # ki_api.py DataFrame 컬럼명 매핑 (정확한 컬럼명 사용)
                        stock_code = str(row.get("종목코드", str(idx)))
                        quantity = int(row.get("보유수량", 0))
                        avg_price = int(row.get("매입단가", 0))
                        current_price = int(row.get("현재가", 0))
                        
                        # 평가손익 계산 (실제 컬럼이 없을 경우)
                        unrealized_pnl = (current_price - avg_price) * quantity if avg_price > 0 else 0
                        total_unrealized_pnl += unrealized_pnl
                        total_invested_amount += avg_price * quantity
                        
                        position = {
                            "stock_code": stock_code,
                            "stock_name": str(row.get("종목명", "")),
                            "quantity": quantity,
                            "sellable_quantity": int(row.get("매도가능수량", quantity)),
                            "avg_price": avg_price,
                            "current_price": current_price,
                            "unrealized_pnl": unrealized_pnl,
                            "profit_rate": float(row.get("수익률", 0.0)),
                            "day_change": int(row.get("전일대비", 0)),
                            "day_change_rate": float(row.get("전일대비 등락률", 0.0))
                        }
                        positions.append(position)
                
                # 가용현금 계산 (총평가금액 - 투자원금)
                available_cash = max(0, int(total_value) - total_invested_amount) if total_value and total_invested_amount else 0
                
                return {
                    "total_value": int(total_value) if total_value else 0,
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "available_cash": available_cash,
                    "positions": positions,
                    "dataframe": df  # 내부 처리용
                }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"계좌 잔고 조회 실패: {e}")
        
        return None
    
    async def buy_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """매수 주문 (비동기)"""
        if not self.is_connected or not self.api_instance:
            return {"success": False, "message": "API가 연결되지 않았습니다."}
        
        try:
            result = await self._run_in_executor(
                self.api_instance.buy_order, 
                stock_code, order_qty, order_price, order_type
            )
            
            return {
                "success": True,
                "message": "매수 주문이 성공적으로 접수되었습니다.",
                "data": result
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"매수 주문 실패: {e}")
            return {"success": False, "message": f"매수 주문 실패: {str(e)}"}
    
    async def sell_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """매도 주문 (비동기)"""
        if not self.is_connected or not self.api_instance:
            return {"success": False, "message": "API가 연결되지 않았습니다."}
        
        try:
            result = await self._run_in_executor(
                self.api_instance.sell_order,
                stock_code, order_qty, order_price, order_type
            )
            
            return {
                "success": True,
                "message": "매도 주문이 성공적으로 접수되었습니다.",
                "data": result
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"매도 주문 실패: {e}")
            return {"success": False, "message": f"매도 주문 실패: {str(e)}"}
    
    async def get_minute_chart_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """1분봉 차트 데이터 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            result = await self._run_in_executor(
                self.api_instance.get_minute_chart_data,
                stock_code
            )
            return result
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"차트 데이터 조회 실패: {e}")
            return None
    
    async def get_current_price(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """현재가 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            # 실제 현재가 조회 API 호출 (구체적 메서드명은 utils.py 확인 필요)
            # 임시로 기본 구조만 제공
            result = await self._run_in_executor(
                getattr(self.api_instance, 'get_current_price', lambda x: None),
                stock_code
            )
            
            if result:
                return {
                    "stock_code": stock_code,
                    "current_price": result.get("현재가", 0),
                    "change": result.get("전일대비", 0),
                    "change_rate": result.get("등락률", 0.0),
                    "volume": result.get("거래량", 0)
                }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"현재가 조회 실패: {e}")
        
        return None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 확인"""
        return {
            "connected": self.is_connected,
            "last_error": self.last_error,
            "api_instance": self.api_instance is not None
        }
    
    async def reconnect(self) -> bool:
        """연결 재시도"""
        try:
            self._initialize_api()
            return self.is_connected
        except Exception as e:
            logger.error(f"재연결 실패: {e}")
            return False
    
    def __del__(self):
        """소멸자"""
        if self.executor:
            self.executor.shutdown(wait=False)