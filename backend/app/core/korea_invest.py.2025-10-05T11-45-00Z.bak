"""
한국투자증권 API 서비스
기존 utils.py의 KoreaInvestAPI를 FastAPI와 통합
"""

import sys
import os
import pandas as pd
import asyncio
from functools import partial
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta

from app.models.schemas import ChartCandle
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from loguru import logger
except ImportError:
    # Fallback logger if loguru is not available
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

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
    
    async def get_minute_chart_data(self, stock_code: str) -> Optional[List[ChartCandle]]:
        """1분봉 차트 데이터 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            logger.debug(f"Calling ki_api method: {self.api_instance.get_minute_chart_data.__name__}")
            df = await self._run_in_executor(
                self.api_instance.get_minute_chart_data,
                stock_code
            )

            if df is None or df.empty:
                return []

            # 중복 제거: 일자와 시간이 같은 데이터는 첫 번째만 유지
            df = df.drop_duplicates(subset=['일자', '시간'], keep='first')
            logger.info(f"분봉 데이터 중복 제거 완료: {len(df)}개")

            chart_candles: List[ChartCandle] = []
            for _, row in df.iterrows():
                try:
                    # '일자' (YYYYMMDD)와 '시간' (HHMMSS)을 결합하여 ISO 형식의 타임스탬프 생성
                    date_str = str(row['일자'])
                    time_str = str(row['시간']).zfill(6) # HHMMSS 형식으로 6자리 채우기
                    # KIS API의 시간은 000000 ~ 235959 이므로, 240000은 다음 날 000000으로 처리
                    if time_str == "240000":
                        # 다음 날 00시 00분 00초로 처리 (날짜도 하루 증가)
                        dt_object = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                        timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")
                    else:
                        dt_object = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                        timestamp_iso = dt_object.isoformat()

                    candle = ChartCandle(
                        timestamp=timestamp_iso,
                        open=float(row['시가']),
                        high=float(row['고가']),
                        low=float(row['저가']),
                        close=float(row['종가']),
                        volume=int(row['거래량'])
                    )
                    chart_candles.append(candle)
                except Exception as e:
                    logger.warning(f"분봉 데이터 변환 중 오류 발생: {e}, 데이터: {row}")
                    continue
            
            return chart_candles
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"차트 데이터 조회 실패: {e}")
            return None

    async def get_daily_minute_chart_data(self, stock_code: str, target_date: datetime) -> Optional[List[ChartCandle]]:
        """과거 특정 날짜의 1분봉 차트 데이터 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None

        try:
            logger.info(f"과거 분봉 데이터 조회: {stock_code}, {target_date.strftime('%Y-%m-%d')}")
            df = await self._run_in_executor(
                self.api_instance.get_daily_minute_chart_data,
                stock_code,
                target_date
            )

            if df is None or df.empty:
                logger.warning(f"과거 분봉 데이터 없음: {stock_code}, {target_date.strftime('%Y-%m-%d')}")
                return []

            # 중복 제거
            df = df.drop_duplicates(subset=['일자', '시간'], keep='first')
            logger.info(f"과거 분봉 데이터 중복 제거 완료: {len(df)}개")

            chart_candles: List[ChartCandle] = []
            for _, row in df.iterrows():
                try:
                    date_str = str(row['일자'])
                    time_str = str(row['시간']).zfill(6)

                    if time_str == "240000":
                        dt_object = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                        timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")
                    else:
                        dt_object = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                        timestamp_iso = dt_object.isoformat()

                    candle = ChartCandle(
                        timestamp=timestamp_iso,
                        open=float(row['시가']),
                        high=float(row['고가']),
                        low=float(row['저가']),
                        close=float(row['종가']),
                        volume=int(row['거래량'])
                    )
                    chart_candles.append(candle)
                except Exception as e:
                    logger.warning(f"과거 분봉 데이터 변환 중 오류: {e}")
                    continue

            logger.info(f"✅ 과거 분봉 데이터 변환 완료: {len(chart_candles)}개 캔들")
            return chart_candles

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"과거 차트 데이터 조회 실패: {e}")
            return None

    async def get_minute_chart_data_from(
        self,
        stock_code: str,
        start_time: str  # HHMMSS 형식
    ) -> Optional[List[ChartCandle]]:
        """
        특정 시간부터 현재까지 분봉 데이터 조회 (Gap-fill 최적화)

        Args:
            stock_code: 종목 코드 (예: "005930")
            start_time: 시작 시간 HHMMSS 형식 (예: "113000" = 11:30:00)

        Returns:
            start_time 이후 분봉 데이터만 반환

        Example:
            # 11:30부터 현재까지만 조회 (Gap-fill 최적화)
            candles = await service.get_minute_chart_data_from("005930", "113000")
        """
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None

        try:
            logger.info(f"Gap 구간 조회: {stock_code}, {start_time}~현재")

            # API 호출 (start_time 지정) - functools.partial 사용
            func = partial(
                self.api_instance.get_minute_chart_data,
                stock_code,
                start_time=start_time,  # 🔑 Gap 시작 시간
                max_count=None
            )
            df = await self._run_in_executor(func)

            if df is None or df.empty:
                logger.info(f"Gap 구간 데이터 없음: {stock_code}, {start_time}~")
                return []

            # 중복 제거: 일자와 시간이 같은 데이터는 첫 번째만 유지
            df = df.drop_duplicates(subset=['일자', '시간'], keep='first')
            logger.info(f"Gap 데이터 수집 완료: {len(df)}개 ({start_time}~현재)")

            # DataFrame → ChartCandle 변환
            chart_candles: List[ChartCandle] = []
            for _, row in df.iterrows():
                try:
                    date_str = str(row['일자'])
                    time_str = str(row['시간']).zfill(6)  # HHMMSS 형식으로 6자리 채우기

                    # KIS API의 시간은 000000 ~ 235959 이므로, 240000은 다음 날 000000으로 처리
                    if time_str == "240000":
                        dt_object = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                        timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")
                    else:
                        dt_object = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                        timestamp_iso = dt_object.isoformat()

                    candle = ChartCandle(
                        timestamp=timestamp_iso,
                        open=float(row['시가']),
                        high=float(row['고가']),
                        low=float(row['저가']),
                        close=float(row['종가']),
                        volume=int(row['거래량'])
                    )
                    chart_candles.append(candle)
                except Exception as e:
                    logger.warning(f"Gap 데이터 변환 중 오류 발생: {e}, 데이터: {row}")
                    continue

            return chart_candles

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Gap 구간 조회 실패: {stock_code}, {start_time}~, 오류: {e}")
            return None

    async def get_daily_minute_chart_data(
        self,
        stock_code: str,
        target_date
    ):
        """
        특정 날짜의 전체 분봉 데이터 조회 (과거 날짜용)
        
        Args:
            stock_code: 종목코드
            target_date: 조회 날짜 (datetime 또는 "YYYYMMDD")
        
        Returns:
            DataFrame: 해당 날짜의 전체 분봉 데이터
        """
        try:
            # 비동기 실행자를 통해 동기 메서드 호출
            result = await self._run_in_executor(
                self.api_instance.get_daily_minute_chart_data,
                stock_code,
                target_date
            )
            return result
        except Exception as e:
            logger.error(f"❌ 과거 분봉 데이터 조회 실패: {e}")
            return None

    async def get_daily_price_chart(self, stock_code: str, start_date: str, end_date: str, period_code: str = 'D') -> Optional[pd.DataFrame]:
        """일/주/월봉 차트 데이터 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            result = await self._run_in_executor(
                self.api_instance.get_daily_price_chart,
                stock_code,
                start_date,
                end_date,
                period_code
            )
            return result
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"일/주/월봉 차트 데이터 조회 실패: {e}")
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