#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
직접 API 호출 테스트 스크립트
"""

import sys
import os
import json
import requests

# Windows에서 UTF-8 출력 지원
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def main():
    """직접 API 호출로 요청/응답 데이터 확인"""
    
    print("🔍 직접 API 호출 테스트")
    print("=" * 60)
    
    # 로컬 서버 URL (simple_server.py가 실행 중이어야 함)
    base_url = "http://localhost:8000"
    
    try:
        print(f"🚀 [REQUEST] GET {base_url}/api/account/balance")
        print("=" * 60)
        
        print("\n📤 [REQUEST INFO]")
        print("- URL: /api/account/balance")
        print("- Method: GET")
        print("- Headers: {'Content-Type': 'application/json'}")
        
        # API 호출
        response = requests.get(f"{base_url}/api/account/balance", 
                              headers={'Content-Type': 'application/json'})
        
        print(f"\n📥 [RESPONSE INFO]")
        print(f"- Status Code: {response.status_code}")
        print(f"- Headers: {dict(response.headers)}")
        print(f"- Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📋 [RESPONSE BODY - FULL JSON]")
            print(f"Raw JSON Response:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            
            print(f"\n🔬 [RESPONSE DATA ANALYSIS]")
            print(f"Response Keys: {list(data.keys())}")
            
            # 기본 정보 출력
            if 'total_value' in data:
                print(f"\n📊 [계좌 정보 요약]")
                print(f"총 자산: {data.get('total_value', 0):,}원")
                print(f"총 평가금액: {data.get('total_evaluation_amount', 0):,}원")
                print(f"총 손익: {data.get('total_profit_loss', 0):,}원")
                print(f"수익률: {data.get('total_profit_loss_rate', 0)}%")
                print(f"사용 가능 현금: {data.get('available_cash', 0):,}원")
                
                positions = data.get('positions', [])
                print(f"보유 종목 수: {len(positions)}개")
                
                print(f"\n📈 [보유 종목 상세 정보]")
                if len(positions) > 0:
                    for i, position in enumerate(positions):
                        print(f"[{i+1}] {json.dumps(position, ensure_ascii=False, indent=2)}")
                else:
                    print("보유 종목 없음")
            
        else:
            print(f"\n❌ API 호출 실패")
            print(f"Error Response: {response.text}")
            
        print(f"\n{'='*60}")
        print(f"✅ 직접 API 테스트 완료")
        print(f"{'='*60}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 연결 실패: {base_url}")
        print("simple_server.py가 실행 중인지 확인하세요.")
        print("backend 디렉토리에서 'python simple_server.py' 실행")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()