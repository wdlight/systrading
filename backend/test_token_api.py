#!/usr/bin/env python3
"""
한국투자증권 API 토큰 발급 테스트 스크립트
"""

import requests
import json
import yaml
import os

def test_token_api():
    print("=== 한국투자증권 API 토큰 발급 테스트 ===")

    # config.yaml 로드
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ {config_path} 파일이 없습니다.")
        return False

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 설정 값 확인
    api_key = config.get('KI_API_KEY')
    api_secret_key = config.get('KI_SECRET_KEY')
    using_url = config.get('KI_USING_URL', 'https://openapi.koreainvestment.com:9443')

    print(f"API Key: {api_key[:10]}...{api_key[-4:] if api_key and len(api_key) > 14 else api_key}")
    print(f"Secret Key: {api_secret_key[:10]}...{api_secret_key[-4:] if api_secret_key and len(api_secret_key) > 14 else api_secret_key}")
    print(f"URL: {using_url}")

    if not api_key or not api_secret_key:
        print("❌ API 키 또는 Secret 키가 설정되지 않았습니다.")
        return False

    # 토큰 발급 API 호출
    url = f"{using_url}/oauth2/tokenP"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "charset": "UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    data = {
        "grant_type": "client_credentials",
        "appkey": api_key,
        "appsecret": api_secret_key
    }

    print(f"\n요청 URL: {url}")
    print(f"요청 헤더: {json.dumps(headers, indent=2)}")
    print(f"요청 데이터: {json.dumps(data, indent=2)}")

    try:
        print("\n🔄 API 호출 중...")
        response = requests.post(url, headers=headers, json=data, timeout=30)

        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print(f"응답 내용: {response.text}")

        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            if access_token:
                print(f"✅ 토큰 발급 성공!")
                print(f"Access Token: {access_token[:20]}...")
                return True
            else:
                print(f"❌ 응답에 access_token이 없습니다. 응답: {result}")
                return False
        else:
            print(f"❌ API 호출 실패. 상태코드: {response.status_code}")
            if response.status_code == 403:
                print("🔍 403 에러 분석:")
                print("  - API 키/Secret 키가 유효하지 않을 수 있습니다")
                print("  - API 사용 권한이 없을 수 있습니다")
                print("  - 일일 API 호출 한도를 초과했을 수 있습니다")
                print("  - 한국투자증권 서버 이슈일 수 있습니다")
            return False

    except requests.exceptions.Timeout:
        print("❌ API 호출 타임아웃")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 네트워크 연결 오류")
        return False
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return False

if __name__ == "__main__":
    success = test_token_api()
    print(f"\n{'=' * 50}")
    print(f"테스트 결과: {'성공' if success else '실패'}")