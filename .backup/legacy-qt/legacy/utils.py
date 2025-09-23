import requests
import time
from loguru import logger
import json
import copy, yaml
import os
from datetime import datetime, timedelta

import Crypto
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode

import pandas as pd
from collections import namedtuple
from datetime import datetime

# from realtime_view import aes_cbc_base64_dec  # 순환 import 방지를 위해 제거

def aes_cbc_base64_dec(key, iv, cipher_text):
    """
    :param key = str type AES256 secret key value
    :param iv = str type AES256 initialize Vector
    :param cipher_text = str type Base64 encoded AES256 str
    :return: Base64-AES256 decodec str
    """
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size()))



class TokenManager:
    """토큰 파일 기반 관리 클래스"""
    
    def __init__(self, token_file="access.tok"):
        self.token_file = token_file
        self.backup_dir = "token_backup"
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def load_token_data(self):
        """토큰 파일에서 데이터 로드"""
        if not os.path.exists(self.token_file):
            return None
            
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"토큰 파일 로드 실패: {e}")
            return None
    
    def save_token_data(self, token_data):
        """토큰 데이터를 파일에 저장"""
        try:
            # 기존 파일이 있으면 백업
            if os.path.exists(self.token_file):
                self._backup_existing_token()
            
            # 새로운 토큰 데이터 저장
            token_data['last_updated'] = datetime.now().isoformat()
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"토큰 파일 저장 완료: {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"토큰 파일 저장 실패: {e}")
            return False
    
    def _backup_existing_token(self):
        """기존 토큰 파일을 날짜별로 백업"""
        try:
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"access.{current_date}.tok"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            import shutil
            shutil.copy2(self.token_file, backup_path)
            logger.info(f"토큰 파일 백업 완료: {backup_path}")
        except Exception as e:
            logger.error(f"토큰 파일 백업 실패: {e}")
    
    def is_token_expired(self, hours_threshold=12):
        """토큰 파일의 생성 시간과 토큰 데이터를 기준으로 만료 여부 확인 (기본 12시간)"""
        if not os.path.exists(self.token_file):
            logger.info("토큰 파일이 존재하지 않음")
            return True
        
        try:
            # 토큰 데이터 로드
            token_data = self.load_token_data()
            if not token_data:
                logger.info("토큰 데이터 로드 실패")
                return True
            
            # last_updated 시간이 있으면 우선 사용
            if 'last_updated' in token_data:
                try:
                    last_updated = datetime.fromisoformat(token_data['last_updated'])
                    now = datetime.now()
                    elapsed_hours = (now - last_updated).total_seconds() / 3600
                    
                    logger.info(f"토큰 마지막 업데이트: {last_updated}")
                    logger.info(f"현재 시간: {now}")
                    logger.info(f"경과 시간: {elapsed_hours:.2f}시간")
                    
                    return elapsed_hours >= hours_threshold
                except ValueError as e:
                    logger.warning(f"last_updated 파싱 실패: {e}, 파일 수정시간으로 폴백")
            
            # last_updated가 없거나 파싱 실패 시 파일 수정시간 사용
            file_mtime = os.path.getmtime(self.token_file)
            file_time = datetime.fromtimestamp(file_mtime)
            now = datetime.now()
            elapsed_hours = (now - file_time).total_seconds() / 3600
            
            logger.info(f"토큰 파일 생성 시간: {file_time}")
            logger.info(f"현재 시간: {now}")
            logger.info(f"경과 시간: {elapsed_hours:.2f}시간")
            
            return elapsed_hours >= hours_threshold
        except Exception as e:
            logger.error(f"토큰 만료 시간 확인 실패: {e}")
            return True

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




class KoreaInvestAPI:
    def __init__(self, config, base_headers=None):
        self.config = config
        self.custtype = config.get('custtype', 'P')
        self.websocket_approval_key = config.get('websocket_approval_key')
        self.stock_account_number = config.get('stock_account_number')
        self.paper_url = config.get('paper_url', 'https://openapivts.koreainvestment.com:29443')
        self.is_paper_trading = config.get('is_paper_trading', False)
        self.htsid = config.get('htsid', '')
        self.stock_api_url = config.get('using_url')
        
        # g_approval_key와 g_personal_seckey 설정
        self.g_approval_key = self.websocket_approval_key
        self.g_personal_seckey = config.get('api_secret_key', '')
        
        # KoreaInvestEnv에서 헤더를 가져오거나 기본값 설정
        if base_headers:
            self._base_headers = base_headers.copy()
        else:
            # 기본 헤더 설정 (KoreaInvestEnv가 없을 경우)
            env = KoreaInvestEnv(config)
            self._base_headers = env.get_base_headers()
        
        # 연속조회를 위한 키 저장 변수
        self.balance_ctx_fk100 = ""
        self.balance_ctx_nk100 = ""



    def set_order_hash_key(self, h, p ):
        url = f"{self.using_url}/uapi/hashkey"
        
        res = requests.post(url, data=json.dumps(p), headers=h)
        return res
    
    def get_current_price(self, stock_no):
        url = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"

        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_no
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request=False, tr_cont="")

        if t1 is not None and t1.is_ok():
            return t1.get_body().output
        elif t1 is None:
            return dict()

    def get_hoga_info(self, stock_no):
        """주식 호가/예상 체결 조회"""
        url = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"    
        tr_id = "FHKST01010200"
        v_tr_id ="FHKST01010200"

        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_no,
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request=False, tr_cont="")

        if t1 is not None and t1.is_ok():
            return t1.get_body().output1
        elif t1 is None:
            t1.print_error()
            return dict()


    def get_minute_chart_data(self, stock_code):
        # 계좌 잔고 평가 잔고와 상세 내역을 Data Frame으로 반환.
        url = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
        tr_id='FHKST03010230'

        params = {
            'FID_ETC_CLS_CODE': "",
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_HOUR_1': datetime.now().strftime("%H%M%S"),
            'FID_PW_DATA_INCU_YN': 'Y'
        }

        t1 = self._url_fetch( url, tr_id, params)
        output_columns = ['일자', '시간', '시가', '고가', '저가', '종가']
        if t1 is None : 
            return 0, pd.DataFrame( columns=output_columns)
        try:
            output2 = t1.get_body().output2
        except Exception as e:
            logger.info(f"Exception: {e}, t1: {t1}")
            return 0, pd.DataFrame(columns=output_columns)

        if t1 is not None and t1.is_ok() and output2: # body 의 rt_cd 가 0 인 경우에만 성공
            df = pd.DataFrame(output2)
            target_columns = [
                'stck_bsop_date',
                'stck_cntg_hour',
                'stck_oprc',
                'stck_hgpr',
                'stck_lwpr',
                'stck_prpr',
            ]

            df = df[target_columns ]
            df[target_columns[2:]] = df[target_columns[2:]].apply(pd.to_numeric) # 종목코드, 종목명 제외 하고 형변환
            column_name_map = dict(zip(target_columns, output_columns))
            df.rename( columns=column_name_map, inplace=True)
            return df[::-1].reset_index(drop=True)
        else:
            return pd.DataFrame(columns=output_columns)

        


    def get_acct_balance(self):
        """
        계좌 balance 조회 : https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/inquire-balance
        """
        url = "/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "TTTC8434R"

        params = {
            'CANO': self.stock_account_number,
            "ACNT_PRDT_CD": "01", 
            "AFHR_FLPR_YN": "N",     # 계좌 상품 코드 01 : 국내 주식, 02 : 선물, 03 : 
            "OFL_YN": "",            # 오프라인 여부 (공란 처리)
            "INQR_DVSN": "02",       # 01 : 대출일별, 02 : 종목별
            "UNPR_DVSN": "01",       # 단가 구분
            "FUND_STTL_ICLD_YN": "N", #펀드 결제분 포함 여부 , N - 포함하지 않음, ㅛ - 포함
            "FNCG_AMT_AUTO_RDPT_YN": "N",   # 기본 값 - N
            "PRCS_DVSN": "00",            # 처리 구분  00 전일매매포함, 01 전일매매미포함
            "CTX_AREA_FK100": self.balance_ctx_fk100,    # 연속조회검색조건100
            "CTX_AREA_NK100": self.balance_ctx_nk100     # 연속조회키100
        }

        t1 = self._url_fetch(url, tr_id, params)
        out_columns   = ["종목코드", "종목명",    "보유수량",   "매도가능수량", "매입단가", "수익률",         "현재가", "전일대비", "전일대비 등락률" ]
        
        if t1 is None:
            return 0, pd.DataFrame(columns=out_columns)
        
        try:
            output1 = t1.get_body().output1
            logger.info(f' account info output : {output1}')
        except Exception as e:
            logger.info(f"account balance Fetch Exception: {e}, t1: {t1.get_body()}")
            return 0, pd.DataFrame(columns=out_columns)

        if t1 is not None and t1.is_ok() and output1:
            # 연속조회 키 저장 (다음 조회를 위해)
            try:
                response_body = t1.get_body()
                self.balance_ctx_fk100 = getattr(response_body, 'ctx_area_fk100', "")
                self.balance_ctx_nk100 = getattr(response_body, 'ctx_area_nk100', "")
                logger.info(f"연속조회 키 저장: FK100={self.balance_ctx_fk100}, NK100={self.balance_ctx_nk100}")
            except Exception as e:
                logger.warning(f"연속조회 키 저장 실패: {e}")
            
            df = pd.DataFrame(output1)
            target_columns = [ 'pdno',  'prdt_name', 'hldg_qty', 'ord_psbl_qty', 'pchs_amt', 'evlu_erng_rt','prpr', 'bfdy_cprs_icdc', 'fltt_rt' ]
            df = df[target_columns]
            df[target_columns[2:]] = df[target_columns[2:]].apply(pd.to_numeric) # 종목코드, 종목명 제외하고 형변환
            column_name_map = dict( zip(target_columns, out_columns))
            df.rename(columns=column_name_map, inplace=True)
            df = df[df['보유수량'] !=0]
            r2 = t1.get_body().output2

            return int( r2[0]['tot_evlu_amt']), df      # body2.tot_evlu_amt - 총평가금액

        else:
            logger.info(f"t1.is_ok(): {t1.is_ok()}, output1: {output1}")
            tot_evlu_amt = 0
            if t1.is_ok():
                r2 = t1.get_body().output2tot_evlu_amt = int(r2[0]['tot_evlu_amt'])
                tot_evlu_amt = int(r2[0]['tot_evlu_amt'])
                return tot_evlu_amt, pd.DataFrame(columns=out_columns)
        

    def get_fluctuation_ranking(self):
        """
        등락율 순위 조회 : 2025.08 
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/ranking/fluctuation
        """
        url = "/uapi/domestic-stock/v1/ranking/fluctuation"
        tr_id = "FHPST01700000"
        params = {
            "fid_rsfl_rate2": "",   # 공백 입력 시 전체 (~ 비율
            "fid_cond_mrkt_div_code": "J" ,               # 시장구분코드 (J:KRX, NX:NXT)
            "fid_cond_scr_div_code": "20170",               # Unique key( 20170 )
            "fid_input_iscd": "0001" ,               # 0000(전체) 코스피(0001), 코스닥(1001), 코스피200(2001)
            "fid_rank_sort_cls_code": "0",               # 0:상승율순 1:하락율순 2:시가대비상승율 3:시가대비하락율 4:변동율
            "fid_input_cnt_1": "0",               # 0:전체 , 누적일수 입력
            "fid_prc_cls_code":"0",               # 'fid_rank_sort_cls_code :0 상승율 순일때 (0:저가대비, 1:종가대비)
                                                    #fid_rank_sort_cls_code :1 하락율 순일때 (0:고가대비, 1:종가대비)
                                                    #fid_rank_sort_cls_code : 기타 (0:전체)'
            "fid_input_price_1": "",               # 공백 입력 시 전체 (가격 ~)
            "fid_input_price_2": "",               # 공백 입력 시 전체 (가격 ~)
            "fid_vol_cnt": "",                        # 공백 입력 시 전체 (거래량 ~)
            "fid_trgt_cls_code": "0",               #  0:전체    
            "fid_trgt_exls_cls_code": "0",               # 0:전체
            "fid_div_cls_code": "0",               # 0:전체
            "fid_rsfl_rate1": "",               # 공백 입력 시 전체 (비율 ~)
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request=False, tr_cont="")

        if t1 is not None and t1.is_ok():
            df = pd.DataFrame( t1.get_body().output )
            target_columns = ["stck_shrn_iscd", "hts_kor_isnm", "stck_prpr", "prdy_vrss"]
            out_columns = ['종목코드',"종목 명", "현재가","전일대비" ]
            df = df[target_columns]
            df[target_columns[2:]] = df[target_columns[2:]].apply(pd.to_numeric)
            columns_rename_map = dict( zip( target_columns, out_columns))
            df.rename(columns=columns_rename_map, inplace=True)

            return df # t1.get_body().output
        elif t1 is None:
            t1.print_error()
            return dict()




    def set_order_hash_key(self, h, p):
        """주식 매매를 위한 hash key 발급"""
        url = f"{self.stock_api_url}/uapi/hashkey"

        response = requests.post(url, data=json.dumps(p), headers=h)
        result = response.status_code

        if result == 200:
            h['hashkey'] = response.json()['HASH']
        else:
            logger.info(f"Error: {result}")

    def buy_order(self, stock_code, order_qty, order_price, order_type="00"):
        t1 = self.stock_order(stock_code, order_qty, order_price, buy_flag=True, order_type=order_type)
        return t1

    def sell_order(self, stock_code, order_qty, order_price, order_type="00"):
        t1 = self.stock_order(stock_code, order_qty, order_price, buy_flag=False, order_type=order_type)
        return t1

        

    def stock_order(self,stock_code, order_qty, order_price, prd_code="01", buy_flag=True, order_type="00"):
        """주식 실제 매매를 위한 주문"""
        url = "/uapi/domestic-stock/v1/trading/order-cash"
        tr_id = "TTTC0012U" if buy_flag else "TTTC0011U"
        params = {
            "CANO": self.stock_account_number ,  #종합계좌번호
            "ACNT_PRDT_CD": prd_code ,  #상품유형코드
            "PDNO": stock_code ,  #종목코드(6자리) , ETN의 경우 7자리 입력
            "ORD_DVSN":  order_type,  
                            # """
                            # 00 : 지정가
                            # 03 : 최유리지정가
                            # 04 : 최우선지정가
                            # 11 : IOC지정가 (즉시체결,잔량취소)
                            # 12 : FOK지정가 (즉시체결,전량취소)
                            # 13 : IOC시장가 (즉시체결,잔량취소)
                            # 14 : FOK시장가 (즉시체결,전량취소)
                            # 15 : IOC최유리 (즉시체결,잔량취소)
                            # 16 : FOK최유리 (즉시체결,전량취소)
                            # 21 : 중간가
                            # 22 : 스톱지정가
                            # 23 : 중간가IOC
                            # 24 : 중간가FOK
                            # """

            "ORD_QTY": str(order_qty) ,  #주문수량
            "ORD_UNPR": str(order_price) ,  # 주문단가
                                            # 시장가 등 주문시, "0"으로 입력         
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request=True, use_hash=True)
        out_columns   = ["종목코드", "종목명",    "보유수량",   "매도가능수량", "매입단가", "수익률",         "현재가", "전일대비", "전일대비 등락률" ]
        
        if t1 is not None and t1.is_ok():
            return t1
        elif t1 is None:
            return None
        else:
            t1.print_error()
            return None
            

                

###################################################

    def get_stock_price(self, ticker, date=None):
        """주식 현재가 조회"""
        try:
            if date:
                df = stock.get_market_ohlcv_by_date(date, date, ticker)
            else:
                df = stock.get_market_ohlcv_by_ticker(date, ticker)
            return df
        except Exception as e:
            print(f"주식 데이터 조회 오류: {e}")
            return None


        
    
    def get_market_cap(self, date=None):
        """시가총액 상위 종목 조회"""
        try:
            df = stock.get_market_cap(date)
            return df
        except Exception as e:
            print(f"시가총액 데이터 조회 오류: {e}")
            return None
    
    def get_ticker_name(self, ticker):
        """종목코드로 종목명 조회"""
        try:
            name = stock.get_market_ticker_name(ticker)
            return name
        except Exception as e:
            print(f"종목명 조회 오류: {e}")
            return None


    def _url_fetch(self, api_url, tr_id, params, is_post_request=False, use_hash=True, tr_cont=""):
        try:
            # API URL 구성 - GitHub 코드 참고
            if api_url.startswith('/'):
                url = f'{self.stock_api_url}{api_url}'
            else:
                url = api_url
                
            headers = self._base_headers.copy()

            # 모의 투자용 TR_ID 변환
            if tr_id[0] in ('T', 'J', 'C', 'F', 'H'): # GitHub 코드 참고: F, H 추가
                if self.is_paper_trading:
                    tr_id = 'V' + tr_id[1:]

            # GitHub 코드 참고 - 필수 헤더들
            headers['tr_id'] = tr_id
            headers['custtype'] = self.custtype
            headers['tr_cont'] = tr_cont  # 연속 거래 여부
            
            # Content-Type 중복 방지
            headers['Content-Type'] = 'application/json; charset=utf-8'
            
            #print(f"DEBUG: Request URL: {url}")
            #print(f"DEBUG: Request Headers: {headers}")
            ##print(f"DEBUG: Request Params: {params}")
            #print(f"DEBUG: Is POST Request: {is_post_request}")
            #print(f"DEBUG: TR_ID after conversion: {tr_id}")

            if is_post_request:
                if use_hash:
                    self.set_order_hash_key( headers, params)
                response = requests.post(url, headers=headers, data=json.dumps(params) )

            else:
                print(f"DEBUG: Making GET request with params: {params}")
                response = requests.get(url, headers=headers, params=params)
                print(f"DEBUG: Final request URL with params: {response.url}")

            #print(f"DEBUG: Response Status: {response.status_code}")
            #print(f"DEBUG: Response Headers: {dict(response.headers)}")
            #print(f"DEBUG: Response Text: {response.text}")
            
            if response.status_code == 200:
                ar = APIResponse(response)
                return ar
            else:
                logger.error(f"API Error - Status: {response.status_code}")
                logger.error(f"Response Text: {response.text}")
                logger.error(f"Request URL: {url}")
                logger.error(f"Request Headers: {headers}")
                return None
                
        except Exception as e:
            logger.info(f"URL exception: {e}")
        

    def get_send_data(self, cmd=None, stock_code=None):
        # 1.주식호가, 2.주식호가해제, 3. 주식체결, 4.주식체결해제, 5.주식체결통보(고객), 
        # 6. 주식체결통보해제(고객), 7.주식체결통보(모의), 8. 주식체결통보해제(모의)

        # 입력값 check
        assert 0 < cmd < 9, f"WrongInput Data: {cmd}"
        
        tr_ids = ['HOSTASP0',]

        #입력값에 따른 전송 데이터셋 구분 처리
        match cmd:
            case 1:
                tr_id = 'H0STASP0'
                tr_type = '1'
            case 2:
                tr_id = 'H0STASP0'
                tr_type = '2'
            case 3:
                tr_id = 'H0STCNT0'
                tr_type = '1'
            case 4:
                tr_id = 'H0STCNT0'
                tr_type = '2'
            case 5:
                tr_id = 'H0STCNI0'
                tr_type = '1'
            case 6:
                tr_id = 'H0STCNI0'
                tr_type = '2'
            case 7:
                tr_id = 'H0STCNI9'
                tr_type = '1'
            case 8:
                tr_id = 'H0STCNI9'
                tr_type = '2'

        if cmd in ( 5,6,7,8):
            send_data = (
                '{"header":{"approval_key":"' + self.g_approval_key + 
                '","personalseckey":"' + self.g_personal_seckey + 
                '","custtype":"' + self.custtype + 
                '","tr_type":"' + tr_type + 
                '","content-type":"utf-8"},"body":{"input":{"tr_id":"' + tr_id + 
                '","tr_key":"' + self.htsid + '"}}}'
            )
        else:
            send_data = (
                '{"header":{"approval_key":"' + self.g_approval_key + 
                '","personalseckey":"' + self.g_personal_seckey + 
                '","custtype":"' + self.custtype + 
                '","tr_type":"' + tr_type + 
                '","content-type":"utf-8"},"body":{"input":{"tr_id":"' + tr_id + 
                '","tr_key":"' + stock_code + '"}}}'
            )
        
        return send_data


    def oversea_get_send_data(self, cmd=None, stock_code=None):
        # 1.주식호가, 2.주식호가해제, 3. 주식체결, 4.주식체결해제, 5.주식체결통보(고객), 
        # 6. 주식체결통보해제(고객), 7.주식체결통보(모의), 8. 주식체결통보해제(모의)

        # 입력값 check
        assert 0 < cmd < 9, f"WrongInput Data: {cmd}"
        
        #tr_ids = ['HOSTASP0',]

        #입력값에 따른 전송 데이터셋 구분 처리
        match cmd:
            case 1: # 주식 호가 등록
                tr_id = 'HDFSASP0'
                tr_type = '1'
            case 2: # 주식 호가 등록 헤제
                tr_id = 'HDFSASP0'
                tr_type = '2'
            case 3: # 주식 체결 등록
                tr_id = 'HDFSCNT0'
                tr_type = '1'
            case 4: # 주식 체결 등록 해제
                tr_id = 'HDFSCNT0'
                tr_type = '2'
            case 5: # 주식체결통보 등록(고객용)
                tr_id = 'H0GS용NI0'
                tr_type = '1'
            case 6: # 주식 체결통보 등록 해제
                tr_id = 'H0GS용NI0'
                tr_type = '2'
        

        if cmd in ( 5,6,7,8):
            send_data = (
                '{"header":{"approval_key":"' + self.g_approval_key + 
                '","personalseckey":"' + self.g_personal_seckey + 
                '","custtype":"' + self.custtype + 
                '","tr_type":"' + tr_type + 
                '","content-type":"utf-8"},"body":{"input":{"tr_id":"' + tr_id + 
                '","tr_key":"' + self.htsid + '"}}}'
            )
        else:
            send_data = (
                '{"header":{"approval_key":"' + self.g_approval_key + 
                '","personalseckey":"' + self.g_personal_seckey + 
                '","custtype":"' + self.custtype + 
                '","tr_type":"' + tr_type + 
                '","content-type":"utf-8"},"body":{"input":{"tr_id":"' + tr_id + 
                '","tr_key":"' + stock_code + '"}}}'
            )
        
        return send_data



    def do_cancel(self, order_no, order_qty, order_price="01", order_branch="0610", prd_code="01", order_dv="00", cancel_dv="02", qty_all_yn="Y"):
        return self._do_cancel_revise(order_no, order_qty, order_price, order_branch, prd_code, order_dv, cancel_dv, qty_all_yn)

    def oversea_do_cancel(self, order_no, order_qty, order_price="0", order_branch="0610", prd_code="01", cancel_dv="02" ):
        return self._oversea_do_cancel_revise( order_no, order_qty, order_price, order_branch, prd_code, cancel_dv )

    def do_revise(self, order_no, order_qty, order_price="01", order_branch="0610", prd_code="01", order_dv="00", cancel_dv="01", qty_all_yn="Y"):
        return self._do_cancel_revise(order_no, order_qty, order_price, order_branch, prd_code, order_dv, cancel_dv, qty_all_yn)

    def oversea_do_revise(self, order_no, order_qty, order_price="0", order_branch="0610", prd_code="01", cancel_dv="01" ):
        return self._oversea_do_cancel_revise( order_no, order_qty, order_price, order_branch, prd_code, cancel_dv )


    def _do_cancel_revise(self, order_no, order_qty, order_price, order_branch, prd_code, order_dv, cancel_dv, qty_all_yn):
        """
        특정 주문 취소(01)/정정(02)
        input : 주문번호 ( get_orders를 호출해서 얻은 DataFrame의 index column값이 취소 가능한 주문번호임)
                주문점(통상 06010), 주문수량, 주문가격, 상품코드(01), 주문유형(00), 정정구분(취소-02, 정정-01)
        Output : APIResponse Object
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-rvsecncl
        """
        url = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
        tr_id = "TTTC0013U"
        params = {
            "CANO": self.stock_account_number,
            "ACNT_PRDT_CD": prd_code,
            "KRX_FWDG_ORD_ORGNO": order_branch,
            "ORGN_ODNO": order_no,
            "ORD_DVSN": order_dv,
            "RVSE_CNCL_DVSN_CD":cancel_dv, # 취소 ( 02)
            "ORD_QTY": str(order_qty),
            "ORD_UNPR": str(order_price),
            "QTY_ALL_ORD_YN": qty_all_yn
        }

        t1 = self._url_fetch(url, tr_id, params=params, is_post_request=True)

        if t1 is not None and t1.is_ok():
            return t1
        elif t1 is None:
            return None
        else:
            t1.print_error()
            return None


    def receive_signing_notice(data,key,iv,accnt_num):
        """
        """
        #AES256 처리 단계
        aes_dec_str = aes_cbc_base64_dec(key, iv, data)
        values = aes_dec_str.split('^')
        계좌번호  = values(1)

        if 계좌번호[:8] != accnt_num:
            return
        
        거부여부 = values[12]
        if 거부여부 != '0':
            logger.info(f"Got 거부 TR!")
            return

        체결여부 = values[13]
        종목코드 = values[8]
        종목명 = values[18]
        시간 = values[11]
        주문수량 = 0 if len(values[16]) == 0 else int(values[16])

        if values[13] == '1':
            주문가격 = 0 if len(values[10]) else int(values[10])
        else:
            주문가격 = 0 if len(values[22]) else int(values[22])

        체결수량= 0 if len(values[9]) == 0 or 체결여부 =='1' else int(values[9])

        if values[13] == '1':
            체결가격 = 0
        else:   
            체결가격 = 0 if len(values[10]) == 0 else int(values[10])

        매수매도구분 = values[4]
        정정구분 = values[5]

        if 매수매도구분 =="02" and 정정구분 != "0": 
            주문구분 = "매수정정"
        elif 매수매도구분 =="01" and 정정구분 != "0": 
            주문구분 = "매도정정"
        elif 매수매도구분 =="02":
            주문구분 ="매수"
        elif 매수매도구분 =="01":
            주문구분 ="매도"
        else:
            raise ValueError(f"주문구분 실패! 매도매수구분; {매수매도구분}, 정정구분:{정정구분}")

        주문번호 = values[2]
        원주문번호 = values[3]
        logger.info(f"Received chejandata 시간: {시간}" 
                    f"종목코드: {종목코드}, 종목명:{종목명}, 주문수량:{주문수량}"
                    f"주문가격: {주문가격}, 체결수량:{체결수량}, 체결가격:{체결가격}"
                    f"주문문분: {주문구분}, 종목명:{종목명},"
                    f"원주문번호: {원주문번호}, 체결여부:{체결여부}"
        )

    def __str__(self):
        return f"KoreaInvestAPI(config={self.config})"



class APIResponse:


    def __init__(self, resp):
        self._rescode = resp.status_code
        self._resp = resp
        self._header = self._set_header()
        self._body = self._set_body()
        self._err_code = getattr(self._body, 'rt_cd', None) # rt_cd - return code - defined in API
        self._err_message = getattr(self._body, 'msg1', None)

    def get_result_code(self):
        return self._rescode

    def _set_header(self):
        fld = dict()
        for x in self._resp.headers.keys():
            if x.islower():
                fld[x] = self._resp.headers.get(x)

        _th_ = namedtuple('header', fld.keys())
        return _th_(**fld)


    def _set_body(self):
        _tb_ = namedtuple('body', self._resp.json().keys())
        return _tb_(**self._resp.json())

    def get_header(self):
        return self._header

    def get_body(self):
        return self._body

    def get_response(self):
        return self._resp

    def is_ok(self):
        try:
            if ( self.get_body().rt_cd == '0'):
                return True
            else:
                return False
        except:
            return False

    def get_error_code(self):
        return self._err_code

    def get_error_message(self):
        return self._err_message

    def print_all(self):
        """API 응답의 모든 정보를 출력하는 함수"""
        print("=" * 60)
        print("API Response Information")
        print("=" * 60)
        
        # Status Code
        print(f"Status Code: {self._rescode}")
        
        # Headers
        print("\n[Headers]")
        try:
            header_dict = self._header._asdict() if hasattr(self._header, '_asdict') else {}
            for key, value in header_dict.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"  Header parsing error: {e}")
        
        # Body
        print("\n[Body]")
        try:
            body_dict = self._body._asdict() if hasattr(self._body, '_asdict') else {}
            for key, value in body_dict.items():
                if isinstance(value, (dict, list)):
                    print(f"  {key}:")
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            print(f"    {sub_key}: {sub_value}")
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            print(f"    [{i}]: {item}")
                else:
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"  Body parsing error: {e}")
            # Raw JSON 출력 시도
            try:
                import json
                raw_json = self._resp.json()
                print(f"  Raw JSON: {json.dumps(raw_json, indent=2, ensure_ascii=False)}")
            except:
                print(f"  Raw text: {self._resp.text}")
        
        # Error Information
        if self._err_code or self._err_message:
            print("\n[Error Information]")
            print(f"  Error Code: {self._err_code}")
            print(f"  Error Message: {self._err_message}")
        
        # Response Status
        print(f"\n[Status]")
        print(f"  Is OK: {self.is_ok()}")
        
        print("=" * 60)

    def print_error(self):
        logger.info(f'--------------------------')
        logger.info(f'Error in response: {self.get_result_code()}')
        logger.info(f'{self.get_body().rt_cd}, {self.get_error_code()}, {self.get_error_message()}')
        logger.info(f'--------------------------')


