"""
일자별 분봉 API 상세 디버깅 테스트
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

def test_with_debug():
    """상세 디버깅 출력"""

    print("\n" + "="*80)
    print("📅 일자별 분봉 API 상세 디버깅 테스트")
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
    print(f"   날짜: {target_date}")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 직접 API 호출
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    url = '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice'
    tr_id = 'FHKST03010320'

    params = {
        'FID_COND_MRKT_DIV_CODE': 'J',
        'FID_INPUT_ISCD': stock_code,
        'FID_INPUT_DATE_1': target_date,
        'FID_INPUT_HOUR_1': '153000',  # 장 마감 시간으로 변경
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

        body = response.get_body()
        print(f"\n   body 타입: {type(body)}")

        if hasattr(body, 'rt_cd'):
            print(f"   rt_cd: {body.rt_cd}")
        if hasattr(body, 'msg_cd'):
            print(f"   msg_cd: {body.msg_cd}")
        if hasattr(body, 'msg1'):
            print(f"   msg1: {body.msg1}")

        if hasattr(body, 'output2'):
            print(f"\n   output2 존재: {body.output2 is not None}")
            if body.output2:
                print(f"   output2 길이: {len(body.output2)}")
                if len(body.output2) > 0:
                    print(f"\n   첫 번째 데이터:")
                    first_item = body.output2[0]
                    for key, value in first_item.items():
                        print(f"      {key}: {value}")

        # 전체 body 출력 (디버깅용)
        print(f"\n   전체 body 내용:")
        print(f"   {body}")

    print("\n" + "="*80)
    print("🏁 디버깅 테스트 완료")
    print("="*80)

if __name__ == "__main__":
    test_with_debug()
