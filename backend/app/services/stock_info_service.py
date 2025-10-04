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
