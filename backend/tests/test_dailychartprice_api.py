"""
한국투자증권 일자별 분봉 API 직접 테스트
API: /uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice
TR_ID: FHKST03010320

사용자 제공 샘플 파라미터:
FID_COND_MRKT_DIV_CODE:J
FID_INPUT_ISCD:005930
FID_INPUT_DATE_1:20251001
FID_INPUT_HOUR_1:140000
FID_PW_DATA_INCU_YN:Y
FID_FAKE_TICK_INCU_YN:N

실행: python tests/test_dailychartprice_api.py
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from brokers.korea_investment.ki_env import KoreaInvestEnv
from brokers.korea_investment.ki_api import KoreaInvestAPI
from app.core.config import reload_settings

def test_dailychartprice_api():
    """일자별 분봉 API 테스트 (사용자 제공 샘플)"""

    print("\n" + "="*80)
    print("📅 한국투자증권 일자별 분봉 API 테스트")
    print("   API: /uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice")
    print("   TR_ID: FHKST03010320")
    print("="*80 + "\n")

    # 설정 로드
    settings = reload_settings()
    config = settings.get_korea_invest_config()

    # KI API 초기화
    print("🔧 API 초기화 중...")
    env = KoreaInvestEnv(config)
    api = KoreaInvestAPI(config, base_headers=env.get_base_headers())

    # 테스트 파라미터 (사용자 제공 샘플)
    stock_code = "005930"
    target_date = "20251001"

    print(f"📊 테스트 파라미터")
    print(f"   종목: {stock_code} (삼성전자)")
    print(f"   날짜: {target_date}")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 직접 API 호출 (사용자 제공 샘플 파라미터 사용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    url = '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice'
    tr_id = 'FHKST03010320'

    # 사용자 제공 샘플 파라미터 그대로 사용
    params = {
        'FID_COND_MRKT_DIV_CODE': 'J',
        'FID_INPUT_ISCD': stock_code,
        'FID_INPUT_DATE_1': target_date,
        'FID_INPUT_HOUR_1': '140000',  # 사용자 샘플: 14:00:00
        'FID_PW_DATA_INCU_YN': 'Y',
        'FID_FAKE_TICK_INCU_YN': 'N'
    }

    print("🌐 API 호출 중...")
    print("-" * 80)
    print(f"URL: {url}")
    print(f"TR_ID: {tr_id}")
    print(f"Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print("-" * 80)
    print()

    # API 호출
    response = api._url_fetch(url, tr_id, params)

    # 결과 확인
    if response is None:
        print("❌ API 응답 없음")
        return False

    if not response.is_ok():
        body = response.get_body()
        print("❌ API 호출 실패")
        print(f"   rt_cd: {body.rt_cd if hasattr(body, 'rt_cd') else 'N/A'}")
        print(f"   msg_cd: {body.msg_cd if hasattr(body, 'msg_cd') else 'N/A'}")
        print(f"   msg1: {body.msg1 if hasattr(body, 'msg1') else 'N/A'}")
        return False

    # 성공
    body = response.get_body()
    output2 = body.output2 if hasattr(body, 'output2') else []

    if not output2:
        print("⚠️ 데이터 없음")
        return False

    print("✅ API 호출 성공!")
    print(f"   데이터 개수: {len(output2)}개")
    print()

    # 데이터 샘플 출력
    if len(output2) > 0:
        print("📋 응답 데이터 구조 (첫 번째 항목):")
        first_item = output2[0]
        for key, value in first_item.items():
            print(f"   {key}: {value}")
        print()

        print("📋 시간 범위:")
        print(f"   첫 시간: {output2[0].get('stck_cntg_hour', 'N/A')}")
        print(f"   마지막 시간: {output2[-1].get('stck_cntg_hour', 'N/A')}")
        print()

    print("=" * 80)
    print("🎉 일자별 분봉 API 테스트 성공!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_dailychartprice_api()
    sys.exit(0 if success else 1)
