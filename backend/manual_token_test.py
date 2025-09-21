#!/usr/bin/env python3
"""
한국투자증권 API 토큰 수동 발급 테스트
EGW00002 오류 디버깅용
"""

import requests
import yaml
import json
from datetime import datetime

def load_config():
    """config.yaml 로드"""
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test_token_request():
    """토큰 발급 직접 테스트"""
    config = load_config()

    # API 키 정보
    api_key = config['api_key']
    api_secret = config['api_secret_key']
    base_url = config['url']

    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🔐 Secret Key: {api_secret[:30]}...")
    print(f"🌐 Base URL: {base_url}")

    # 토큰 발급 요청
    token_url = f"{base_url}/oauth2/tokenP"

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    data = {
        "grant_type": "client_credentials",
        "appkey": api_key,
        "appsecret": api_secret
    }

    print(f"\n📤 요청 URL: {token_url}")
    print(f"📤 요청 헤더: {headers}")
    print(f"📤 요청 데이터: {data}")

    try:
        print("\n🚀 토큰 발급 요청 시작...")
        response = requests.post(token_url, headers=headers, json=data, timeout=10)

        print(f"📨 응답 상태코드: {response.status_code}")
        print(f"📨 응답 헤더: {dict(response.headers)}")

        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ 토큰 발급 성공!")
            print(f"📊 응답 데이터: {json.dumps(token_data, indent=2, ensure_ascii=False)}")

            # 토큰 저장
            access_token = token_data.get('access_token')
            if access_token:
                save_data = {
                    "account_access_token": access_token,
                    "last_updated": datetime.now().isoformat()
                }

                with open('access_manual.tok', 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)

                print(f"💾 토큰 저장 완료: access_manual.tok")

        else:
            print(f"❌ 토큰 발급 실패!")
            print(f"📄 응답 내용: {response.text}")

            # 응답을 JSON으로 파싱 시도
            try:
                error_data = response.json()
                error_code = error_data.get('error_code', 'Unknown')
                error_desc = error_data.get('error_description', 'Unknown')

                print(f"🚨 오류 코드: {error_code}")
                print(f"🚨 오류 설명: {error_desc}")

                # EGW00002 전용 해결책
                if error_code == "EGW00002":
                    print(f"\n💡 EGW00002 해결 가이드:")
                    print(f"1. 한국투자증권 홈페이지 > KIS Developers > API 관리")
                    print(f"2. API 키 상태 확인 (활성화 여부)")
                    print(f"3. 서비스 신청 상태 확인 (승인 여부)")
                    print(f"4. 일일 API 호출 한도 확인")
                    print(f"5. 계정 상태 확인 (제재 여부)")

            except json.JSONDecodeError:
                print(f"📄 JSON 파싱 실패: {response.text}")

    except requests.RequestException as e:
        print(f"🌐 네트워크 오류: {e}")
    except Exception as e:
        print(f"🚨 예상치 못한 오류: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("한국투자증권 API 토큰 발급 테스트")
    print("=" * 60)
    test_token_request()