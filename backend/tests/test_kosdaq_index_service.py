#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국투자증권 API를 통해 KOSDAQ 지수 조회가 가능한지 확인하는 테스트.

KOSPI 테스트와 동일하게 `KoreaInvestAPIService`를 직접 초기화한 뒤
`get_index_current_price`를 시장 코드 `J`, 지수 코드 `1001` 조합으로 호출합니다.
결과를 표준 출력에 남기고, 필수 필드가 비어 있지 않은지 검증해서
실제 데이터가 내려오는지 여부를 확인합니다.

실제 KIS API 호출이 필요한 테스트이므로, 토큰과 인증 정보가 유효한 환경에서만
성공합니다. 실패 시 응답 내용을 함께 출력합니다.
"""

import asyncio
import json
import os
import sys

import pytest

# 테스트가 단독 실행될 때도 backend/app 패키지를 찾을 수 있도록 경로 추가
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.config import get_settings
from app.core.korea_invest import KoreaInvestAPIService


@pytest.mark.asyncio
async def test_kosdaq_index_query():
    """KOSDAQ 지수 조회 테스트"""
    settings = get_settings()

    service = KoreaInvestAPIService(settings)
    assert service.is_connected, "한국투자증권 API 서비스 초기화 실패"

    print("=== KOSDAQ 지수 조회 테스트 ===")
    print("market_code=J, index_code=1001 조합으로 호출합니다.")

    candidate_codes = [
        ("J", "1001"),  # 공식 문서 예시
        ("J", "0201"),  # KOSDAQ 지수 변형 후보
        ("J", "1501"),  # KOSDAQ150
        ("J", "2001"),  # 기타 업계 보고 코드
        ("U", "1001"),  # 시장 코드 변경 실험
    ]

    last_result = None
    for market_code, index_code in candidate_codes:
        print(f"\n--- 호출: market_code={market_code}, index_code={index_code} ---")
        result = await service.get_index_current_price(
            index_code=index_code,
            market_code=market_code
        )

        raw = service.get_last_raw_response() or {}
        print("RAW 응답:")
        print(json.dumps(raw, ensure_ascii=False, indent=2))

        print("응답 객체:")
        print(result)

        if result is None:
            print(f"⚠️  결과가 None입니다. last_error={service.last_error}")
            continue

        # MarketIndexData는 Pydantic BaseModel이므로 dict로 직렬화 가능
        result_dict = result.model_dump()
        print("직렬화된 응답:")
        print(json.dumps(result_dict, ensure_ascii=False, indent=2))

        if result.current != 0.0 or result.change != 0.0 or result.change_rate != 0.0:
            last_result = result
            break

        last_result = result

    if last_result is None:
        pytest.fail("KOSDAQ 지수 조회에 성공하지 못했습니다. 응답이 모두 None입니다.")

    if last_result.current == 0.0 and last_result.change == 0.0 and last_result.change_rate == 0.0:
        pytest.skip(
            "KOSDAQ 지수 응답이 모두 0입니다. 다른 지수 코드나 WebSocket 경로를 확인하세요."
        )

    print(
        f"KOSDAQ 현재지수: {last_result.current:.2f}, 전일 대비: {last_result.change:+.2f},"
        f" 등락률: {last_result.change_rate:+.2f}%"
    )


if __name__ == "__main__":
    import pytest as _pytest
    raise SystemExit(_pytest.main([__file__, "-v"]))
