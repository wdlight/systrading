# 한국투자증권 API 클라이언트
# utils.py에서 이동된 KoreaInvestAPI 클래스

import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import time
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

    def get_send_data(self, cmd, stock_code=None):
        """실시간 데이터 요청을 위한 데이터 생성"""
        is_register = cmd in [1, 3, 5]
        tr_type = "1" if is_register else "2"

        tr_id = ""
        tr_key = ""

        if cmd in [1, 2]:  # 실시간호가
            tr_id = "H0STASP0"
            tr_key = stock_code
        elif cmd in [3, 4]:  # 실시간체결
            tr_id = "H0STCNT0"
            tr_key = stock_code
        elif cmd == 5:  # 주문/체결 통보
            tr_id = "H0STCNI0"
            tr_key = self.htsid  # HTS ID 사용
        else:
            raise ValueError(f"Unknown cmd for get_send_data: {cmd}")

        if not tr_key:
             if cmd != 5:
                raise ValueError(f"stock_code is required for cmd {cmd}")

        header = {
            "approval_key": self.g_approval_key,
            "custtype": self.custtype,
            "tr_type": tr_type,
            "content-type": "utf-8"
        }

        body = {
            "input": {
                "tr_id": tr_id,
                "tr_key": tr_key
            }
        }

        return json.dumps({"header": header, "body": body})

    def get_index_send_data(self, tr_key: str) -> str:
        """지수 실시간 구독 요청 생성 (H0STISE0)"""
        header = {
            "approval_key": self.g_approval_key,
            "custtype": self.custtype,
            "tr_type": "1",  # 등록
            "content-type": "utf-8"
        }

        body = {
            "input": {
                "tr_id": "H0STISE0",
                "tr_key": tr_key
            }
        }

        return json.dumps({"header": header, "body": body})

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
            target_columns = [ 'pdno',  'prdt_name', 'hldg_qty', 'ord_psbl_qty', 'pchs_avg_pric', 'evlu_pfls_rt','prpr', 'bfdy_cprs_icdc', 'fltt_rt' ]
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

    def get_minute_chart_data(self, stock_code, start_time=None, max_count=None):
        """
        1분봉 차트 데이터 조회 (개선: 여러 번 호출로 전체 데이터 수집)
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice

        Args:
            stock_code: 종목 코드
            start_time: 시작 시간 (HHMMSS 형식, 기본값: 090000)
            max_count: 최대 조회 개수 (기본값: 무제한, 9:00~현재까지 전체)

        Returns:
            DataFrame: 분봉 데이터 (과거 -> 최신 순서)
        """
        url = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
        tr_id='FHKST03010230'

        output_columns = ['일자', '시간', '시가', '고가', '저가', '종가', '거래량']

        # 시작 시간 기본값: 09:00:00 (장 시작)
        if start_time is None:
            start_time = "090000"

        # 현재 시간
        current_date = datetime.now().strftime("%Y%m%d")
        current_time = datetime.now().strftime("%H%M%S")

        all_data = []
        end_time = current_time
        iteration = 0
        max_iterations = 10  # 무한 루프 방지 (최대 1200분 = 20시간)

        logger.info(f"📊 분봉 데이터 수집 시작: {stock_code}, {start_time} ~ {end_time}")

        while iteration < max_iterations:
            params = {
                'FID_ETC_CLS_CODE': "",
                'FID_COND_MRKT_DIV_CODE': 'J',
                'FID_INPUT_ISCD': stock_code,
                'FID_INPUT_DATE_1': current_date,
                'FID_INPUT_HOUR_1': end_time,
                'FID_PW_DATA_INCU_YN': 'Y',  # 가격 데이터 포함
                'FID_FAKE_TICK_INCU_YN': 'N'  # 가짜 틱 제외
            }

            # ✅ API 요청 파라미터 로그
            logger.info(f"🌐 API 요청 [{iteration + 1}]: end_time={end_time}, target=09:00부터 {end_time}까지 역순 조회")

            t1 = self._url_fetch(url, tr_id, params)

            if t1 is None:
                logger.warning(f"⚠️ API 응답 없음 (iteration {iteration})")
                break

            try:
                output2 = t1.get_body().output2
            except Exception as e:
                logger.info(f"Exception: {e}, t1: {t1}")
                break

            if not (t1.is_ok() and output2):
                logger.warning(f"⚠️ 유효하지 않은 응답 (iteration {iteration})")
                break

            # 데이터 변환
            df_batch = pd.DataFrame(output2)
            target_columns = [
                'stck_bsop_date',
                'stck_cntg_hour',
                'stck_oprc',
                'stck_hgpr',
                'stck_lwpr',
                'stck_prpr',
                'cntg_vol',
            ]

            df_batch = df_batch[target_columns]
            df_batch[target_columns[2:]] = df_batch[target_columns[2:]].apply(pd.to_numeric)
            column_name_map = dict(zip(target_columns, output_columns))
            df_batch.rename(columns=column_name_map, inplace=True)

            # 역순으로 정렬 (최신 -> 과거 → 과거 -> 최신)
            df_batch = df_batch[::-1].reset_index(drop=True)

            batch_count = len(df_batch)

            # ✅ 배치 데이터 범위 로그 (역순 정렬 후: 첫번째=가장 오래된 시간, 마지막=최신 시간)
            if batch_count > 0:
                oldest_in_batch = df_batch.iloc[0]['시간']   # 과거 (가장 오래된)
                newest_in_batch = df_batch.iloc[-1]['시간']  # 최신 (가장 최근)
                logger.info(f"📦 Batch {iteration + 1}: {batch_count}개 수집 | 범위: {oldest_in_batch}(oldest) ~ {newest_in_batch}(newest)")
            else:
                logger.info(f"📦 Batch {iteration + 1}: 0개")

            if batch_count == 0:
                logger.info("✅ 더 이상 데이터 없음")
                break

            all_data.append(df_batch)

            # 시작 시간에 도달했는지 확인
            # ✅ 수정: 역순 정렬 후 첫 번째가 가장 오래된 시간
            oldest_time = df_batch.iloc[0]['시간']
            if oldest_time <= start_time:
                logger.info(f"✅ 시작 시간 {start_time}에 도달")
                break

            # 다음 배치를 위한 종료 시간 업데이트
            # ✅ 수정: 가장 오래된 데이터(배치의 첫 번째)의 1분 전으로 설정
            # (API는 end_time부터 역순으로 반환하므로, 다음 배치는 이전 배치의 oldest - 1분부터 시작)
            oldest_datetime = datetime.strptime(oldest_time, "%H%M%S")
            next_end_datetime = oldest_datetime - timedelta(minutes=1)
            prev_end_time = end_time
            end_time = next_end_datetime.strftime("%H%M%S")
            logger.info(f"🔄 다음 end_time: {prev_end_time} → {end_time} (oldest {oldest_time} - 1분)")

            # 최대 개수 체크
            if max_count and sum(len(df) for df in all_data) >= max_count:
                logger.info(f"✅ 최대 개수 {max_count}에 도달")
                break

            iteration += 1

            # API 호출 간격 (초당 최대 20건 제한)
            import time
            time.sleep(0.05)  # 50ms 대기

        # 모든 배치 합치기
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)

            # 시작 시간 이후 데이터만 필터링
            final_df = final_df[final_df['시간'] >= start_time]

            # 최대 개수 제한
            if max_count:
                final_df = final_df.head(max_count)

            # 과거 -> 최신 순서로 정렬 (시간 기준 오름차순)
            final_df = final_df.sort_values(by='시간', ascending=True).reset_index(drop=True)

            logger.info(f"✅ 총 {len(final_df)}개 분봉 데이터 수집 완료")
            return final_df
        else:
            logger.warning("❌ 수집된 데이터 없음")
            return pd.DataFrame(columns=output_columns)

    def get_daily_minute_chart_data(self, stock_code, target_date):
        """
        특정 날짜의 전체 분봉 데이터 조회 (과거 날짜 전용)

        ⚠️ 중요: 오늘 데이터가 아닌 과거 특정 날짜 조회 전용 함수
        ⚠️ API 특성: 한 번 호출로 최대 120개 데이터만 반환 (약 2시간 분량)
        ⚠️ 해결책: 여러 번 호출하여 09:00~15:30 전체 데이터 수집

        전략:
        1. 09:00~11:00, 11:00~13:00, 13:00~15:30 구간으로 3회 호출
        2. 각 구간의 마지막 시간(FID_INPUT_HOUR_1)을 달리하여 호출
        3. 모든 구간 데이터를 병합하여 전체 일자 데이터 생성

        ⚠️ API 문서와 실제 동작 불일치:
        - API 문서: inquire-time-dailychartprice (TR_ID: FHKST03010320) 사용 명시
          https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice
        - 실제: FHKST03010320은 "없는 서비스 코드" 오류 발생 (OPSQ0002)
        - 해결: inquire-time-itemchartprice (TR_ID: FHKST03010230)로 과거 날짜 조회 가능 확인

        Args:
            stock_code (str): 종목코드 (예: "005930")
            target_date (datetime or str): 조회 날짜 (datetime 또는 "YYYYMMDD")

        Returns:
            DataFrame: 해당 날짜의 전체 분봉 데이터 (09:00~15:30, 약 390개)
            Columns: ['일자', '시간', '시가', '고가', '저가', '종가', '거래량']

        Example:
            >>> api.get_daily_minute_chart_data("005930", "20251001")
            >>> # 2025년 10월 1일의 삼성전자 전체 분봉 데이터 반환 (09:00~15:30)
        """
        # 날짜 형식 변환
        if isinstance(target_date, datetime):
            date_str = target_date.strftime("%Y%m%d")
        else:
            date_str = target_date

        logger.info(f"📅 과거 전체 분봉 조회 시작: {stock_code}, 날짜={date_str}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 시간 구간 설정 (3개 구간으로 분할)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        time_segments = [
            '110000',  # 09:00 ~ 11:00 (120분)
            '130000',  # 11:00 ~ 13:00 (120분)
            '153000',  # 13:00 ~ 15:30 (150분)
        ]

        all_data = []
        url = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
        tr_id = 'FHKST03010230'

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 각 시간 구간별로 API 호출
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for idx, end_time in enumerate(time_segments, 1):
            params = {
                'FID_ETC_CLS_CODE': '',
                'FID_COND_MRKT_DIV_CODE': 'J',
                'FID_INPUT_ISCD': stock_code,
                'FID_INPUT_DATE_1': date_str,
                'FID_INPUT_HOUR_1': end_time,  # 구간 종료 시간
                'FID_PW_DATA_INCU_YN': 'Y',
                'FID_FAKE_TICK_INCU_YN': 'N'
            }

            logger.info(f"  📡 구간 {idx}/3 호출: ~ {end_time[:2]}:{end_time[2:4]}")

            response = self._url_fetch(url, tr_id, params)

            if response is None or not response.is_ok():
                logger.warning(f"  ⚠️ 구간 {idx} 호출 실패: {end_time}")
                continue

            try:
                output2 = response.get_body().output2
                if output2:
                    all_data.extend(output2)
                    logger.info(f"  ✅ 구간 {idx} 수신: {len(output2)}개")
                else:
                    logger.warning(f"  ⚠️ 구간 {idx} 데이터 없음")
            except Exception as e:
                logger.error(f"  ❌ 구간 {idx} 파싱 실패: {e}")
                continue

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 데이터 병합 및 중복 제거
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if not all_data:
            logger.warning(f"❌ 전체 데이터 수집 실패: {stock_code}, {date_str}")
            return pd.DataFrame()

        try:
            # DataFrame 변환
            df = pd.DataFrame(all_data)

            target_columns = [
                'stck_bsop_date',   # 영업일자
                'stck_cntg_hour',   # 체결시간
                'stck_oprc',        # 시가
                'stck_hgpr',        # 고가
                'stck_lwpr',        # 저가
                'stck_prpr',        # 종가
                'cntg_vol',         # 거래량
            ]

            output_columns = ['일자', '시간', '시가', '고가', '저가', '종가', '거래량']

            df = df[target_columns]
            df[target_columns[2:]] = df[target_columns[2:]].apply(pd.to_numeric)
            df.rename(columns=dict(zip(target_columns, output_columns)), inplace=True)

            # 중복 제거 (같은 시간대가 여러 구간에 포함될 수 있음)
            df = df.drop_duplicates(subset=['시간'], keep='first')

            # 시간 순으로 정렬 (과거 → 최신)
            df = df.sort_values(by='시간', ascending=True).reset_index(drop=True)

            logger.info(f"✅ 전체 분봉 수집 완료: {stock_code}, {date_str}, 총 {len(df)}개")
            if len(df) > 0:
                logger.info(f"   시간 범위: {df.iloc[0]['시간']} ~ {df.iloc[-1]['시간']}")

            return df

        except Exception as e:
            logger.error(f"❌ 데이터 병합 실패: {stock_code}, {date_str}, 오류: {e}")
            return pd.DataFrame()

    def get_daily_price_chart(self, stock_code, start_date, end_date, period_code='D'):
        """
        일/주/월봉 차트 데이터 조회
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice
        """
        url = '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
        tr_id = 'FHKST03010100'

        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': start_date,
            'FID_INPUT_DATE_2': end_date,
            'FID_PERIOD_DIV_CODE': period_code,
            'FID_ORG_ADJ_PRC': '1',  # 수정주가 반영
        }

        t1 = self._url_fetch(url, tr_id, params)
        output_columns = ['일자', '시가', '고가', '저가', '종가', '거래량']
        if t1 is None:
            return pd.DataFrame(columns=output_columns)
        
        try:
            output2 = t1.get_body().output2
        except Exception as e:
            logger.info(f"Exception: {e}, t1: {t1}")
            return pd.DataFrame(columns=output_columns)

        if t1 is not None and t1.is_ok() and output2:
            df = pd.DataFrame(output2)
            target_columns = [
                'stck_bsop_date',
                'stck_oprc',
                'stck_hgpr',
                'stck_lwpr',
                'stck_clpr',
                'acml_vol',
            ]
            
            df = df[target_columns]
            df[target_columns[1:]] = df[target_columns[1:]].apply(pd.to_numeric)
            column_name_map = dict(zip(target_columns, output_columns))
            df.rename(columns=column_name_map, inplace=True)
            return df[::-1].reset_index(drop=True)
        else:
            return pd.DataFrame(columns=output_columns)

    def get_current_price(self, stock_code: str):
        """
        현재가 조회 (KIS-06)
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-price
        """
        url = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
        }
        t1 = self._url_fetch(url, tr_id, params)
        if t1 and t1.is_ok():
            return t1.get_body().output
        return None

    def get_orderable_amount(self, stock_code: str, price: int):
        """
        매수 가능 조회 (KIS-07)
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/inquire-psbl-order
        """
        url = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
        tr_id = "TTTC8908R"
        params = {
            "CANO": self.stock_account_number,
            "ACNT_PRDT_CD": "01",
            "PDNO": stock_code,
            "ORD_UNPR": str(price),
            "ORD_DVSN": "01", # 지정가
            "CMA_EVLU_AMT_ICLD_YN": "N",
            "OVRS_ICLD_YN": "N"
        }
        t1 = self._url_fetch(url, tr_id, params)
        if t1 and t1.is_ok():
            return t1.get_body().output
        return None


    def get_index_current_price(self, market_code: str, index_code: str):
        """국내 업종/지수 현재가 조회 (inquire-price)"""
        url = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHPUP02100000"

        params = {
            "fid_cond_mrkt_div_code": market_code,  # "U": KOSPI, "J": KOSDAQ 등
            "fid_input_iscd": index_code
        }

        response = self._url_fetch(url, tr_id, params)

        if not response:
            return None

        body = response.get_body()
        output = getattr(body, "output", None)
        meta = {
            "rt_cd": getattr(body, "rt_cd", None),
            "msg_cd": getattr(body, "msg_cd", None),
            "msg1": getattr(body, "msg1", None),
        }

        return {
            "ok": response.is_ok(),
            "output": output,
            "meta": meta,
        }


    def get_overseas_price_periodic(
        self,
        market_code: str,
        item_code: str,
        start_date: str,
        end_date: str,
        period_code: str = "D",
    ):
        """해외 지수/환율 기간별 시세 조회 (price-periodic)"""
        url = "/uapi/overseas-price/v1/quotations/price-periodic"
        tr_id = "FHKST03030100"

        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_iscd": item_code,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": period_code,
        }

        response = self._url_fetch(url, tr_id, params)

        if not response:
            return None

        body = response.get_body()
        meta = {
            "rt_cd": getattr(body, "rt_cd", None),
            "msg_cd": getattr(body, "msg_cd", None),
            "msg1": getattr(body, "msg1", None),
        }

        output1 = getattr(body, "output1", None)
        output2 = getattr(body, "output2", None)

        return {
            "ok": response.is_ok(),
            "output1": output1,
            "output2": output2,
            "meta": meta,
        }

    def get_overseas_daily_chartprice(
        self,
        market_code: str,
        item_code: str,
        start_date: str,
        end_date: str,
        period_code: str = "D",
    ):
        """해외 종목/지수/환율 기간별 시세 조회 (inquire-daily-chartprice)"""
        url = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"
        tr_id = "FHKST03030100"

        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_iscd": item_code,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": period_code,
        }

        response = self._url_fetch(url, tr_id, params)

        if not response:
            return None

        body = response.get_body()
        meta = {
            "rt_cd": getattr(body, "rt_cd", None),
            "msg_cd": getattr(body, "msg_cd", None),
            "msg1": getattr(body, "msg1", None),
        }

        output1 = getattr(body, "output1", None)
        output2 = getattr(body, "output2", None)

        return {
            "ok": response.is_ok(),
            "output1": output1,
            "output2": output2,
            "meta": meta,
        }


    def get_daily_ccld(self, start_date: str, end_date: str, stock_code: str = "", sll_buy_dvsn_cd: str = "00"):
        """
        일별 주문 체결 조회 (KIS-04)
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/inquire-daily-ccld
        """
        url = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        tr_id = "TTTC8001R"
        params = {
            "CANO": self.stock_account_number,
            "ACNT_PRDT_CD": "01",
            "INQR_STRT_DT": start_date,
            "INQR_END_DT": end_date,
            "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd, # 00:전체, 01:매도, 02:매수
            "INQR_DVSN": "00", # 종목별
            "PDNO": stock_code,
            "CCLD_DVSN": "00", # 00:전체, 01:체결, 02:미체결
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        t1 = self._url_fetch(url, tr_id, params)
        output_columns = ['주문일자', '주문번호', '원주문번호', '매매구분', '종목코드', '종목명', '주문수량', '주문단가', '총체결수량', '평균체결가', '총체결금액']
        if t1 is None:
            return pd.DataFrame(columns=output_columns)

        try:
            output1 = t1.get_body().output1
        except Exception as e:
            logger.info(f"Exception: {e}, t1: {t1}")
            return pd.DataFrame(columns=output_columns)

        if t1.is_ok() and output1:
            df = pd.DataFrame(output1)
            target_columns = ['ord_dt', 'odno', 'orgn_odno', 'ord_dvsn_name', 'pdno', 'prdt_name', 'ord_qty', 'ord_unpr', 'tot_ccld_qty', 'avg_prvs', 'tot_ccld_amt']
            df = df[target_columns]
            df[target_columns[6:]] = df[target_columns[6:]].apply(pd.to_numeric)
            column_name_map = dict(zip(target_columns, output_columns))
            df.rename(columns=column_name_map, inplace=True)
            return df
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

    def cancel_order(self, org_branch_code: str, org_order_no: str, order_qty: int):
        """주문 취소 (KIS-03)"""
        return self._revise_or_cancel(org_branch_code, org_order_no, "02", order_qty, 0)

    def revise_order(self, org_branch_code: str, org_order_no: str, order_qty: int, order_price: int):
        """주문 정정 (KIS-03)"""
        return self._revise_or_cancel(org_branch_code, org_order_no, "01", order_qty, order_price)

    def _revise_or_cancel(self, org_branch_code: str, org_order_no: str, division_code: str, order_qty: int, order_price: int):
        """주문 정정/취소 공통 로직"""
        url = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
        # 취소: TTTC0801U, 정정: TTTC0803U
        tr_id = "TTTC0801U" if division_code == "02" else "TTTC0803U"
        
        params = {
            "CANO": self.stock_account_number,
            "ACNT_PRDT_CD": "01",
            "KRX_FWDG_ORD_ORGNO": org_branch_code,
            "ORGN_ODNO": org_order_no,
            "ORD_DVSN": "01", # 지정가
            "RVSE_CNCL_DVSN_CD": division_code, # 01:정정, 02:취소
            "ORD_QTY": str(order_qty),
            "ORD_UNPR": str(order_price),
            "QTY_ALL_ORD_YN": "Y" if order_qty > 0 else "N",
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request=True, use_hash=True)
        
        if t1 and t1.is_ok():
            return t1
        elif t1:
            t1.print_error()
        return None

    def stock_order(self, stock_code, order_qty, order_price, prd_code="01", buy_flag=True, order_type="00"):
        """주식 실제 매매를 위한 주문"""
        url = "/uapi/domestic-stock/v1/trading/order-cash"
        tr_id = "TTTC0802U" if buy_flag else "TTTC0801U" # 정정: TTTC0802U는 매수, TTTC0801U는 매도
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
                logger.error(f"Request Params: {params}")

                # Try to parse JSON response for more details
                try:
                    error_json = response.json()
                    logger.error(f"Response JSON: {error_json}")
                    if 'msg1' in error_json and error_json['msg1']:
                        logger.error(f"API Error Message: {error_json['msg1']}")
                except:
                    pass

                return None
                
        except Exception as e:
            logger.info(f"URL exception: {e}")
            # 예외 발생 시에도 로그 기록
            if response is None:
                self._write_api_log(tr_id, url if 'url' in locals() else api_url, params, None, is_post_request)
            return None

    def __str__(self):
        return f"KoreaInvestAPI(config={self.config})"
