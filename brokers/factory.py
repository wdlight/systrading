# 브로커 팩토리 패턴
# 다양한 증권사 API를 통합 관리

from core.interfaces.broker_interface import BrokerInterface
from .korea_investment.ki_api import KoreaInvestAPI
from .korea_investment.ki_env import KoreaInvestEnv
# TODO: 향후 다른 브로커 추가 시 import

class BrokerFactory:
    """증권사 브로커 생성 팩토리"""
    
    SUPPORTED_BROKERS = {
        'korea_investment': 'KoreaInvestAPI',
        'ls_securities': 'LSSecuritiesAPI',  # TODO: 향후 구현
        # TODO: 다른 증권사 추가
    }
    
    @staticmethod
    def create_broker(broker_type: str, config: dict) -> BrokerInterface:
        """
        브로커 인스턴스 생성
        
        Args:
            broker_type: 브로커 타입 ('korea_investment', 'ls_securities' 등)
            config: 브로커 설정
            
        Returns:
            BrokerInterface: 브로커 인스턴스
            
        Raises:
            ValueError: 지원하지 않는 브로커 타입인 경우
        """
        if broker_type == 'korea_investment':
            env = KoreaInvestEnv(config)
            base_headers = env.get_base_headers()
            full_config = env.get_full_config()
            return KoreaInvestAPI(full_config, base_headers)
            
        elif broker_type == 'ls_securities':
            # TODO: LS증권 구현 후 활성화
            raise NotImplementedError("LS증권 API는 아직 구현되지 않았습니다")
            
        else:
            raise ValueError(f"지원하지 않는 브로커 타입: {broker_type}")
    
    @staticmethod
    def get_supported_brokers():
        """지원하는 브로커 목록 반환"""
        return list(BrokerFactory.SUPPORTED_BROKERS.keys())
    
    @staticmethod
    def is_broker_supported(broker_type: str) -> bool:
        """브로커 지원 여부 확인"""
        return broker_type in BrokerFactory.SUPPORTED_BROKERS