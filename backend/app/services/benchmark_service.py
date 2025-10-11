"""
벤치마크(KOSPI) 데이터 서비스 v2.0

변경사항:
- KoreaInvestAPIService의 비동기 래퍼 메서드 사용
- _run_in_executor 패턴 적용
"""

import json
import asyncio
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from loguru import logger

from app.core.korea_invest import KoreaInvestAPIService


class BenchmarkService:
    """KOSPI 벤치마크 데이터 서비스"""

    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest = korea_invest_service
        self.cache_dir = Path("data/cache/benchmarks")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def get_kospi_history(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """KOSPI 지수 시계열 조회 (pykrx 사용)"""

        # 캐시 확인
        cache_key = f"kospi_df_{start_date:%Y%m%d}_{end_date:%Y%m%d}.json"
        cache_file = self.cache_dir / cache_key

        if cache_file.exists():
            logger.info(f"✅ DF 캐시 사용: {cache_key}")
            return pd.read_json(cache_file, orient='split')

        # pykrx를 사용하여 데이터 조회
        try:
            df = await self._fetch_from_pykrx(start_date, end_date)
            self._save_df_cache(cache_file, df)
            return df
        except Exception as e:
            logger.error(f"pykrx를 이용한 KOSPI 데이터 조회 실패: {e}")
            return pd.DataFrame() # 실패 시 빈 DF 반환



    async def _fetch_from_pykrx(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """pykrx로 KOSPI 조회"""
        try:
            from pykrx import stock

            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                stock.get_index_ohlcv,
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d"),
                "1001"  # KOSPI
            )

            if df is None or df.empty:
                raise ValueError("pykrx 데이터 없음")

            return df

        except ImportError:
            raise ValueError("pykrx 미설치. pip install pykrx")
        except Exception as e:
            raise ValueError(f"pykrx 실패: {e}")

    def _save_df_cache(self, cache_file: Path, data: pd.DataFrame):
        """DataFrame 캐시 저장"""
        try:
            data.to_json(cache_file, orient='split')
            logger.info(f"💾 DF 캐시 저장: {cache_file.name}")
        except Exception as e:
            logger.error(f"DF 캐시 저장 실패: {e}")

    def normalize_to_portfolio(
        self,
        benchmark_values: List[float],
        initial_portfolio_value: float
    ) -> List[float]:
        """벤치마크 정규화"""
        if not benchmark_values:
            return []

        if benchmark_values[0] == 0:
            return [initial_portfolio_value] * len(benchmark_values)

        base = benchmark_values[0]
        return [
            initial_portfolio_value * (v / base)
            for v in benchmark_values
        ]
