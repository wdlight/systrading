"""
벤치마크(KOSPI) 데이터 서비스 v2.0

변경사항:
- KoreaInvestAPIService의 비동기 래퍼 메서드 사용
- _run_in_executor 패턴 적용
"""

import json
import asyncio
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
    ) -> List[float]:
        """KOSPI 지수 시계열 조회"""

        # 캐시 확인
        cache_key = f"kospi_{start_date:%Y%m%d}_{end_date:%Y%m%d}.json"
        cache_file = self.cache_dir / cache_key

        if cache_file.exists():
            logger.info(f"✅ 캐시 사용: {cache_key}")
            with open(cache_file) as f:
                return json.load(f)

        # Primary: 한투 API
        try:
            data = await self._fetch_from_kis_api(start_date, end_date)
            if data and len(data) > 0:
                self._save_cache(cache_file, data)
                return data
        except Exception as e:
            logger.warning(f"⚠️ 한투 API 실패: {e}")

        # Fallback: pykrx
        data = await self._fetch_from_pykrx(start_date, end_date)
        self._save_cache(cache_file, data)
        return data

    async def _fetch_from_kis_api(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[List[float]]:
        """
        한투 API로 KOSPI 조회

        ✅ v2.0: KoreaInvestAPIService의 비동기 래퍼 사용

        ⚠️ 구현 확인 필요:
        - get_index_chart_data() 메서드가 korea_invest.py에 존재하는지 확인
        - _run_in_executor로 동기 메서드를 래핑했는지 확인
        - Step 3에서 이 메서드를 추가하지 않았다면 먼저 구현 필요
        """
        try:
            # ✅ 비동기 래퍼 메서드 호출 (Step 3에서 추가 예정)
            df = await self.korea_invest.get_index_chart_data(
                market_code="U",
                index_code="0001",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                period_code="D"
            )

            if df is None or df.empty:
                return None

            # 종가 컬럼 찾기
            close_col = None
            for col in ["종가", "bstp_nmix_prpr", "close"]:
                if col in df.columns:
                    close_col = col
                    break

            if close_col is None:
                logger.error(f"종가 컬럼 없음: {df.columns.tolist()}")
                return None

            return df[close_col].astype(float).tolist()

        except Exception as e:
            logger.error(f"한투 API 오류: {e}")
            return None

    async def _fetch_from_pykrx(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[float]:
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

            return df["종가"].astype(float).tolist()

        except ImportError:
            raise ValueError("pykrx 미설치. pip install pykrx")
        except Exception as e:
            raise ValueError(f"pykrx 실패: {e}")

    def _save_cache(self, cache_file: Path, data: List[float]):
        """캐시 저장"""
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)
            logger.info(f"💾 캐시 저장: {cache_file.name}")
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")

    def normalize_to_portfolio(
        self,
        benchmark_values: List[float],
        initial_portfolio_value: float
    ) -> List[float]:
        """벤치마크 정규화"""
        if not benchmark_values or benchmark_values[0] == 0:
            return [initial_portfolio_value] * len(benchmark_values)

        base = benchmark_values[0]
        return [
            initial_portfolio_value * (v / base)
            for v in benchmark_values
        ]
