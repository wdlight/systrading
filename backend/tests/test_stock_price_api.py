#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국투자증권 API: 개별 종목 현재가 조회 테스트 (FHKST01010100)
API 호출의 가장 기본적인 기능 (인증, 개별 종목 조회)이 정상 동작하는지 확인합니다.

실행 방법:
1. backend 폴더에 유효한 config.yaml 파일이 있는지 확인합니다.
2. 프로젝트 루트 폴더에서 다음 명령어를 실행합니다:
   python backend/tests/test_stock_price_api.py
"""

import requests
import json
import yaml
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from brokers.korea_investment.ki_env import KoreaInvestEnv

def test_basic_stock_price_api():
    print("=== 한국투자증권 API 기본 기능 테스트 (개별 종목 현재가) ===")

    # 1. 설정 파일 로드
    try:
        config_path = os.path.join(project_root, "backend", "config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 설정 파일 로드 실패: {e}")
        return False

    # 2. KoreaInvestEnv 초기화
    print("🔄 KoreaInvestEnv 초기화 중...")
    try:
        env = KoreaInvestEnv(config)
    except Exception as e:
        print(f"❌ KoreaInvestEnv 초기화 실패: {e}")
        return False
    print("✅ KoreaInvestEnv 초기화 완료!")

    # 3. API 호출 준비 (삼성전자 현재가 조회)
    full_config = env.get_full_config()
    headers = env.get_base_headers()
    
    headers['tr_id'] = 'FHKST01010100' # 주식 현재가 시세
    
    url = f"{full_config['using_url']}/uapi/domestic-stock/v1/quotations/inquire-price"
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": "005930", # 삼성전자
    }

    print("\n🔄 삼성전자 현재가 API 호출 중...")
    print(f"요청 URL: {url}")
    print(f"요청 파라미터: {json.dumps(params, indent=2)}")

    # 4. API 호출 실행
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"\n응답 상태 코드: {response.status_code}")
        result = response.json()

        if response.status_code == 200 and result.get('rt_cd') == '0':
            print("✅ API 호출 성공!")
            print("--- 수신 데이터 (output) ---")
            print(json.dumps(result.get('output'), indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ API 호출 실패: {result.get('msg1')} (rt_cd: {result.get('rt_cd')})")
            print(f"전체 응답: {result}")
            return False

    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_stock_price_api()
    print(f"\n{'=' * 50}")
    print(f"테스트 결과: {'성공' if success else '실패'}")
