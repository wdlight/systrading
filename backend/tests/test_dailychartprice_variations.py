"""
일자별 분봉 API 다양한 파라미터 조합 테스트
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from brokers.korea_investment.ki_env import KoreaInvestEnv
from brokers.korea_investment.ki_api import KoreaInvestAPI
from app.core.config import reload_settings

def test_variation(api, stock_code, target_date, variation_name, url, tr_id, params):
    """파라미터 조합 테스트"""
    print("\n" + "="*80)
    print(f"🧪 테스트: {variation_name}")
    print("="*80)
    print(f"URL: {url}")
    print(f"TR_ID: {tr_id}")
    print(f"Parameters: {params}")
    print("-"*80)

    response = api._url_fetch(url, tr_id, params)

    if response is None:
        print("❌ 응답 없음")
        return False

    if not response.is_ok():
        body = response.get_body()
        print(f"❌ 실패 - rt_cd: {body.rt_cd if hasattr(body, 'rt_cd') else 'N/A'}")
        print(f"   msg_cd: {body.msg_cd if hasattr(body, 'msg_cd') else 'N/A'}")
        print(f"   msg1: {body.msg1 if hasattr(body, 'msg1') else 'N/A'}")
        return False

    body = response.get_body()
    output2 = body.output2 if hasattr(body, 'output2') else []

    if not output2:
        print("⚠️ 데이터 없음")
        return False

    print(f"✅ 성공! 데이터 {len(output2)}개")
    if len(output2) > 0:
        print(f"   시간 범위: {output2[0].get('stck_cntg_hour')} ~ {output2[-1].get('stck_cntg_hour')}")
    return True


def main():
    print("\n" + "="*80)
    print("📅 일자별 분봉 API 다양한 조합 테스트")
    print("="*80)

    # 설정
    settings = reload_settings()
    config = settings.get_korea_invest_config()
    env = KoreaInvestEnv(config)
    api = KoreaInvestAPI(config, base_headers=env.get_base_headers())

    stock_code = "005930"
    target_date = "20251001"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조합 1: 사용자 제공 샘플 (14:00 종료)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    test_variation(
        api, stock_code, target_date,
        "조합 1: 사용자 샘플 (FHKST03010320, 14:00)",
        '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice',
        'FHKST03010320',
        {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': target_date,
            'FID_INPUT_HOUR_1': '140000',
            'FID_PW_DATA_INCU_YN': 'Y',
            'FID_FAKE_TICK_INCU_YN': 'N'
        }
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조합 2: 장 마감 시간 (15:30)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    test_variation(
        api, stock_code, target_date,
        "조합 2: 장 마감 시간 (FHKST03010320, 15:30)",
        '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice',
        'FHKST03010320',
        {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': target_date,
            'FID_INPUT_HOUR_1': '153000',
            'FID_PW_DATA_INCU_YN': 'Y',
            'FID_FAKE_TICK_INCU_YN': 'N'
        }
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조합 3: FID_ETC_CLS_CODE 추가
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    test_variation(
        api, stock_code, target_date,
        "조합 3: FID_ETC_CLS_CODE 추가 (FHKST03010320)",
        '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice',
        'FHKST03010320',
        {
            'FID_ETC_CLS_CODE': '',
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': target_date,
            'FID_INPUT_HOUR_1': '153000',
            'FID_PW_DATA_INCU_YN': 'Y',
            'FID_FAKE_TICK_INCU_YN': 'N'
        }
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조합 4: 모의투자용 TR_ID (V로 시작)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    test_variation(
        api, stock_code, target_date,
        "조합 4: 모의투자 TR_ID (VHKST03010320)",
        '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice',
        'VHKST03010320',
        {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': target_date,
            'FID_INPUT_HOUR_1': '140000',
            'FID_PW_DATA_INCU_YN': 'Y',
            'FID_FAKE_TICK_INCU_YN': 'N'
        }
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조합 5: 확인용 - 동작하는 API (오늘용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    success = test_variation(
        api, stock_code, target_date,
        "조합 5: 확인용 - 동작하는 API (FHKST03010230)",
        '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice',
        'FHKST03010230',
        {
            'FID_ETC_CLS_CODE': '',
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': target_date,
            'FID_INPUT_HOUR_1': '153000',
            'FID_PW_DATA_INCU_YN': 'Y',
            'FID_FAKE_TICK_INCU_YN': 'N'
        }
    )

    print("\n" + "="*80)
    print("🏁 테스트 완료")
    print("="*80)

if __name__ == "__main__":
    main()
