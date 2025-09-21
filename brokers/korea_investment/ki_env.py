# 한국투자증권 환경 설정 관리자
# utils.py에서 이동된 KoreaInvestEnv 클래스

import copy
import json
import requests
from loguru import logger
from .token_manager import TokenManager

class KoreaInvestEnv:
    def __init__(self, config):
        self.config = config
        self.custtype = config.get('custtype', 'P')
        self.token_manager = TokenManager()
        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "charset": "utf-8",
            "User-Agent": config.get('my_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            
        } 
  
        self.url = config.get('url', 'https://openapi.koreainvestment.com:9443')
        self.paper_url = config.get('paper_url', 'https://openapivts.koreainvestment.com:29443')

        # 실제 거래 환경인지 판단
        is_paper_trading = config.get('is_paper_trading', False)
        
        api_secret_key = ''
        if is_paper_trading:
            using_url = self.paper_url  
            api_key = config.get('paper_api_key')
            api_secret_key = config.get('paper_api_secret_key')
            stock_account_number = config.get('stock_account_number')
        else:
            using_url = self.url
            api_key = config.get('api_key')
            api_secret_key = config.get('api_secret_key')
            stock_account_number = config.get('stock_account_number')
        
        # 토큰 파일 만료 여부 확인 및 토큰 획득
        websocket_approval_key = None
        account_access_token = None
        
        # 먼저 토큰 만료 여부 확인
        token_expired = self.token_manager.is_token_expired()
        logger.info(f"토큰 만료 여부: {token_expired}")
        
        if not token_expired:
            # 토큰이 유효하면 기존 토큰 로드 시도
            websocket_approval_key, account_access_token = self._load_existing_tokens()
            
            # 기존 토큰 로드 실패 시에도 새로 발급
            if not websocket_approval_key or not account_access_token:
                logger.warning("토큰이 유효하지만 로드 실패. 새로 발급")
                token_expired = True
        
        # 토큰이 만료되었거나 로드 실패 시 새로 발급
        if token_expired or not websocket_approval_key or not account_access_token:
            logger.info("새로운 토큰 발급 진행")
            websocket_approval_key, account_access_token = self._fetch_new_tokens(using_url, api_key, api_secret_key)
        self.base_headers["authorization"] = account_access_token
        self.base_headers["appkey"] = api_key
        self.base_headers["appsecret"] = api_secret_key
        self.config["websocket_approval_key"] = websocket_approval_key       
        self.config["stock_account_number"] = stock_account_number
        self.config["using_url"] = using_url

    
    def get_base_headers(self):
        return copy.deepcopy(self.base_headers) 
    
    def get_full_config(self):
        return self.config

    def _fetch_new_tokens(self, using_url, api_key, api_secret_key):
        """새로운 토큰들을 발급받아 저장하는 함수"""
        logger.info("새로운 토큰 발급 시작")
        
        # 먼저 account_access_token 발급
        account_access_token = self.get_account_access_token(using_url, api_key, api_secret_key)
        
        # account_access_token을 이용해 websocket_approval_key 발급  
        websocket_approval_key = self.get_websocket_approval_key_with_token(using_url, api_key, api_secret_key, account_access_token)
        
        if websocket_approval_key and account_access_token:
            # Bearer 제거하고 저장
            raw_token = account_access_token.replace("Bearer ", "") if isinstance(account_access_token, str) else account_access_token
            token_data = {
                'websocket_approval_key': websocket_approval_key,
                'account_access_token': raw_token
            }
            
            if self.token_manager.save_token_data(token_data):
                logger.info("새로운 토큰 데이터 저장 완료")
                return websocket_approval_key, account_access_token
        
        logger.error("토큰 발급 또는 저장 실패")
        return None, None

    def _load_existing_tokens(self):
        """기존 토큰 파일에서 토큰들을 로드하는 함수"""
        logger.info("기존 토큰 파일 사용")
        token_data = self.token_manager.load_token_data()
        
        if token_data:
            websocket_approval_key = token_data.get('websocket_approval_key')
            raw_token = token_data.get('account_access_token')
            account_access_token = f"Bearer {raw_token}" if raw_token and not raw_token.startswith("Bearer ") else raw_token
            
            # websocket_approval_key가 없으면 새로 발급
            if not websocket_approval_key and account_access_token:
                logger.info("websocket_approval_key가 없어서 새로 발급")
                api_key = self.config.get('api_key')
                api_secret_key = self.config.get('api_secret_key')
                using_url = self.config.get('url', 'https://openapi.koreainvestment.com:9443')
                
                if self.config.get('is_paper_trading', False):
                    using_url = self.config.get('paper_url', 'https://openapivts.koreainvestment.com:29443')
                    api_key = self.config.get('paper_api_key')
                    api_secret_key = self.config.get('paper_api_secret_key')
                
                websocket_approval_key = self.get_websocket_approval_key_with_token(using_url, api_key, api_secret_key, account_access_token)
                
                # 새로 발급받은 키를 토큰 파일에 저장
                if websocket_approval_key:
                    token_data['websocket_approval_key'] = websocket_approval_key
                    self.token_manager.save_token_data(token_data)
                    logger.info("새로 발급받은 websocket_approval_key 저장 완료")
            
            return websocket_approval_key, account_access_token
        
        return None, None

    def get_account_access_token(self, request_base_url , api_key, api_secret_key):
        """계좌 접근 토큰 발급"""
        try:
            url = f"{request_base_url}/oauth2/tokenP"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "charset": "UTF-8",
                "User-Agent": self.config.get('my_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            }
            data = {
                "grant_type": "client_credentials",
                "appkey": api_key,
                "appsecret": api_secret_key,
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                print ( "Success Access Token : "+ response.json()['access_token'] )                
                return f"Bearer {response.json()['access_token']}"
            else:
                logger.error(f"계좌 접근 토큰 발급 실패: {response.status_code} {response.text}")
                return None
        except Exception as e:
            logger.error(f"계좌 접근 토큰 발급 오류: {e}")
            return None

    def get_websocket_approval_key(self, url, api_key, api_secret_key):
        """웹소켓 승인키 발급 - access_token을 이용해 별도 발급"""
        logger.info("=== 웹소켓 승인키 발급 시작 ===")
        logger.info(f"요청 URL: {url}")
        logger.info(f"API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
        logger.info(f"API Secret Key: {api_secret_key[:10]}...{api_secret_key[-4:] if len(api_secret_key) > 14 else api_secret_key}")
        
        try:
            # 먼저 access_token 발급
            logger.info("1단계: Access Token 발급 중...")
            access_token = self.get_account_access_token(url, api_key, api_secret_key)
            if not access_token:
                logger.error("Access token 발급 실패로 웹소켓 승인키 발급 불가")
                return None
            
            logger.info(f"Access token 발급 성공: {access_token[:20]}...")
            
            # Bearer 제거
            raw_token = access_token.replace("Bearer ", "") if access_token.startswith("Bearer ") else access_token
            logger.info(f"Raw token: {raw_token[:20]}...")
            
            # 웹소켓 승인키 발급 요청
            approval_url = f"{url}/oauth2/Approval"
            logger.info(f"2단계: 웹소켓 승인키 요청 URL: {approval_url}")
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "charset": "utf-8",
                "User-Agent": self.config.get('my_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
                "authorization": f"Bearer {raw_token}",
                "appkey": api_key,
                "appsecret": api_secret_key,
            }
            data = {
                "grant_type": "client_credentials",
                "appkey": api_key,
                "secretkey": api_secret_key,
            }
            
            logger.info(f"요청 헤더: {headers}")
            logger.info(f"요청 데이터: {data}")
            
            logger.info("웹소켓 승인키 요청 전송 중...")
            response = requests.post(approval_url, headers=headers, json=data)
            
            logger.info(f"응답 상태 코드: {response.status_code}")
            logger.info(f"응답 헤더: {dict(response.headers)}")
            logger.info(f"응답 내용: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"JSON 응답: {result}")
                
                approval_key = result.get("approval_key")
                if approval_key:
                    logger.info(f"웹소켓 승인키 발급 성공: {approval_key[:20]}...")
                    logger.info("=== 웹소켓 승인키 발급 완료 ===")
                    return approval_key
                else:
                    logger.error(f"응답에 approval_key가 없음. 응답 키들: {list(result.keys())}")
                    return None
            else:
                logger.error(f"웹소켓 승인키 발급 실패 - 상태코드: {response.status_code}")
                logger.error(f"에러 응답: {response.text}")
                logger.error(f"요청 URL: {approval_url}")
                logger.error(f"요청 헤더: {headers}")
                logger.error(f"요청 데이터: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"네트워크 요청 오류: {e}")
            logger.error(f"요청 URL: {approval_url}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            logger.error(f"응답 내용: {response.text}")
            return None
        except Exception as e:
            logger.error(f"웹소켓 승인키 발급 예외 오류: {e}")
            logger.error(f"오류 타입: {type(e).__name__}")
            import traceback
            logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
            return None 

    def get_websocket_approval_key_with_token(self, url, api_key, api_secret_key, access_token):
        """기존 access_token을 이용해 웹소켓 승인키만 발급"""
        logger.info("=== 기존 토큰을 이용한 웹소켓 승인키 발급 시작 ===")
        
        if not access_token:
            logger.error("Access token이 None입니다")
            return None
            
        try:
            # Bearer 제거
            raw_token = access_token.replace("Bearer ", "") if access_token.startswith("Bearer ") else access_token
            logger.info(f"기존 토큰 사용: {raw_token[:20]}...")
            
            # 웹소켓 승인키 발급 요청
            approval_url = f"{url}/oauth2/Approval"
            logger.info(f"웹소켓 승인키 요청 URL: {approval_url}")
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "charset": "utf-8",
                "User-Agent": self.config.get('my_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
                "authorization": f"Bearer {raw_token}",
                "appkey": api_key,
                "appsecret": api_secret_key,
            }
            data = {
                "grant_type": "client_credentials",
                "appkey": api_key,
                "secretkey": api_secret_key,
            }
            
            response = requests.post(approval_url, headers=headers, json=data)
            logger.info(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                approval_key = result.get("approval_key")
                if approval_key:
                    logger.info(f"웹소켓 승인키 발급 성공: {approval_key[:20]}...")
                    return approval_key
                else:
                    logger.error(f"응답에 approval_key가 없음. 응답: {result}")
                    return None
            else:
                logger.error(f"웹소켓 승인키 발급 실패: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"웹소켓 승인키 발급 오류: {e}")
            return None