#!/usr/bin/env python3
"""
연결 문제 진단 스크립트
각 단계별로 연결 상태와 로그를 확인
"""

import sys
import os
from loguru import logger
import json
from datetime import datetime

# 프로젝트 루트 경로 설정
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def check_config_yaml():
    """config.yaml 파일 확인"""
    print("=" * 60)
    print("1. config.yaml 파일 확인")
    print("=" * 60)
    
    config_path = os.path.join(project_root, 'config.yaml')
    
    if not os.path.exists(config_path):
        print("[FAIL] config.yaml 파일이 없습니다.")
        print(f"   경로: {config_path}")
        return None
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("[OK] config.yaml 로드 성공")
        print(f"   API Key: {config.get('api_key', 'None')[:20] if config.get('api_key') else 'None'}...")
        print(f"   Account Number: {config.get('stock_account_number', 'None')}")
        print(f"   Paper Trading: {config.get('is_paper_trading', 'None')}")
        print(f"   Using URL: {config.get('using_url', 'None')}")
        
        return config
        
    except Exception as e:
        print(f"[FAIL] config.yaml 로드 실패: {e}")
        return None

def check_access_token():
    """access.tok 파일 확인"""
    print("\n" + "=" * 60)
    print("2. access.tok 파일 확인")
    print("=" * 60)
    
    token_path = os.path.join(project_root, 'access.tok')
    
    if not os.path.exists(token_path):
        print("[FAIL] access.tok 파일이 없습니다.")
        print(f"   경로: {token_path}")
        return None
    
    try:
        with open(token_path, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        
        print("[OK] access.tok 로드 성공")
        print(f"   Timestamp: {token_data.get('timestamp', 'None')}")
        print(f"   WebSocket Key: {'Present' if token_data.get('websocket_approval_key') else 'None'}")
        print(f"   Access Token: {'Present' if token_data.get('account_access_token') else 'None'}")
        
        # 토큰 만료 확인
        timestamp = token_data.get('timestamp')
        if timestamp:
            token_time = datetime.fromisoformat(timestamp)
            now = datetime.now()
            hours_diff = (now - token_time).total_seconds() / 3600
            print(f"   토큰 생성 후 경과시간: {hours_diff:.1f}시간")
            if hours_diff > 12:
                print("   [WARNING]  토큰이 12시간 이상 경과했습니다. 갱신이 필요할 수 있습니다.")
            else:
                print("   [OK] 토큰이 유효한 시간 범위입니다.")
        
        return token_data
        
    except Exception as e:
        print(f"[FAIL] access.tok 로드 실패: {e}")
        return None

def check_ki_env():
    """KoreaInvestEnv 초기화 확인"""
    print("\n" + "=" * 60)
    print("3. KoreaInvestEnv 초기화 확인")
    print("=" * 60)
    
    try:
        from brokers.korea_investment.ki_env import KoreaInvestEnv
        print("[OK] KoreaInvestEnv import 성공")
        
        # config.yaml 로드
        config_path = os.path.join(project_root, 'config.yaml')
        if not os.path.exists(config_path):
            print("[FAIL] config.yaml이 없어서 KoreaInvestEnv 초기화 불가")
            return None
        
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # KoreaInvestEnv 초기화
        env = KoreaInvestEnv(config)
        print("[OK] KoreaInvestEnv 초기화 성공")
        
        # 헤더 확인
        base_headers = env.get_base_headers()
        print(f"   Authorization: {'Present' if base_headers.get('authorization') else 'None'}")
        print(f"   App Key: {'Present' if base_headers.get('appkey') else 'None'}")
        print(f"   App Secret: {'Present' if base_headers.get('appsecret') else 'None'}")
        
        # 전체 설정 확인
        full_config = env.get_full_config()
        print(f"   Using URL: {full_config.get('using_url', 'None')}")
        print(f"   WebSocket Key: {'Present' if full_config.get('websocket_approval_key') else 'None'}")
        
        return env
        
    except ImportError as e:
        print(f"[FAIL] KoreaInvestEnv import 실패: {e}")
        return None
    except Exception as e:
        print(f"[FAIL] KoreaInvestEnv 초기화 실패: {e}")
        return None

def check_ki_api():
    """KoreaInvestAPI 초기화 확인"""
    print("\n" + "=" * 60)
    print("4. KoreaInvestAPI 초기화 확인")
    print("=" * 60)
    
    try:
        from brokers.korea_investment.ki_api import KoreaInvestAPI
        from brokers.korea_investment.ki_env import KoreaInvestEnv
        print("[OK] KoreaInvestAPI import 성공")
        
        # config.yaml 로드
        config_path = os.path.join(project_root, 'config.yaml')
        if not os.path.exists(config_path):
            print("[FAIL] config.yaml이 없어서 KoreaInvestAPI 초기화 불가")
            return None
        
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 환경 설정 초기화
        env = KoreaInvestEnv(config)
        base_headers = env.get_base_headers()
        full_config = env.get_full_config()
        
        # API 인스턴스 생성
        api = KoreaInvestAPI(full_config, base_headers=base_headers)
        print("[OK] KoreaInvestAPI 초기화 성공")
        
        print(f"   Account Number: {api.stock_account_number}")
        print(f"   Paper Trading: {api.is_paper_trading}")
        print(f"   API URL: {api.stock_api_url}")
        
        return api
        
    except Exception as e:
        print(f"[FAIL] KoreaInvestAPI 초기화 실패: {e}")
        import traceback
        print(f"   스택 트레이스:\n{traceback.format_exc()}")
        return None

def test_account_balance_api(api):
    """계좌 잔고 API 테스트"""
    print("\n" + "=" * 60)
    print("5. 계좌 잔고 API 테스트")
    print("=" * 60)
    
    if not api:
        print("[FAIL] API 인스턴스가 없어서 테스트 불가")
        return None
    
    try:
        print("[WAIT] 계좌 잔고 조회 중...")
        result = api.get_acct_balance()
        
        if result and len(result) >= 2:
            total_value, df = result[0], result[1]
            print("[OK] 계좌 잔고 조회 성공")
            print(f"   총평가금액: {total_value:,}원")
            print(f"   보유종목 수: {len(df) if df is not None else 0}")
            
            if df is not None and not df.empty:
                print("\n   보유 종목 (최대 3개):")
                for i, (idx, row) in enumerate(df.head(3).iterrows()):
                    print(f"   - {row.get('종목명', 'N/A')}({row.get('종목코드', idx)}): "
                          f"{row.get('보유수량', 0)}주, {row.get('현재가', 0):,}원")
            
            return result
        else:
            print("[FAIL] 계좌 잔고 조회 실패 (빈 결과)")
            return None
            
    except Exception as e:
        print(f"[FAIL] 계좌 잔고 조회 실패: {e}")
        import traceback
        print(f"   스택 트레이스:\n{traceback.format_exc()}")
        return None

def check_backend_integration():
    """백엔드 통합 테스트"""
    print("\n" + "=" * 60)
    print("6. 백엔드 서비스 통합 테스트")
    print("=" * 60)
    
    try:
        # FastAPI 관련 모듈이 없을 수 있으므로 예외 처리
        try:
            sys.path.append(os.path.join(project_root, 'backend'))
            from app.core.config import get_settings
            from app.core.korea_invest import KoreaInvestAPIService
            
            print("[OK] 백엔드 모듈 import 성공")
            
            # 설정 로드
            settings = get_settings()
            print(f"   계좌번호: {settings.KI_ACCOUNT_NUMBER}")
            print(f"   모의투자: {settings.KI_IS_PAPER_TRADING}")
            
            # API 서비스 초기화
            korea_invest_service = KoreaInvestAPIService(settings)
            status = korea_invest_service.get_connection_status()
            print(f"   연결 상태: {status['connected']}")
            if status['last_error']:
                print(f"   마지막 에러: {status['last_error']}")
            
            return korea_invest_service
            
        except ImportError as e:
            print(f"[FAIL] 백엔드 모듈 import 실패: {e}")
            print("   FastAPI 관련 의존성이 설치되지 않았을 수 있습니다.")
            return None
            
    except Exception as e:
        print(f"[FAIL] 백엔드 통합 테스트 실패: {e}")
        import traceback
        print(f"   스택 트레이스:\n{traceback.format_exc()}")
        return None

def main():
    """메인 진단 함수"""
    print("주식 매매 시스템 연결 진단을 시작합니다...")
    print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"작업 디렉토리: {project_root}")
    
    # 1. config.yaml 확인
    config = check_config_yaml()
    
    # 2. access.tok 확인
    token_data = check_access_token()
    
    # 3. KoreaInvestEnv 확인
    env = check_ki_env()
    
    # 4. KoreaInvestAPI 확인
    api = check_ki_api()
    
    # 5. 계좌 잔고 API 테스트
    balance_result = test_account_balance_api(api)
    
    # 6. 백엔드 통합 테스트
    backend_service = check_backend_integration()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("진단 결과 요약")
    print("=" * 60)
    
    print(f"[OK] config.yaml: {'OK' if config else 'FAIL'}")
    print(f"[OK] access.tok: {'OK' if token_data else 'FAIL'}")
    print(f"[OK] KoreaInvestEnv: {'OK' if env else 'FAIL'}")
    print(f"[OK] KoreaInvestAPI: {'OK' if api else 'FAIL'}")
    print(f"[OK] 계좌 잔고 조회: {'OK' if balance_result else 'FAIL'}")
    print(f"[OK] 백엔드 통합: {'OK' if backend_service else 'FAIL'}")
    
    # 권장 사항
    print("\n[INFO] 권장 사항:")
    if not config:
        print("   1. config.yaml 파일을 생성하고 API 키를 설정하세요.")
    if not token_data:
        print("   2. access.tok 파일을 생성하거나 토큰을 갱신하세요.")
    if config and not api:
        print("   3. API 키 또는 계정 설정을 확인하세요.")
    if api and not balance_result:
        print("   4. 계좌번호 또는 API 권한을 확인하세요.")
    
    print(f"\n진단 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()