#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""해외 주요 지수 및 환율 조회 검증 테스트"""

import json
import os
import sys
from typing import Iterable, Tuple

import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.config import get_settings
from app.core.korea_invest import KoreaInvestAPIService


async def _attempt_overseas_fetch(
    service: KoreaInvestAPIService,
    label: str,
    candidates: Iterable[Tuple[str, str]],
):
    """후보 시장/지수 조합을 순회하며 첫 번째 유효 응답을 찾는다."""
    last_result = None

    for market_code, index_code in candidates:
        print(f"\n--- {label.upper()} 호출: market_code={market_code}, index_code={index_code} ---")
        result = await service.get_overseas_index_price(
            index_code=index_code,
            market_code=market_code,
        )

        raw = service.get_last_raw_response() or {}
        print("RAW 응답:")
        print(json.dumps(raw, ensure_ascii=False, indent=2))

        print("응답 객체:")
        print(result)

        if result is None:
            print(f"⚠️  결과가 None입니다. last_error={service.last_error}")
            continue

        result_dict = result.model_dump()
        print("직렬화된 응답:")
        print(json.dumps(result_dict, ensure_ascii=False, indent=2))

        last_result = result

        if result.current != 0.0 or result.change != 0.0 or result.change_rate != 0.0:
            break

    return last_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "label,candidates",
    [
        ("nasdaq", [("N", "NDX"), ("N", "IXIC")]),
        ("sp500", [("N", "US500"), ("N", "SPX")]),
        ("usd_krw", [("X", "FX@KRW")]),
    ],
)
async def test_overseas_index_query(label, candidates):
    settings = get_settings()
    service = KoreaInvestAPIService(settings)
    assert service.is_connected, "한국투자증권 API 서비스 초기화 실패"

    print(f"=== {label.upper()} 지수/환율 조회 테스트 ===")

    result = await _attempt_overseas_fetch(service, label, candidates)

    if result is None:
        pytest.fail(f"{label} 지수/환율 조회에 성공하지 못했습니다. 모든 응답이 None입니다.")

    if result.current == 0.0 and result.change == 0.0 and result.change_rate == 0.0:
        pytest.skip(
            f"{label} 응답이 모두 0입니다. 다른 코드나 WebSocket 경로를 확인하세요."
        )

    print(
        f"{label.upper()} 현재값: {result.current:.2f}, 전일 대비: {result.change:+.2f}, "
        f"등락률: {result.change_rate:+.2f}%"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
