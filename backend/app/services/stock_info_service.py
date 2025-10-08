from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

# pykrx는 vkis 가상환경에 설치되어 있어야 합니다.
# pip install pykrx
from pykrx import stock
from app.core.korea_invest import KoreaInvestAPIService

class StockInfoService:
    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self._stock_list_cache: List[Dict[str, str]] = []
        self._last_updated: Optional[datetime] = None
        self._cache_duration = timedelta(hours=12) # 12시간 캐시 유지
        self.korea_invest_service = korea_invest_service
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
        """초기 로딩을 위한 시장 지수 더미 데이터를 반환합니다. 실제 데이터는 WebSocket을 통해 제공됩니다."""
        logger.info("Returning initial dummy data for market indices. Real data will be pushed via WebSocket.")
        try:
            indices: Dict[str, Dict[str, float]] = {}

            request_map = {
                "kospi": {
                    "type": "domestic",
                    "candidates": [("U", "0001")],
                },
                "kosdaq": {
                    "type": "domestic",
                    "candidates": [
                        ("J", "1001"),
                        ("J", "0201"),
                        ("J", "1501"),
                        ("J", "2001"),
                        ("U", "1001"),
                    ],
                },
                "nasdaq": {
                    "type": "overseas",
                    "candidates": [
                        ("N", "NDX"),
                        ("N", "IXIC"),
                    ],
                },
                "sp500": {
                    "type": "overseas",
                    "candidates": [
                        ("N", "US500"),
                        ("N", "SPX"),
                    ],
                },
                "usd_krw": {
                    "type": "overseas",
                    "candidates": [
                        ("X", "FX@KRW"),
                    ],
                },
            }

            def zero_payload(market_code: str, index_code: str) -> Dict[str, float]:
                return {
                    "code": index_code,
                    "market": market_code,
                    "current": 0.0,
                    "change": 0.0,
                    "change_rate": 0.0,
                }

            fetch_map = {
                "domestic": self.korea_invest_service.get_index_current_price,
                "overseas": self.korea_invest_service.get_overseas_index_price,
            }

            for label, spec in request_map.items():
                candidates = spec.get("candidates", [])
                fetch_type = spec.get("type", "domestic")
                fetcher = fetch_map.get(fetch_type, self.korea_invest_service.get_index_current_price)
                result_data = None
                last_meta = None

                for market_code, index_code in candidates:
                    result = await fetcher(
                        index_code=index_code,
                        market_code=market_code
                    )

                    raw = self.korea_invest_service.get_last_raw_response() or {}
                    if isinstance(raw, dict):
                        meta = raw.get("meta")
                    else:
                        meta = None
                    last_meta = meta

                    logger.info(
                        "지수 조회 응답",
                        extra={
                            "label": label,
                            "fetch_type": fetch_type,
                            "market_code": market_code,
                            "index_code": index_code,
                            "meta": meta,
                            "values": result.model_dump() if result else None,
                        }
                    )

                    if (
                        result
                        and (result.current != 0.0 or result.change != 0.0 or result.change_rate != 0.0)
                    ):
                        result_data = result
                        break

                if result_data:
                    indices[label] = {
                        "code": result_data.index_code,
                        "market": result_data.market_code,
                        "current": result_data.current,
                        "change": result_data.change,
                        "change_rate": result_data.change_rate,
                    }
                else:
                    cached_result = None
                    for market_code, index_code in candidates:
                        cached = self.korea_invest_service.get_cached_index(index_code)
                        if not cached:
                            continue

                        current = cached.get("current")
                        change = cached.get("change")
                        change_rate = cached.get("change_rate")

                        if any(
                            value not in (None, 0.0, 0)
                            for value in (current, change, change_rate)
                        ):
                            cached_result = {
                                "code": cached.get("index_code", index_code),
                                "market": cached.get("market_code", market_code),
                                "current": current or 0.0,
                                "change": change or 0.0,
                                "change_rate": change_rate or 0.0,
                            }
                            logger.info(
                                f"{label.upper()} 지수를 WebSocket 캐시에서 사용합니다.",
                                extra={
                                    "index_code": index_code,
                                    "market_code": market_code,
                                    "cached_timestamp": cached.get("timestamp"),
                                }
                            )
                            break

                    if cached_result:
                        indices[label] = cached_result
                        continue

                    # 실패 시 최근 메타 정보와 함께 0 값 반환
                    if last_meta:
                        logger.warning(
                            f"{label.upper()} 지수 데이터를 가져오지 못했습니다. 마지막 메타={last_meta}"
                        )
                    else:
                        logger.warning(
                            f"{label.upper()} 지수 데이터를 가져오지 못했습니다. 후보 코드 모두 실패"
                        )

                    fallback_market = candidates[-1][0] if candidates else "U"
                    fallback_code = candidates[-1][1] if candidates else "0001"
                    indices[label] = zero_payload(fallback_market, fallback_code)

            return indices
        except Exception as e:
            logger.error(f"Failed to fetch market indices: {e}", exc_info=True)
            return {
                "kospi": {"code": "0001", "market": "U", "current": 0.0, "change": 0.0, "change_rate": 0.0},
                "kosdaq": {"code": "1001", "market": "J", "current": 0.0, "change": 0.0, "change_rate": 0.0},
                "nasdaq": {"code": "NDX", "market": "N", "current": 0.0, "change": 0.0, "change_rate": 0.0},
                "sp500": {"code": "US500", "market": "N", "current": 0.0, "change": 0.0, "change_rate": 0.0},
                "usd_krw": {"code": "FX@KRW", "market": "X", "current": 0.0, "change": 0.0, "change_rate": 0.0},
            }

    async def get_market_overview(self) -> Dict[str, Any]:
        """시장 현황 데이터를 구성하여 반환합니다."""
        indices = await self.get_market_indices()
        
        # 주요 종목 정보 (더미)
        top_gainers = [{"stock_code": "005930", "stock_name": "삼성전자", "current_price": 78000, "change_rate": 1.5}]
        top_losers = [{"stock_code": "035720", "stock_name": "카카오", "current_price": 45000, "change_rate": -2.1}]

        return {
            "market_status": "open",
            "kospi": indices.get("kospi", {"code": "0001", "market": "U", "current": 0.0, "change": 0.0, "change_rate": 0.0}),
            "kosdaq": indices.get("kosdaq", {"code": "1001", "market": "J", "current": 0.0, "change": 0.0, "change_rate": 0.0}),
            "nasdaq": indices.get("nasdaq", {"code": "NDX", "market": "N", "current": 0.0, "change": 0.0, "change_rate": 0.0}),
            "sp500": indices.get("sp500", {"code": "US500", "market": "N", "current": 0.0, "change": 0.0, "change_rate": 0.0}),
            "usd_krw": indices.get("usd_krw", {"code": "FX@KRW", "market": "X", "current": 0.0, "change": 0.0, "change_rate": 0.0}),
            "top_gainers": top_gainers,
            "top_losers": top_losers,
        }
