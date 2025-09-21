#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
단일 테스트 실행을 위한 스크립트
"""

import sys
import os
import subprocess

# Windows에서 UTF-8 출력 지원
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def main():
    # 현재 디렉토리를 프로젝트 루트로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 백엔드 디렉토리로 이동
    backend_dir = os.path.join(script_dir, 'backend')
    os.chdir(backend_dir)
    
    # Python 경로에 현재 디렉토리 추가
    sys.path.insert(0, backend_dir)
    sys.path.insert(0, script_dir)
    
    # TestRealAccountBalanceAPI 직접 실행
    try:
        # 절대 경로로 import
        tests_dir = os.path.join(backend_dir, 'tests')
        sys.path.insert(0, tests_dir)
        
        from test_real_account_integration import TestRealAccountBalanceAPI
        from fastapi.testclient import TestClient
        from simple_server import app
        
        print("테스트 TestRealAccountBalanceAPI 직접 실행")
        print("=" * 60)
        
        # 테스트 클래스 초기화
        test_instance = TestRealAccountBalanceAPI()
        
        # TestClient 생성
        client = TestClient(app)
        
        # KI 환경 설정
        ki_env_setup = test_instance.ki_env_setup()
        
        # API 가용성 확인
        real_api_available = test_instance.real_api_available(ki_env_setup)
        
        if real_api_available:
            print("\n✅ 실제 API 연결 확인됨")
            
            # 실제 테스트 실행
            print("\n🚀 test_real_account_balance_basic 실행 중...")
            test_instance.test_real_account_balance_basic(client, real_api_available)
            
            print("\n✅ 모든 테스트 완료!")
        else:
            print("\n❌ 실제 API 연결 실패")
            
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()