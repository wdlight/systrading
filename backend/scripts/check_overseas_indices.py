#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""해외 지수/환율 조회를 수동으로 검증하는 CLI 스크립트."""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, Iterable, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.config import get_settings
from app.core.korea_invest import KoreaInvestAPIService

CANDIDATE_MAP: Dict[str, Iterable[Tuple[str, str]]] = {
    "nasdaq": [("N", "NDX"), ("N", "IXIC")],
    "sp500": [("N", "US500"), ("N", "SPX")],
    "usd_krw": [("X", "FX@KRW")],
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="한국투자증권 해외 지수/환율 조회 도구")
    parser.add_argument(
        "--target",
        choices=list(CANDIDATE_MAP.keys()) + ["all"],
        default="all",
        help="조회할 대상 선택 (기본: all)",
    )
    parser.add_argument("--start-date", help="조회 시작일 (YYYYMMDD)")
    parser.add_argument("--end-date", help="조회 종료일 (YYYYMMDD)")
    parser.add_argument(
        "--period",
        default="D",
        help="기간 구분 코드 (D/W/M/Y, 기본: D)",
    )
    return parser.parse_args()


def _pretty_json(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


async def _fetch_single(
    service: KoreaInvestAPIService,
    label: str,
    candidates: Iterable[Tuple[str, str]],
    start_date: str | None,
    end_date: str | None,
    period_code: str,
) -> None:
    print(f"\n=== {label.upper()} 조회 ===")
    last_result = None

    for market_code, index_code in candidates:
        print(f"- 요청: market_code={market_code}, index_code={index_code}")
        result = await service.get_overseas_index_price(
            index_code=index_code,
            market_code=market_code,
            start_date=start_date,
            end_date=end_date,
            period_code=period_code,
        )

        raw = service.get_last_raw_response() or {}
        print("RAW 응답:")
        print(_pretty_json(raw))

        if result is None:
            print(f"⚠️  결과가 None입니다. last_error={service.last_error}")
            continue

        print("정규화된 응답:")
        print(_pretty_json(result.model_dump()))
        print(
            f"요약 → 현재:{result.current:.2f}, 전일대비:{result.change:+.2f}, 등락률:{result.change_rate:+.2f}%"
        )

        last_result = result
        if result.current != 0.0 or result.change != 0.0 or result.change_rate != 0.0:
            break

    if last_result is None:
        print("❌ 유효한 응답을 얻지 못했습니다.")
    elif last_result.current == 0.0 and last_result.change == 0.0 and last_result.change_rate == 0.0:
        print("❗ 응답이 모두 0입니다. 코드 조합이나 시장 상태를 확인하세요.")
    else:
        print("✅ 유효한 데이터를 수신했습니다.")


async def _async_main() -> None:
    args = _parse_args()

    settings = get_settings()
    service = KoreaInvestAPIService(settings)

    if not service.is_connected:
        print("API 서비스 초기화에 실패했습니다. 설정/토큰을 확인하세요.")
        sys.exit(1)

    targets = (
        CANDIDATE_MAP.keys()
        if args.target == "all"
        else [args.target]
    )

    for label in targets:
        await _fetch_single(
            service,
            label,
            CANDIDATE_MAP[label],
            start_date=args.start_date,
            end_date=args.end_date,
            period_code=args.period,
        )


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
