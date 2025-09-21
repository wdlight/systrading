# 한국투자증권 API 클라이언트
# utils.py에서 이동된 KoreaInvestAPI 클래스

import json
import requests
from datetime import datetime
import pandas as pd
import os
from loguru import logger
from core.interfaces.broker_interface import BrokerInterface
from .ki_env import KoreaInvestEnv

class APIResponse:
    """API 응답 래퍼 클래스"""
    def __init__(self, resp):
        self._rescode = resp.status_code
        self._resp = resp
        
        try:
            self._body = resp.json()
        except:
            self._body = {}
            
    def get_body(self):
        """응답 본문 반환"""
        return type('obj', (object,), self._body)
        
    def is_ok(self):
        """성공 여부 확인"""
        return self._rescode == 200 and self._body.get('rt_cd', '1') == '0'
        
    def print_error(self):
        """에러 출력"""
        if not self.is_ok():
            logger.error(f"API Error: {self._body}")

class KoreaInvestAPI(BrokerInterface):
    """한국투자증권 API 클라이언트"""
    
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

    def authenticate(self, credentials):
        """인증 처리 (이미 KoreaInvestEnv에서 처리됨)"""
        return True

    def get_account_balance(self):
        """계좌 잔고 조회"""
        return self.get_acct_balance()

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
                r2 = t1.get_body().output2
                tot_evlu_amt = int(r2[0]['tot_evlu_amt'])
                return tot_evlu_amt, pd.DataFrame(columns=out_columns)
            return 0, pd.DataFrame(columns=out_columns)

    def get_minute_chart_data(self, stock_code):
        """
        1분봉 차트 데이터 조회
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice
        """
        url = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
        tr_id='FHKST03010230'

        params = {
            'FID_ETC_CLS_CODE': "",
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': datetime.now().strftime("%Y%m%d"),
            'FID_INPUT_HOUR_1': datetime.now().strftime("%H%M%S"),
            'FID_PW_DATA_INCU_YN': 'Y',
            'FID_FAKE_TICK_INCU_YN': 'N'
        }

        t1 = self._url_fetch( url, tr_id, params)
        output_columns = ['일자', '시간', '시가', '고가', '저가', '종가']
        if t1 is None : 
            return pd.DataFrame( columns=output_columns)
        try:
            output2 = t1.get_body().output2
        except Exception as e:
            logger.info(f"Exception: {e}, t1: {t1}")
            return pd.DataFrame(columns=output_columns)

        if t1 is not None and t1.is_ok() and output2:
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
            df[target_columns[2:]] = df[target_columns[2:]].apply(pd.to_numeric)
            column_name_map = dict(zip(target_columns, output_columns))
            df.rename( columns=column_name_map, inplace=True)
            return df[::-1].reset_index(drop=True)
        else:
            return pd.DataFrame(columns=output_columns)

    def buy_order(self, stock_code, order_qty, order_price, order_type="00"):
        """매수 주문"""
        t1 = self.stock_order(stock_code, order_qty, order_price, buy_flag=True, order_type=order_type)
        return t1

    def sell_order(self, stock_code, order_qty, order_price, order_type="00"):
        """매도 주문"""
        t1 = self.stock_order(stock_code, order_qty, order_price, buy_flag=False, order_type=order_type)
        return t1

    def cancel_order(self, stock_code, order_qty, order_price, order_type="00"):
        """주문 취소 (향후 구현)"""
        # TODO: 주문 취소 구현
        logger.warning("cancel_order 메서드는 아직 구현되지 않았습니다")
        return None

    def revise_order(self, stock_code, order_qty, order_price, order_type="00"):
        """주문 정정 (향후 구현)"""
        # TODO: 주문 정정 구현
        logger.warning("revise_order 메서드는 아직 구현되지 않았습니다")
        return None

    def stock_order(self, stock_code, order_qty, order_price, prd_code="01", buy_flag=True, order_type="00"):
        """주식 실제 매매를 위한 주문"""
        url = "/uapi/domestic-stock/v1/trading/order-cash"
        tr_id = "TTTC0012U" if buy_flag else "TTTC0011U"
        params = {
            "CANO": self.stock_account_number ,  #종합계좌번호
            "ACNT_PRDT_CD": prd_code ,  #상품유형코드
            "PDNO": stock_code ,  #종목코드(6자리) , ETN의 경우 7자리 입력
            "ORD_DVSN":  order_type,  
            "ORD_QTY": str(order_qty) ,  #주문수량
            "ORD_UNPR": str(order_price) ,  # 주문단가
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request=True, use_hash=True)
        
        if t1 is not None and t1.is_ok():
            return t1
        elif t1 is None:
            return None
        else:
            t1.print_error()
            return None

    def set_order_hash_key(self, h, p):
        """주식 매매를 위한 hash key 발급"""
        url = f"{self.stock_api_url}/uapi/hashkey"

        response = requests.post(url, data=json.dumps(p), headers=h)
        result = response.status_code
        
        # Hash key API 호출도 로깅
        self._write_api_log("HASHKEY", url, p, response, True)

        if result == 200:
            h['hashkey'] = response.json()['HASH']
        else:
            logger.info(f"Error: {result}")

    def _write_api_log(self, tr_id, url, params, response, is_post=False):
        """API 호출을 일별 로그 파일에 기록"""
        print(f"[_write_api_log] CALLED - TR_ID: {tr_id}")  # 강제 로그 출력
        try:
            # 날짜별 로그 파일 경로
            today = datetime.now().strftime("%Y%m%d")
            # 프로젝트 루트에서 logs 디렉토리 찾기
            current_file = os.path.abspath(__file__)
            project_root = current_file
            # 상위로 올라가면서 logs 디렉토리 찾기
            for _ in range(5):  # 최대 5단계까지 상위로 올라가기
                project_root = os.path.dirname(project_root)
                logs_dir = os.path.join(project_root, "logs")
                if os.path.exists(logs_dir) or os.path.basename(project_root) == "0908.claude-init":
                    break
            
            log_dir = os.path.join(project_root, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"API_{today}.log")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            method = "POST" if is_post else "GET"
            
            # 응답 내용 준비
            if response and hasattr(response, 'status_code'):
                status = response.status_code
                try:
                    response_json = response.json()
                    response_text = json.dumps(response_json, ensure_ascii=False, indent=2)
                except:
                    response_text = response.text[:1000] if hasattr(response, 'text') else str(response)[:1000]
            else:
                status = "N/A"
                response_text = "No response"
            
            # 파라미터 문자열화
            params_str = json.dumps(params, ensure_ascii=False, indent=2) if params else "No parameters"
            
            # 로그 내용 구성
            log_entry = f"""
================================================================================
[{timestamp}] KOREA INVESTMENT API CALL
================================================================================
TR_ID: {tr_id}
METHOD: {method}
URL: {url}
STATUS: {status}

PARAMETERS:
{params_str}

RESPONSE:
{response_text}

================================================================================

"""
            
            # 파일에 로그 추가
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"API 로깅 실패: {e}")

    def _url_fetch(self, api_url, tr_id, params, is_post_request=False, use_hash=True, tr_cont=""):
        """API 호출 공통 메서드"""
        logger.info(f"[_url_fetch] 호출됨 - TR_ID: {tr_id}, URL: {api_url}")
        response = None
        try:
            # API URL 구성
            if api_url.startswith('/'):
                url = f'{self.stock_api_url}{api_url}'
            else:
                url = api_url
                
            headers = self._base_headers.copy()

            # 모의 투자용 TR_ID 변환
            if tr_id[0] in ('T', 'J', 'C', 'F', 'H'):
                if self.is_paper_trading:
                    tr_id = 'V' + tr_id[1:]

            # 필수 헤더들
            headers['tr_id'] = tr_id
            headers['custtype'] = self.custtype
            headers['tr_cont'] = tr_cont
            headers['Content-Type'] = 'application/json; charset=utf-8'

            if is_post_request:
                if use_hash:
                    self.set_order_hash_key( headers, params)
                response = requests.post(url, headers=headers, data=json.dumps(params) )
            else:
                response = requests.get(url, headers=headers, params=params)
            
            # API 호출 및 응답을 일별 로그 파일에 기록
            self._write_api_log(tr_id, url, params, response, is_post_request)
            
            if response.status_code == 200:
                ar = APIResponse(response)
                # --- Start of Gemini Modification ---
                try:
                    response_body = ar.get_body()
                    # mappingproxy 객체를 안전하게 처리하기 위한 변환
                    def convert_to_serializable(obj):
                        """mappingproxy와 getset_descriptor 등 특수 객체를 JSON 직렬화 가능한 형태로 변환"""
                        # getset_descriptor, method-wrapper 등 직렬화 불가능한 타입들
                        obj_type_name = str(type(obj).__name__)
                        if obj_type_name in ['getset_descriptor', 'method-wrapper', 'builtin_function_or_method', 'function', 'method']:
                            return f"<{obj_type_name}: {str(obj)}>"

                        if hasattr(obj, '__dict__'):
                            # __dict__에서 직렬화 불가능한 속성들을 필터링
                            result = {}
                            for k, v in obj.__dict__.items():
                                try:
                                    result[k] = convert_to_serializable(v)
                                except (TypeError, ValueError):
                                    result[k] = f"<non-serializable: {str(type(v).__name__)}>"
                            return result
                        elif isinstance(obj, dict):
                            result = {}
                            for k, v in obj.items():
                                try:
                                    result[k] = convert_to_serializable(v)
                                except (TypeError, ValueError):
                                    result[k] = f"<non-serializable: {str(type(v).__name__)}>"
                            return result
                        elif isinstance(obj, (list, tuple)):
                            return [convert_to_serializable(item) for item in obj]
                        elif hasattr(obj, '_asdict'):  # namedtuple
                            return convert_to_serializable(obj._asdict())
                        elif str(type(obj).__name__) == 'mappingproxy':
                            return dict(obj)
                        else:
                            # 기본 타입들 (str, int, float, bool, None) 확인
                            try:
                                json.dumps(obj)  # 테스트 직렬화
                                return obj
                            except (TypeError, ValueError):
                                return f"<non-serializable: {obj_type_name}>"

                    # 안전한 변환 후 JSON 직렬화
                    serializable_body = convert_to_serializable(response_body)
                    response_text = json.dumps(serializable_body, ensure_ascii=False, indent=2)
                    # log_message = (
                    #     f"[_url_fetch RESPONSE]\n"
                    #     f"  - TR_ID: {tr_id}\n"
                    #     f"  - URL: {url}\n"
                    #     f"  - PARAMS: {params}\n"
                    #     f"  - RESPONSE_BODY:\n{response_text}"
                    # )
                    # logger.info(log_message)
                except Exception as log_e:
                    logger.error(f"[_url_fetch] 응답 로깅 실패: {log_e}")
                    logger.error(f" raw data : {response.text}")
                # --- End of Gemini Modification ---
                return ar
            else:
                logger.error(f"API Error - Status: {response.status_code}")
                logger.error(f"Response Text: {response.text}")
                logger.error(f"Request URL: {url}")
                logger.error(f"Request Headers: {headers}")
                return None
                
        except Exception as e:
            logger.info(f"URL exception: {e}")
            # 예외 발생 시에도 로그 기록
            if response is None:
                self._write_api_log(tr_id, url if 'url' in locals() else api_url, params, None, is_post_request)
            return None

    def __str__(self):
        return f"KoreaInvestAPI(config={self.config})"