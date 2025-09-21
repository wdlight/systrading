#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 계좌 API를 사용한 통합 테스트 실행 스크립트
"""

import sys
import os
import subprocess
import argparse
import yaml
from pathlib import Path

# Windows에서 UTF-8 출력 지원
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def check_config():
    """config.yaml 파일 및 설정 확인 (KoreaInvestEnv 활용)"""
    script_dir = Path(__file__).parent
    config_path = script_dir / 'config.yaml'
    
    print("🔍 실제 API 테스트 사전 조건 확인 중...")
    
    if not config_path.exists():
        print("❌ config.yaml 파일이 없습니다.")
        print("\n📋 다음 형식으로 backend/config.yaml 파일을 생성해주세요:")
        print("""
# 기본 필수 설정 (KoreaInvestEnv 호환)
KI_API_KEY: "your_api_key"
KI_SECRET_KEY: "your_secret_key"  
KI_ACCOUNT_NUMBER: "your_account_number"
KI_USING_URL: "https://openapi.koreainvestment.com:9443"
KI_IS_PAPER_TRADING: false  # true: 모의투자, false: 실계좌

# 선택사항 (KoreaInvestEnv가 자동 발급)
# KI_API_APPROVAL_KEY: "approval_key"  # 자동 발급됨
# KI_ACCOUNT_ACCESS_TOKEN: "access_token"  # 자동 발급됨
# KI_WEBSOCKET_APPROVAL_KEY: "websocket_key"  # 자동 발급됨

# 모의투자용 (KI_IS_PAPER_TRADING: true인 경우)
# KI_PAPER_API_KEY: "paper_api_key"  # 없으면 KI_API_KEY 사용
# KI_PAPER_SECRET_KEY: "paper_secret_key"  # 없으면 KI_SECRET_KEY 사용
        """)
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # KoreaInvestEnv에 필요한 최소 설정만 확인
        required_keys = ['KI_API_KEY', 'KI_SECRET_KEY', 'KI_ACCOUNT_NUMBER']
        missing_keys = [key for key in required_keys if not config.get(key)]
        
        if missing_keys:
            print(f"❌ 필수 설정이 누락되었습니다: {missing_keys}")
            print("\n💡 각 설정의 의미:")
            print("  - KI_API_KEY: 한국투자증권 API Key")
            print("  - KI_SECRET_KEY: 한국투자증권 Secret Key")
            print("  - KI_ACCOUNT_NUMBER: 계좌번호 (8자리)")
            print("\n🔧 KoreaInvestEnv가 자동으로 처리하는 것들:")
            print("  - KI_API_APPROVAL_KEY: 웹소켓 승인키 (자동 발급)")
            print("  - KI_ACCOUNT_ACCESS_TOKEN: 계좌 접근 토큰 (자동 발급)")
            print("  - 토큰 만료 관리 및 자동 재발급")
            return False
        
        # KoreaInvestEnv로 토큰 자동 발급 테스트
        print("🔧 KoreaInvestEnv를 사용한 토큰 발급 테스트...")
        
        try:
            # KoreaInvestEnv 설정 변환
            ki_config = {
                'api_key': config.get('KI_API_KEY'),
                'api_secret_key': config.get('KI_SECRET_KEY'), 
                'stock_account_number': config.get('KI_ACCOUNT_NUMBER'),
                'url': config.get('KI_USING_URL', 'https://openapi.koreainvestment.com:9443'),
                'paper_url': 'https://openapivts.koreainvestment.com:29443',
                'is_paper_trading': config.get('KI_IS_PAPER_TRADING', False),
                'custtype': 'P'
            }
            
            # 모의투자 설정
            if ki_config['is_paper_trading']:
                ki_config['paper_api_key'] = config.get('KI_PAPER_API_KEY', ki_config['api_key'])
                ki_config['paper_api_secret_key'] = config.get('KI_PAPER_SECRET_KEY', ki_config['api_secret_key'])
            
            # KoreaInvestEnv import 및 초기화
            sys.path.append(str(script_dir.parent))
            from brokers.korea_investment.ki_env import KoreaInvestEnv
            
            print("🚀 KoreaInvestEnv 초기화 중...")
            ki_env = KoreaInvestEnv(ki_config)
            
            # 토큰 발급 결과 확인
            base_headers = ki_env.get_base_headers()
            full_config = ki_env.get_full_config()
            
            print("✅ KoreaInvestEnv 초기화 성공!")
            print(f"📊 계좌번호: {ki_config['stock_account_number']}")
            print(f"🔑 API Key: {ki_config['api_key'][:10]}...")
            print(f"🌐 API URL: {ki_config.get('url' if not ki_config['is_paper_trading'] else 'paper_url')}")
            is_paper = ki_config['is_paper_trading']
            print(f"📝 투자 모드: {'모의투자' if is_paper else '실계좌'}")
            print(f"🔐 Access Token: {'✅ 발급됨' if base_headers.get('authorization') else '❌ 실패'}")
            print(f"🔌 WebSocket Key: {'✅ 발급됨' if full_config.get('websocket_approval_key') else '⚠️  없음 (계좌조회는 가능)'}")
            
            if not is_paper:
                print("\n⚠️  실계좌 모드입니다. 테스트는 조회만 하며 실제 거래는 하지 않습니다!")
            
            # Access Token이 없으면 실패
            if not base_headers.get('authorization'):
                print("❌ Access Token 발급 실패로 테스트를 실행할 수 없습니다.")
                return False
                
            return True
            
        except ImportError as e:
            print(f"❌ KoreaInvestEnv 모듈을 찾을 수 없습니다: {e}")
            print("💡 brokers/korea_investment/ki_env.py 파일이 있는지 확인해주세요.")
            return False
        except Exception as e:
            print(f"❌ KoreaInvestEnv 초기화 실패: {e}")
            print("💡 API Key와 Secret Key가 올바른지 확인해주세요.")
            return False
        
    except Exception as e:
        print(f"❌ config.yaml 파일 읽기 오류: {e}")
        return False

def run_real_tests(test_class=None, verbose=True):
    """실제 API 테스트 실행"""
    
    # 프로젝트 루트 디렉토리로 이동
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # pytest 실행 명령 구성
    cmd = ["python", "-m", "pytest", "tests/test_real_account_integration.py"]
    
    # 특정 테스트 클래스 지정
    if test_class:
        cmd.append(f"::{test_class}")
    
    # 통합 테스트만 실행
    cmd.extend(["-m", "integration"])
    
    if verbose:
        cmd.extend(["-v", "-s"])  # -s는 print 출력을 실시간으로 보여줌
    
    cmd.extend(["--tb=short", "--color=yes"])
    
    print(f"\n🚀 실행 명령: {' '.join(cmd)}")
    print("=" * 60)
    
    # 테스트 실행
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n❌ 테스트가 사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="실제 계좌 API를 사용한 통합 테스트 실행",
        epilog="""
사용 예시:
  python run_real_tests.py                           # 모든 실제 API 테스트 실행
  python run_real_tests.py --class TestRealAccountBalanceAPI  # 계좌 잔고 테스트만 실행
  python run_real_tests.py --check                   # 설정만 확인
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--class",
        dest="test_class",
        help="실행할 특정 테스트 클래스",
        choices=[
            "TestRealAccountBalanceAPI",
            "TestRealWatchlistAPI", 
            "TestRealTradingConditionsAPI",
            "TestRealMarketOverviewAPI"
        ]
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=True,
        help="상세 출력"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="설정만 확인하고 테스트는 실행하지 않음"
    )
    
    args = parser.parse_args()
    
    # 설정 확인
    if not check_config():
        print("\n❌ 실제 API 테스트를 실행할 수 없습니다.")
        print("위의 안내에 따라 설정을 완료한 후 다시 시도하세요.")
        sys.exit(1)
    
    # 설정만 확인하고 종료
    if args.check:
        print("\n✅ 설정 확인 완료!")
        return
    
    # 사용자 확인 (실계좌 모드인 경우)
    try:
        script_dir = Path(__file__).parent
        config_path = script_dir / 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config.get('KI_IS_PAPER_TRADING', False):
            print("\n⚠️  실계좌 모드에서 테스트를 실행하려고 합니다.")
            print("   실제 API 호출이 발생하지만, 매매 테스트는 포함되지 않습니다.")
            response = input("   계속하시겠습니까? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ 테스트가 취소되었습니다.")
                sys.exit(0)
    except:
        pass
    
    print(f"\n🚀 실제 API 테스트 시작")
    if args.test_class:
        print(f"📋 테스트 클래스: {args.test_class}")
    
    success = run_real_tests(
        test_class=args.test_class,
        verbose=args.verbose
    )
    
    if success:
        print("\n✅ 모든 실제 API 테스트가 성공했습니다!")
        sys.exit(0)
    else:
        print("\n❌ 일부 실제 API 테스트가 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()