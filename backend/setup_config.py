#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KoreaInvestEnv 기반 config.yaml 설정 도우미
실제 API 키를 입력받아 자동으로 토큰을 발급하고 설정을 생성합니다.
"""

import sys
import os
import yaml
from pathlib import Path

# Windows에서 UTF-8 출력 지원
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def get_user_input():
    """사용자로부터 API 설정 정보를 입력받습니다"""
    print("🔧 한국투자증권 API 설정 도우미")
    print("=" * 50)
    
    config = {}
    
    # API 키 정보 입력
    print("\n📋 기본 API 정보를 입력해주세요:")
    config['KI_API_KEY'] = input("API Key: ").strip()
    config['KI_SECRET_KEY'] = input("Secret Key: ").strip()
    config['KI_ACCOUNT_NUMBER'] = input("계좌번호 (8자리): ").strip()
    
    # URL 설정
    default_url = "https://openapi.koreainvestment.com:9443"
    url_input = input(f"API URL ({default_url}): ").strip()
    config['KI_USING_URL'] = url_input if url_input else default_url
    
    # 모의투자 여부
    print("\n📝 투자 모드를 선택하세요:")
    print("  1. 실계좌 (실제 거래)")
    print("  2. 모의투자 (가상 거래)")
    
    mode_choice = input("선택 (1 또는 2): ").strip()
    is_paper = mode_choice == "2"
    config['KI_IS_PAPER_TRADING'] = is_paper
    
    if is_paper:
        print("\n🧪 모의투자용 API 키 (다르면 입력, 같으면 엔터):")
        paper_api_key = input("모의투자 API Key: ").strip()
        paper_secret_key = input("모의투자 Secret Key: ").strip()
        
        if paper_api_key:
            config['KI_PAPER_API_KEY'] = paper_api_key
        if paper_secret_key:
            config['KI_PAPER_SECRET_KEY'] = paper_secret_key
    
    # 입력 검증
    required_fields = ['KI_API_KEY', 'KI_SECRET_KEY', 'KI_ACCOUNT_NUMBER']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        print(f"\n❌ 필수 정보가 누락되었습니다: {missing_fields}")
        return None
    
    return config

def test_ki_env(config):
    """KoreaInvestEnv를 사용하여 토큰 발급 테스트"""
    print("\n🚀 KoreaInvestEnv를 사용한 토큰 발급 테스트...")
    
    try:
        # 현재 디렉토리를 프로젝트 루트에 추가
        script_dir = Path(__file__).parent
        sys.path.append(str(script_dir.parent))
        
        from brokers.korea_investment.ki_env import KoreaInvestEnv
        
        # KoreaInvestEnv 설정 변환
        ki_config = {
            'api_key': config['KI_API_KEY'],
            'api_secret_key': config['KI_SECRET_KEY'], 
            'stock_account_number': config['KI_ACCOUNT_NUMBER'],
            'url': config.get('KI_USING_URL', 'https://openapi.koreainvestment.com:9443'),
            'paper_url': 'https://openapivts.koreainvestment.com:29443',
            'is_paper_trading': config.get('KI_IS_PAPER_TRADING', False),
            'custtype': 'P'
        }
        
        # 모의투자 설정
        if ki_config['is_paper_trading']:
            ki_config['paper_api_key'] = config.get('KI_PAPER_API_KEY', ki_config['api_key'])
            ki_config['paper_api_secret_key'] = config.get('KI_PAPER_SECRET_KEY', ki_config['api_secret_key'])
        
        print("📡 API 서버 연결 및 토큰 발급 중...")
        
        # KoreaInvestEnv 초기화 (토큰 자동 발급)
        ki_env = KoreaInvestEnv(ki_config)
        
        # 발급 결과 확인
        base_headers = ki_env.get_base_headers()
        full_config = ki_env.get_full_config()
        
        access_token = base_headers.get('authorization')
        websocket_key = full_config.get('websocket_approval_key')
        
        print("✅ 토큰 발급 성공!")
        print(f"🔐 Access Token: {'✅ 발급됨' if access_token else '❌ 실패'}")
        print(f"🔌 WebSocket Key: {'✅ 발급됨' if websocket_key else '⚠️  없음 (계좌조회는 가능)'}")
        
        if access_token:
            # 발급받은 토큰들을 config에 추가 (선택사항)
            raw_token = access_token.replace("Bearer ", "") if access_token.startswith("Bearer ") else access_token
            config['KI_ACCOUNT_ACCESS_TOKEN'] = raw_token
            
            if websocket_key:
                config['KI_WEBSOCKET_APPROVAL_KEY'] = websocket_key
            
            return True
        else:
            print("❌ Access Token 발급 실패")
            return False
            
    except ImportError as e:
        print(f"❌ KoreaInvestEnv 모듈을 찾을 수 없습니다: {e}")
        print("💡 brokers/korea_investment/ki_env.py 파일이 있는지 확인해주세요.")
        return False
    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        print("💡 API Key와 Secret Key가 올바른지 확인해주세요.")
        return False

def save_config(config):
    """설정을 config.yaml 파일로 저장"""
    script_dir = Path(__file__).parent
    config_path = script_dir / 'config.yaml'
    
    # 기존 파일이 있으면 백업
    if config_path.exists():
        backup_path = config_path.with_suffix('.yaml.backup')
        config_path.replace(backup_path)
        print(f"📄 기존 설정을 백업했습니다: {backup_path}")
    
    # 설정 파일 생성
    config_content = f"""# 한국투자증권 API 설정 (KoreaInvestEnv 호환)
# 생성일시: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# 기본 필수 설정
KI_API_KEY: "{config['KI_API_KEY']}"
KI_SECRET_KEY: "{config['KI_SECRET_KEY']}"
KI_ACCOUNT_NUMBER: "{config['KI_ACCOUNT_NUMBER']}"
KI_USING_URL: "{config.get('KI_USING_URL', 'https://openapi.koreainvestment.com:9443')}"
KI_IS_PAPER_TRADING: {str(config.get('KI_IS_PAPER_TRADING', False)).lower()}

# 자동 발급된 토큰들 (KoreaInvestEnv가 관리)
"""
    
    # 발급된 토큰이 있으면 추가
    if config.get('KI_ACCOUNT_ACCESS_TOKEN'):
        config_content += f'KI_ACCOUNT_ACCESS_TOKEN: "{config["KI_ACCOUNT_ACCESS_TOKEN"]}"\n'
    else:
        config_content += f'# KI_ACCOUNT_ACCESS_TOKEN: "자동 발급됨"\n'
        
    if config.get('KI_WEBSOCKET_APPROVAL_KEY'):
        config_content += f'KI_WEBSOCKET_APPROVAL_KEY: "{config["KI_WEBSOCKET_APPROVAL_KEY"]}"\n'
    else:
        config_content += f'# KI_WEBSOCKET_APPROVAL_KEY: "자동 발급됨"\n'
    
    # 모의투자 설정이 있으면 추가
    if config.get('KI_PAPER_API_KEY'):
        config_content += f'\n# 모의투자용 설정\n'
        config_content += f'KI_PAPER_API_KEY: "{config["KI_PAPER_API_KEY"]}"\n'
    
    if config.get('KI_PAPER_SECRET_KEY'):
        config_content += f'KI_PAPER_SECRET_KEY: "{config["KI_PAPER_SECRET_KEY"]}"\n'
    
    config_content += f"""
# 추가 설정 (선택사항)
# USER_AGENT: "Custom User Agent"

# 주의사항:
# - 이 파일은 민감한 정보를 포함하고 있습니다
# - Git에 커밋하지 마세요 (.gitignore에 추가 권장)
# - KoreaInvestEnv가 토큰 만료를 자동으로 관리합니다
"""
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ 설정 파일이 생성되었습니다: {config_path}")
        print(f"📁 파일 크기: {config_path.stat().st_size} bytes")
        return True
        
    except Exception as e:
        print(f"❌ 설정 파일 저장 실패: {e}")
        return False

def show_next_steps():
    """다음 단계 안내"""
    print("\n🎉 설정이 완료되었습니다!")
    print("=" * 50)
    print("\n📋 다음 단계:")
    print("1. 실제 API 테스트 실행:")
    print("   python run_real_tests.py --check")
    print("\n2. 특정 테스트 실행:")
    print("   python run_real_tests.py --class TestRealAccountBalanceAPI")
    print("\n3. 모든 테스트 실행:")
    print("   python run_real_tests.py")
    print("\n🔒 보안 주의사항:")
    print("- config.yaml 파일을 Git에 커밋하지 마세요")
    print("- API 키는 안전한 곳에 보관하세요")
    print("- 주기적으로 API 키를 재발급하세요")

def main():
    """메인 함수"""
    print("🚀 한국투자증권 API 설정 도우미를 시작합니다")
    print("이 도구는 KoreaInvestEnv를 사용하여 토큰을 자동으로 발급받습니다.")
    print()
    
    # 사용자 입력
    config = get_user_input()
    if not config:
        print("❌ 설정이 취소되었습니다.")
        return
    
    print("\n📊 입력된 설정:")
    print(f"계좌번호: {config['KI_ACCOUNT_NUMBER']}")
    print(f"API Key: {config['KI_API_KEY'][:10]}...")
    print(f"URL: {config['KI_USING_URL']}")
    print(f"투자 모드: {'모의투자' if config['KI_IS_PAPER_TRADING'] else '실계좌'}")
    
    confirm = input("\n이 설정으로 진행하시겠습니까? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 설정이 취소되었습니다.")
        return
    
    # KoreaInvestEnv 테스트
    if not test_ki_env(config):
        print("❌ 토큰 발급 테스트 실패")
        retry = input("설정 파일만 생성하시겠습니까? (y/N): ").strip().lower()
        if retry not in ['y', 'yes']:
            return
    
    # 설정 파일 저장
    if save_config(config):
        show_next_steps()
    else:
        print("❌ 설정 파일 생성 실패")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()