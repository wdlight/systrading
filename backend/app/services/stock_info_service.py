from typing import List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

# pykrx는 vkis 가상환경에 설치되어 있어야 합니다.
# pip install pykrx
from pykrx import stock

class StockInfoService:
    def __init__(self):
        self._stock_list_cache: List[Dict[str, str]] = []
        self._last_updated: Optional[datetime] = None
        self._cache_duration = timedelta(hours=12) # 12시간 캐시 유지
        logger.info("StockInfoService 초기화 완료.")

    async def _fetch_all_stocks_from_pykrx(self) -> List[Dict[str, str]]:
        logger.info("pykrx를 통해 전체 종목 리스트를 가져옵니다...")
        try:
            tickers_kospi = stock.get_market_ticker_list(market="KOSPI")
            tickers_kosdaq = stock.get_market_ticker_list(market="KOSDAQ")

            all_tickers = tickers_kospi + tickers_kosdaq
            
            rows = []
            for t in all_tickers:
                try:
                    name = stock.get_market_ticker_name(t)
                    rows.append({"value": t, "label": name})
                except Exception as e:
                    logger.warning(f"종목명 조회 실패: {t}, 오류: {e}")
                    continue
            
            logger.info(f"pykrx에서 {len(rows)}개 종목 정보 로드 완료.")
            return rows
        except Exception as e:
            logger.error(f"pykrx 종목 정보 로드 중 오류 발생: {e}", exc_info=True)
            return []

    async def get_all_stocks(self, force_update: bool = False) -> List[Dict[str, str]]:
        now = datetime.now()
        if force_update or not self._stock_list_cache or \
           (self._last_updated and (now - self._last_updated) > self._cache_duration):
            logger.info("종목 리스트 캐시 업데이트를 시작합니다.")
            self._stock_list_cache = await self._fetch_all_stocks_from_pykrx()
            self._last_updated = now
            logger.info(f"종목 리스트 캐시 업데이트 완료. {len(self._stock_list_cache)}개 종목.")
        else:
            logger.info("종목 리스트 캐시를 사용합니다.")
        
        return self._stock_list_cache

    async def get_market_indices(self) -> Dict[str, Dict[str, float]]:
        """KOSPI, KOSDAQ 지수를 pykrx로 조회합니다."""
        today = datetime.now().strftime("%Y%m%d")
        try:
            df = stock.get_index_ohlcv(today, today, "KOSPI")
            kospi = df.iloc[0]
            
            df_kosdaq = stock.get_index_ohlcv(today, today, "KOSDAQ")
            kosdaq = df_kosdaq.iloc[0]

            return {
                "kospi": {
                    "current": kospi['종가'],
                    "change": kospi['종가'] - kospi['시가'],
                    "change_rate": (kospi['종가'] / kospi['시가'] - 1) * 100 if kospi['시가'] != 0 else 0,
                },
                "kosdaq": {
                    "current": kosdaq['종가'],
                    "change": kosdaq['종가'] - kosdaq['시가'],
                    "change_rate": (kosdaq['종가'] / kosdaq['시가'] - 1) * 100 if kosdaq['시가'] != 0 else 0,
                }
            }
        except Exception as e:
            logger.warning(f"pykrx 지수 조회 실패: {e}. 더미 데이터를 사용합니다.")
            return {
                "kospi": {"current": 2600.0, "change": 10.5, "change_rate": 0.4},
                "kosdaq": {"current": 850.0, "change": -5.2, "change_rate": -0.6},
            }

    async def get_market_overview(self) -> Dict[str, Any]:
        """시장 현황 데이터를 구성하여 반환합니다."""
        indices = await self.get_market_indices()
        
        # 주요 종목 정보 (더미)
        top_gainers = [{"stock_code": "005930", "stock_name": "삼성전자", "current_price": 78000, "change_rate": 1.5}]
        top_losers = [{"stock_code": "035720", "stock_name": "카카오", "current_price": 45000, "change_rate": -2.1}]

        return {
            "market_status": "open",
            "kospi": indices["kospi"],
            "kosdaq": indices["kosdaq"],
            "usd_krw": {"current": 1350.0, "change": 2.0, "change_rate": 0.15}, # 환율은 더미
            "top_gainers": top_gainers,
            "top_losers": top_losers,
        }
