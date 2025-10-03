"""
동작하는 API(FHKST03010230)로 과거 데이터 조회 테스트
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

def test_today_api_with_past_date():
    """오늘용 API로 과거 날짜 조회 시도"""

    print("\n" + "="*80)
    print("📅 오늘용 API(FHKST03010230)로 과거 날짜 조회 테스트")
    print("="*80 + "\n")

    # 설정 로드
    settings = reload_settings()
    config = settings.get_korea_invest_config()

    # KI API 초기화
    print("🔧 API 초기화 중...")
    env = KoreaInvestEnv(config)
    api = KoreaInvestAPI(config, base_headers=env.get_base_headers())

    stock_code = "005930"
    target_date = "20251001"

    print(f"📊 테스트 파라미터")
    print(f"   종목: {stock_code} (삼성전자)")
    print(f"   날짜: {target_date} (과거 날짜)")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 오늘용 API로 과거 날짜 조회
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    url = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
    tr_id = 'FHKST03010230'

    params = {
        'FID_ETC_CLS_CODE': '',
        'FID_COND_MRKT_DIV_CODE': 'J',
        'FID_INPUT_ISCD': stock_code,
        'FID_INPUT_DATE_1': target_date,  # 과거 날짜
        'FID_INPUT_HOUR_1': '153000',
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

    # 결과 상세 출력
    print("📋 응답 상세:")
    print(f"   response is None: {response is None}")

    if response is not None:
        print(f"   response.is_ok(): {response.is_ok()}")

        if response.is_ok():
            body = response.get_body()

            if hasattr(body, 'output2'):
                output2 = body.output2
                print(f"   ✅ 데이터 조회 성공!")
                print(f"   output2 길이: {len(output2)}")

                if len(output2) > 0:
                    print(f"\n   시간 범위:")
                    print(f"      첫 시간: {output2[0].get('stck_cntg_hour', 'N/A')}")
                    print(f"      마지막 시간: {output2[-1].get('stck_cntg_hour', 'N/A')}")

                    print(f"\n   첫 번째 데이터:")
                    first_item = output2[0]
                    for key, value in first_item.items():
                        print(f"      {key}: {value}")
        else:
            body = response.get_body()
            print(f"   ❌ API 호출 실패")
            if hasattr(body, 'rt_cd'):
                print(f"      rt_cd: {body.rt_cd}")
            if hasattr(body, 'msg_cd'):
                print(f"      msg_cd: {body.msg_cd}")
            if hasattr(body, 'msg1'):
                print(f"      msg1: {body.msg1}")

    print("\n" + "="*80)
    print("🏁 테스트 완료")
    print("="*80)

if __name__ == "__main__":
    test_today_api_with_past_date()
