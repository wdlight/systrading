#!/usr/bin/env python3
"""
계좌 서비스 통합 테스트
ki_api.py와 account_service.py 통합 테스트
"""

import asyncio
import sys
import os
import logging

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.core.config import get_settings
    from app.core.korea_invest import KoreaInvestAPIService
    from app.services.account_service import AccountService
except ImportError as e:
    print(f"모듈 임포트 실패: {e}")
    print("backend 디렉토리에서 실행해주세요.")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_account_integration():
    """계좌 서비스 통합 테스트"""
    try:
        print("=" * 60)
        print("계좌 서비스 통합 테스트 시작")
        print("=" * 60)
        
        # 1. 설정 로드
        print("\n1. 설정 로드 중...")
        settings = get_settings()
        print(f"   - 계좌번호: {settings.KI_ACCOUNT_NUMBER}")
        print(f"   - 모의투자: {settings.KI_IS_PAPER_TRADING}")
        
        # 2. 한국투자 API 서비스 초기화
        print("\n2. 한국투자 API 서비스 초기화...")
        korea_invest_service = KoreaInvestAPIService(settings)
        status = korea_invest_service.get_connection_status()
        print(f"   - 연결 상태: {status['connected']}")
        if status['last_error']:
            print(f"   - 에러: {status['last_error']}")
        
        # 3. 계좌 서비스 초기화
        print("\n3. 계좌 서비스 초기화...")
        account_service = AccountService(korea_invest_service)
        
        # 4. 원시 API 데이터 테스트
        print("\n4. 원시 API 데이터 조회...")
        raw_balance_data = await korea_invest_service.get_account_balance()
        
        if raw_balance_data:
            print("   ✅ 원시 API 데이터 조회 성공")
            print(f"   - 총평가금액: {raw_balance_data.get('total_value', 0):,}원")
            print(f"   - 총손익: {raw_balance_data.get('total_unrealized_pnl', 0):,}원")
            print(f"   - 가용현금: {raw_balance_data.get('available_cash', 0):,}원")
            print(f"   - 보유종목 수: {len(raw_balance_data.get('positions', []))}")
            
            # 보유 종목 상세 정보
            positions = raw_balance_data.get('positions', [])
            if positions:
                print("\n   보유 종목:")
                for pos in positions[:3]:  # 최대 3개까지만 표시
                    print(f"   - {pos['stock_name']}({pos['stock_code']}): "
                          f"{pos['quantity']}주, 평균단가 {pos['avg_price']:,}원, "
                          f"현재가 {pos['current_price']:,}원, "
                          f"손익 {pos['unrealized_pnl']:,}원 ({pos['profit_rate']:.2f}%)")
        else:
            print("   ❌ 원시 API 데이터 조회 실패")
            return
        
        # 5. 계좌 서비스를 통한 데이터 조회
        print("\n5. 계좌 서비스를 통한 데이터 조회...")
        try:
            account_balance = await account_service.get_balance()
            print("   ✅ 계좌 서비스 조회 성공")
            
            # 요약 정보
            summary = account_balance.summary
            print(f"   - 계좌번호: {summary.account_number}")
            print(f"   - 총자산: {summary.total_asset:,}원")
            print(f"   - 총평가: {summary.total_evaluation:,}원")
            print(f"   - 가용현금: {summary.available_cash:,}원")
            print(f"   - 총손익: {summary.total_profit_loss:,}원")
            print(f"   - 총수익률: {summary.total_profit_rate:.2f}%")
            
            # 포지션 정보
            positions = account_balance.positions
            print(f"   - 보유종목 수: {len(positions)}")
            
            if positions:
                print("\n   포지션 상세:")
                for pos in positions[:3]:  # 최대 3개까지만 표시
                    print(f"   - {pos.stock_name}({pos.stock_code}): "
                          f"{pos.quantity}주, 평균단가 {pos.avg_price:,}원, "
                          f"현재가 {pos.current_price:,}원, "
                          f"손익 {pos.unrealized_pnl:,}원 ({pos.profit_rate:.2f}%)")
            
        except Exception as e:
            print(f"   ❌ 계좌 서비스 조회 실패: {e}")
            logger.error(f"계좌 서비스 오류: {e}", exc_info=True)
        
        # 6. 연결 상태 확인
        print("\n6. 연결 상태 확인...")
        connection_status = await account_service.get_connection_status()
        print(f"   - 연결됨: {connection_status['connected']}")
        print(f"   - 마지막 업데이트: {connection_status['last_update']}")
        if connection_status['last_error']:
            print(f"   - 마지막 에러: {connection_status['last_error']}")
        
        print("\n" + "=" * 60)
        print("✅ 계좌 서비스 통합 테스트 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        logger.error(f"테스트 오류: {e}", exc_info=True)

async def test_error_handling():
    """오류 처리 테스트"""
    print("\n" + "=" * 60)
    print("오류 처리 테스트")
    print("=" * 60)
    
    try:
        # 잘못된 설정으로 서비스 생성
        print("\n1. 잘못된 설정 테스트...")
        
        # 빈 설정 객체 생성 (실제 구현에 따라 수정 필요)
        class EmptySettings:
            KI_API_KEY = ""
            KI_SECRET_KEY = ""
            KI_ACCOUNT_NUMBER = ""
            # ... 기타 필수 필드들
        
        empty_settings = EmptySettings()
        korea_invest_service = KoreaInvestAPIService(empty_settings)
        account_service = AccountService(korea_invest_service)
        
        # 빈 데이터로 조회 시도
        try:
            await account_service.get_balance()
            print("   ❌ 예상된 오류가 발생하지 않음")
        except Exception as e:
            print(f"   ✅ 예상된 오류 발생: {e}")
        
    except Exception as e:
        print(f"   오류 처리 테스트 중 예외: {e}")

if __name__ == "__main__":
    print("계좌 서비스 통합 테스트를 시작합니다...")
    
    # 메인 테스트 실행
    asyncio.run(test_account_integration())
    
    # 오류 처리 테스트 실행
    asyncio.run(test_error_handling())
    
    print("\n모든 테스트가 완료되었습니다.")