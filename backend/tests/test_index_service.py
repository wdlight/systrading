#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 통합 테스트: KoreaInvestAPIService를 통해 지수 조회가 정상 동작하는지 확인
"""

import pytest
import asyncio
import os
import sys
import json

# 프로젝트 루트 및 backend 폴더 경로 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)


# FastAPI의 의존성 주입 시스템을 사용하기 위해, FastAPI 앱 로딩이 필요할 수 있음
# 여기서는 서비스 클래스를 직접 초기화하여 테스트
from app.core.korea_invest import KoreaInvestAPIService
from app.core.config import get_settings

settings = get_settings()

@pytest.mark.asyncio
async def test_index_service_integration():
    print("=== 최종 통합 테스트: KoreaInvestAPIService.get_index_current_price ===")

    # 1. 서비스 초기화
    print("🔄 KoreaInvestAPIService 초기화 중...")
    try:
        # 설정 값을 사용하여 서비스 직접 초기화
        service = KoreaInvestAPIService(settings)
        assert service.is_connected, "API 서비스가 초기화되지 않았습니다."
    except Exception as e:
        pytest.fail(f"❌ 서비스 초기화 실패: {e}")
    print("✅ 서비스 초기화 완료!")

    # 2. KOSPI 지수 조회 서비스 메소드 호출
    print("\n🔄 service.get_index_current_price('U', '0001') 호출 중...")
    try:
        result = await service.get_index_current_price(market_code="U", index_code="0001")
        
        assert result is not None, "API 결과가 None입니다."
        
        print("✅ API 호출 성공!")
        print("--- 수신 데이터 ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 주요 필드 존재 여부 확인
        assert 'bstp_nmix_prpr' in result, "결과에 현재지수(bstp_nmix_prpr) 필드가 없습니다."

    except Exception as e:
        pytest.fail(f"❌ 서비스 메소드 호출 실패: {e}")

# 스크립트로 직접 실행 가능하도록 설정
if __name__ == "__main__":
    asyncio.run(test_index_service_integration())
