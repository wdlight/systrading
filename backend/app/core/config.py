"""
설정 관리
환경 변수와 설정값들을 관리
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # FastAPI 기본 설정
    APP_NAME: str = "Stock Trading API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 한국투자증권 API 설정
    KI_API_KEY: str = ""
    KI_SECRET_KEY: str = ""
    KI_ACCOUNT_NUMBER: str = ""
    KI_HTSID: str = "wdlight"
    KI_CUSTTYPE: str = "P"
    KI_IS_PAPER_TRADING: bool = False
    KI_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # 한국투자증권 URL 설정
    KI_API_URL: str = "https://openapi.koreainvestment.com:9443"
    KI_WEBSOCKET_URL: str = "ws://ops.koreainvestment.com:21000"
    KI_PAPER_URL: str = "https://openapivts.koreainventment.com:29443"
    KI_PAPER_WEBSOCKET_URL: str = "ws://ops.koreainvestment.com:31000"
    
    # 한국투자증권 토큰 설정
    KI_API_APPROVAL_KEY: str = ""
    KI_ACCESS_TOKEN: str = ""
    KI_WEBSOCKET_APPROVAL_KEY: str = ""
    KI_USING_URL: str = ""
    KI_ACCOUNT_ACCESS_TOKEN: str = ""
    
    # 데이터베이스 설정 (향후 확장용)
    DATABASE_URL: str = "sqlite:///./trading.db"
    
    # Redis 설정 (캐싱용)
    REDIS_URL: str = "redis://localhost:6379"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "trading_api.log"
    
    # WebSocket 설정
    WS_HEARTBEAT_INTERVAL: int = 30  # 초
    WS_MAX_CONNECTIONS: int = 100
    
    # 매매 설정
    DEFAULT_ORDER_AMOUNT: int = 100000  # 기본 매수 금액
    MAX_WATCHLIST_SIZE: int = 50        # 최대 워치리스트 크기
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def load_from_yaml(self, yaml_file_path: str = "config.yaml"):
        """기존 config.yaml에서 설정 로드"""
        import yaml
        import os
        
        if not os.path.exists(yaml_file_path):
            return
        
        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # yaml 설정을 환경 변수로 매핑
            if config:
                self.KI_API_KEY = config.get('api_key', self.KI_API_KEY)
                self.KI_SECRET_KEY = config.get('api_secret_key', self.KI_SECRET_KEY)
                self.KI_ACCOUNT_NUMBER = config.get('stock_account_number', self.KI_ACCOUNT_NUMBER)
                self.KI_HTSID = config.get('htsid', self.KI_HTSID)
                self.KI_CUSTTYPE = config.get('custtype', self.KI_CUSTTYPE)
                self.KI_IS_PAPER_TRADING = config.get('is_paper_trading', self.KI_IS_PAPER_TRADING)
                self.KI_USER_AGENT = config.get('my_agent', self.KI_USER_AGENT)
                
                self.KI_API_URL = config.get('url', self.KI_API_URL)
                self.KI_WEBSOCKET_URL = config.get('websocket_url', self.KI_WEBSOCKET_URL)
                self.KI_PAPER_URL = config.get('paper_url', self.KI_PAPER_URL)
                self.KI_PAPER_WEBSOCKET_URL = config.get('paper_websocket_url', self.KI_PAPER_WEBSOCKET_URL)
                
                # 토큰들은 config.yaml에서 로드하지 않음 (샘플 데이터이므로)
                # self.KI_API_APPROVAL_KEY = config.get('api_approval_key', self.KI_API_APPROVAL_KEY)
                # self.KI_ACCESS_TOKEN = config.get('access_tocken', self.KI_ACCESS_TOKEN)
                # self.KI_WEBSOCKET_APPROVAL_KEY = config.get('websocket_approval_key', self.KI_WEBSOCKET_APPROVAL_KEY)
                # self.KI_ACCOUNT_ACCESS_TOKEN = config.get('account_access_token', self.KI_ACCOUNT_ACCESS_TOKEN)
                
                # using_url만 config.yaml에서 로드
                self.KI_USING_URL = config.get('using_url', self.KI_USING_URL)
                
        except Exception as e:
            import logging
            logging.error(f"config.yaml 로드 실패: {e}")
    
    def initialize_with_env(self):
        """KoreaInvestEnv를 사용하여 토큰을 초기화하고 업데이트
        - access.tok 파일을 최우선으로 사용
        - 12시간마다 자동 갱신
        - config.yaml의 토큰은 무시 (샘플 데이터)
        """
        import sys
        import logging
        
        # 상위 디렉토리 경로 추가
        project_root = os.path.join(os.path.dirname(__file__), '../../..')
        sys.path.append(project_root)
        
        try:
            from brokers.korea_investment.ki_env import KoreaInvestEnv
            from brokers.korea_investment.token_manager import TokenManager
            
            logging.info("=== 백엔드 토큰 초기화 시작 ===")
            
            # TokenManager 초기화 (access.tok 파일 사용)
            token_manager = TokenManager("access.tok")
            
            # 12시간 기준으로 토큰 만료 확인
            token_expired = token_manager.is_token_expired(hours_threshold=12)
            logging.info(f"토큰 만료 여부 (12시간 기준): {token_expired}")
            
            # 기존 토큰 로드 시도
            token_data = None
            if not token_expired:
                token_data = token_manager.load_token_data()
                logging.info(f"access.tok에서 토큰 로드: {'성공' if token_data else '실패'}")
            
            # config 딕셔너리 생성 (API 키만, 토큰 제외)
            config = {
                'api_key': self.KI_API_KEY,
                'api_secret_key': self.KI_SECRET_KEY,
                'stock_account_number': self.KI_ACCOUNT_NUMBER,
                'htsid': self.KI_HTSID,
                'custtype': self.KI_CUSTTYPE,
                'is_paper_trading': self.KI_IS_PAPER_TRADING,
                'my_agent': self.KI_USER_AGENT,
                'url': self.KI_API_URL,
                'websocket_url': self.KI_WEBSOCKET_URL,
                'paper_url': self.KI_PAPER_URL,
                'paper_websocket_url': self.KI_PAPER_WEBSOCKET_URL,
            }
            
            # KoreaInvestEnv 초기화 (토큰 자동 관리, 12시간 갱신)
            logging.info("KoreaInvestEnv를 사용하여 토큰 관리 시작...")
            env = KoreaInvestEnv(config)
            
            # 업데이트된 설정을 가져와서 토큰 설정 업데이트
            full_config = env.get_full_config()
            
            # access.tok에서 실제 토큰 값들 설정
            if token_data:
                self.KI_WEBSOCKET_APPROVAL_KEY = token_data.get('websocket_approval_key', '')
                raw_token = token_data.get('account_access_token', '')
                self.KI_ACCOUNT_ACCESS_TOKEN = f"Bearer {raw_token}" if raw_token and not raw_token.startswith("Bearer ") else raw_token
                logging.info("access.tok의 토큰을 백엔드 설정에 적용")
            else:
                # 새로 발급받은 토큰 사용
                self.KI_WEBSOCKET_APPROVAL_KEY = full_config.get('websocket_approval_key', '')
                base_headers = env.get_base_headers()
                if 'authorization' in base_headers:
                    self.KI_ACCOUNT_ACCESS_TOKEN = base_headers['authorization']
                logging.info("새로 발급받은 토큰을 백엔드 설정에 적용")
            
            # URL 설정 업데이트
            self.KI_USING_URL = full_config.get('using_url', self.KI_USING_URL)
            self.KI_ACCOUNT_NUMBER = full_config.get('stock_account_number', self.KI_ACCOUNT_NUMBER)
            
            logging.info("=== 백엔드 토큰 초기화 완료 ===")
            logging.info(f"WebSocket Approval Key: {self.KI_WEBSOCKET_APPROVAL_KEY[:20] if self.KI_WEBSOCKET_APPROVAL_KEY else 'None'}...")
            logging.info(f"Account Access Token: {'Present' if self.KI_ACCOUNT_ACCESS_TOKEN else 'None'}")
            logging.info(f"Using URL: {self.KI_USING_URL}")
            
        except ImportError as e:
            logging.error(f"KoreaInvestEnv import 실패: {e}")
        except Exception as e:
            logging.error(f"KoreaInvestEnv 초기화 실패: {e}")
            import traceback
            logging.error(f"스택 트레이스:\n{traceback.format_exc()}")

# 전역 설정 인스턴스
_settings = None

def get_settings() -> Settings:
    """설정 인스턴스 반환 (싱글톤 패턴)"""
    global _settings
    if _settings is None:
        _settings = Settings()
        
        # 기존 config.yaml에서 설정 로드 시도
        config_path = os.path.join(os.path.dirname(__file__), '../../../config.yaml')
        if os.path.exists(config_path):
            _settings.load_from_yaml(config_path)
            
        # KoreaInvestEnv를 사용하여 토큰 관리
        _settings.initialize_with_env()
        
    return _settings

def reload_settings():
    """설정 재로드"""
    global _settings
    _settings = None
    return get_settings()