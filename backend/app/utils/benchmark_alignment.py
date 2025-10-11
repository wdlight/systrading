"""
벤치마크 정렬 유틸리티 v2.3

벤치마크 데이터와 포트폴리오 타임라인을 정확하게 정렬합니다.
- 날짜 기반 정확한 매칭
- 선형 보간 (옵션)
- 데이터 누락 처리
"""

from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from loguru import logger


class BenchmarkAligner:
    """벤치마크 데이터 정렬 및 보간"""

    @staticmethod
    def align_by_date(
        benchmark_data: List[Dict[str, any]],  # [{"date": "YYYYMMDD", "value": float}, ...]
        target_dates: List[datetime],
        interpolate: bool = True,
        fill_method: str = "forward"
    ) -> List[float]:
        """
        날짜 기반 벤치마크 정렬

        Args:
            benchmark_data: 벤치마크 데이터 (날짜와 값)
            target_dates: 목표 날짜 리스트
            interpolate: 선형 보간 사용 여부
            fill_method: 누락 데이터 채우기 방법
                - "forward": 앞 값으로 채우기
                - "backward": 뒤 값으로 채우기
                - "nearest": 가장 가까운 값으로 채우기

        Returns:
            정렬된 벤치마크 값 리스트
        """
        if not benchmark_data:
            logger.warning("벤치마크 데이터 없음")
            return [0.0] * len(target_dates)

        # DataFrame 변환
        df = pd.DataFrame(benchmark_data)

        # 날짜를 datetime으로 변환
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        else:
            logger.error("벤치마크 데이터에 'date' 컬럼 없음")
            return [0.0] * len(target_dates)

        # 날짜를 인덱스로 설정
        df = df.set_index("date").sort_index()

        # 목표 날짜를 DataFrame으로
        target_df = pd.DataFrame({"date": target_dates})
        target_df = target_df.set_index("date")

        # 정렬 및 병합
        aligned = target_df.join(df, how="left")

        if interpolate:
            # 선형 보간
            aligned["value"] = aligned["value"].interpolate(
                method="linear",
                limit_direction="both"
            )
        else:
            # 단순 채우기
            if fill_method == "forward":
                aligned["value"] = aligned["value"].fillna(method="ffill")
            elif fill_method == "backward":
                aligned["value"] = aligned["value"].fillna(method="bfill")
            elif fill_method == "nearest":
                # 가장 가까운 값으로 채우기
                aligned["value"] = aligned["value"].interpolate(
                    method="nearest",
                    limit_direction="both"
                )

        # 여전히 NaN이 있으면 0으로 채우기
        aligned["value"] = aligned["value"].fillna(0.0)

        return aligned["value"].tolist()

    @staticmethod
    def align_simple(
        benchmark_values: List[float],
        target_length: int
    ) -> List[float]:
        """
        단순 정렬 (인덱스 기반 샘플링)

        Args:
            benchmark_values: 벤치마크 값 리스트
            target_length: 목표 길이

        Returns:
            샘플링된 벤치마크 값
        """
        if not benchmark_values:
            return [0.0] * target_length

        if len(benchmark_values) == target_length:
            return benchmark_values

        # 선형 보간
        x_original = np.linspace(0, 1, len(benchmark_values))
        x_target = np.linspace(0, 1, target_length)

        interpolated = np.interp(x_target, x_original, benchmark_values)

        return interpolated.tolist()

    @staticmethod
    def normalize_benchmark(
        benchmark_values: List[float],
        initial_portfolio_value: float
    ) -> List[float]:
        """
        벤치마크를 포트폴리오 초기 가치로 정규화

        Args:
            benchmark_values: 벤치마크 값 리스트
            initial_portfolio_value: 포트폴리오 초기 가치

        Returns:
            정규화된 벤치마크 값
        """
        if not benchmark_values or benchmark_values[0] == 0:
            return [initial_portfolio_value] * len(benchmark_values)

        base = benchmark_values[0]
        return [
            initial_portfolio_value * (v / base)
            for v in benchmark_values
        ]

    @staticmethod
    def calculate_tracking_error(
        portfolio_returns: List[float],
        benchmark_returns: List[float]
    ) -> float:
        """
        추적 오차 계산 (Tracking Error)

        Args:
            portfolio_returns: 포트폴리오 수익률 리스트
            benchmark_returns: 벤치마크 수익률 리스트

        Returns:
            추적 오차 (%)
        """
        if len(portfolio_returns) != len(benchmark_returns):
            logger.warning("포트폴리오와 벤치마크 길이 불일치")
            return 0.0

        diff = np.array(portfolio_returns) - np.array(benchmark_returns)
        return float(np.std(diff) * 100)

    @staticmethod
    def validate_alignment(
        portfolio_dates: List[datetime],
        benchmark_dates: List[str]  # YYYYMMDD
    ) -> Tuple[bool, List[str]]:
        """
        정렬 검증

        Args:
            portfolio_dates: 포트폴리오 날짜 리스트
            benchmark_dates: 벤치마크 날짜 리스트

        Returns:
            (유효성, 누락 날짜 리스트)
        """
        portfolio_dates_str = {d.strftime("%Y%m%d") for d in portfolio_dates}
        benchmark_dates_set = set(benchmark_dates)

        missing_dates = portfolio_dates_str - benchmark_dates_set

        is_valid = len(missing_dates) == 0

        return is_valid, sorted(list(missing_dates))


def create_aligned_dataframe(
    dates: List[datetime],
    portfolio_values: List[float],
    benchmark_values: List[float]
) -> pd.DataFrame:
    """
    정렬된 데이터프레임 생성 (분석용)

    Args:
        dates: 날짜 리스트
        portfolio_values: 포트폴리오 가치 리스트
        benchmark_values: 벤치마크 가치 리스트

    Returns:
        DataFrame with columns: date, portfolio, benchmark, portfolio_return, benchmark_return
    """
    df = pd.DataFrame({
        "date": dates,
        "portfolio": portfolio_values,
        "benchmark": benchmark_values
    })

    # 수익률 계산
    df["portfolio_return"] = df["portfolio"].pct_change() * 100
    df["benchmark_return"] = df["benchmark"].pct_change() * 100

    # 초과 수익률
    df["excess_return"] = df["portfolio_return"] - df["benchmark_return"]

    return df
