"""
한국투자증권 API 서비스
기존 utils.py의 KoreaInvestAPI를 FastAPI와 통합
"""

import sys
import os
import pandas as pd
import asyncio
from functools import partial
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta

from pydantic import BaseModel
from app.models.schemas import ChartCandle
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger

try:
    from brokers.korea_investment.ki_api import KoreaInvestAPI
    from brokers.korea_investment.ki_env import KoreaInvestEnv
except ImportError as e:
    logger.error(f"brokers.korea_investment 모듈 임포트 실패: {e}")
    # 임시 더미 클래스들
    class KoreaInvestAPI:
        def __init__(self, *args, **kwargs):
            pass
    class KoreaInvestEnv:
        def __init__(self, *args, **kwargs):
            pass


class MarketIndexData(BaseModel):
    index_code: str
    market_code: str
    current: float
    change: float
    change_rate: float


class KoreaInvestAPIService:
    """한국투자증권 API 서비스 래퍼 클래스"""
    
    def __init__(self, settings):
        self.settings = settings
        self.api_instance = None
        self.is_connected = False
        self.last_error = None
        self.last_raw_response: Optional[Dict[str, Any]] = None
        self.cached_indices: Dict[str, Dict[str, Any]] = {}
        
        # 비동기 실행을 위한 executor
        self.executor = None
        
        self._initialize_api()
    
    def _initialize_api(self):
        """API 인스턴스 초기화"""
        try:
            # 기존 config.yaml 형태의 설정을 dict로 변환
            config = {
                'api_key': self.settings.KI_API_KEY,
                'api_secret_key': self.settings.KI_SECRET_KEY,
                'stock_account_number': self.settings.KI_ACCOUNT_NUMBER,
                'htsid': self.settings.KI_HTSID,
                'custtype': self.settings.KI_CUSTTYPE,
                'is_paper_trading': self.settings.KI_IS_PAPER_TRADING,
                'my_agent': self.settings.KI_USER_AGENT,
                'url': self.settings.KI_API_URL,
                'websocket_url': self.settings.KI_WEBSOCKET_URL,
                'paper_url': self.settings.KI_PAPER_URL,
                'paper_websocket_url': self.settings.KI_PAPER_WEBSOCKET_URL,
                'api_approval_key': self.settings.KI_API_APPROVAL_KEY,
                'access_tocken': self.settings.KI_ACCESS_TOKEN,
                'websocket_approval_key': self.settings.KI_WEBSOCKET_APPROVAL_KEY,
                'using_url': self.settings.KI_USING_URL,
                'account_access_token': self.settings.KI_ACCOUNT_ACCESS_TOKEN
            }
            
            # 환경 설정 초기화
            env_cls = KoreaInvestEnv(config)
            base_headers = env_cls.get_base_headers()
            full_config = env_cls.get_full_config()
            
            # API 인스턴스 생성
            self.api_instance = KoreaInvestAPI(full_config, base_headers=base_headers)
            self.is_connected = True
            
            logger.info("한국투자증권 API 서비스가 초기화되었습니다.")
            
        except Exception as e:
            self.last_error = str(e)
            self.is_connected = False
            logger.error(f"한국투자증권 API 초기화 실패: {e}")
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """동기 함수를 비동기로 실행"""
        loop = asyncio.get_running_loop()
        if kwargs:
            func = partial(func, *args, **kwargs)
            args = ()
        return await loop.run_in_executor(self.executor, func, *args)
    
    async def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """계좌 잔고 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            # 동기 함수를 비동기로 실행하고 APIResponse 객체를 받음
            api_response = await self._run_in_executor(self.api_instance.get_acct_balance)

            if not api_response or not api_response.is_ok():
                logger.error(f"계좌 잔고 API 호출 실패: {api_response.get_body() if api_response else 'No response'}")
                return None

            body = api_response.get_body()
            output1 = getattr(body, 'output1', [])  # 포지션 목록
            output2 = getattr(body, 'output2', [{}])[0]  # 계좌 요약

            # 현금 및 총 평가금액 추출
            total_value = int(output2.get('tot_evlu_amt', 0) or 0)
            available_cash = int(output2.get('dnca_tot_amt', 0) or 0)

            positions = []
            total_unrealized_pnl = 0

            if output1:
                df = pd.DataFrame(output1)
                column_mapping = {
                    'pdno': '종목코드',
                    'prdt_name': '종목명',
                    'hldg_qty': '보유수량',
                    'pchs_avg_pric': '매입단가',
                    'evlu_pfls_rt': '수익률',
                    'prpr': '현재가',
                    'evlu_amt': '평가금액',
                    'pchs_amt': '매입금액',
                    'bfdy_cprs_icdc': '전일대비',
                    'ord_psbl_qty': '매도가능수량',
                    'fltt_rt': '전일대비 등락률'
                }
                df = df.rename(columns=column_mapping)

                for _, row in df.iterrows():
                    current_price = int(float(row.get('현재가', 0) or 0))
                    avg_price = int(float(row.get('매입단가', 0) or 0))
                    quantity = int(float(row.get('보유수량', 0) or 0))
                    
                    # 손익 재계산
                    unrealized_pnl = (current_price - avg_price) * quantity
                    total_unrealized_pnl += unrealized_pnl

                    positions.append({
                        "stock_code": str(row.get("종목코드", "")),
                        "stock_name": str(row.get("종목명", "")),
                        "quantity": quantity,
                        "sellable_quantity": int(float(row.get("매도가능수량", 0) or 0)),
                        "avg_price": avg_price,
                        "current_price": current_price,
                        "unrealized_pnl": unrealized_pnl,
                        "profit_rate": float(row.get("수익률", 0.0) or 0.0),
                        "day_change": int(float(row.get("전일대비", 0) or 0)),
                        "day_change_rate": float(row.get("전일대비 등락률", 0.0) or 0.0)
                    })
            else:
                df = pd.DataFrame() # output1이 비어있을 경우 빈 데이터프레임 생성
            
            return {
                "total_value": total_value,
                "available_cash": available_cash,
                "total_unrealized_pnl": total_unrealized_pnl,
                "positions": positions,
                "dataframe": df  # dataframe 키 다시 추가
            }


            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"계좌 잔고 조회 실패: {e}")
        
        return None
    
    async def buy_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Optional[Any]:
        """매수 주문 (비동기) - APIResponse 객체를 직접 반환하도록 수정"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            # self.api_instance.buy_order가 APIResponse 객체를 반환한다고 가정
            api_response = await self._run_in_executor(
                self.api_instance.buy_order, 
                stock_code, order_qty, order_price, order_type
            )
            return api_response
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"매수 주문 실패: {e}", exc_info=True)
            return None
    
    async def sell_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Optional[Any]:
        """매도 주문 (비동기) - APIResponse 객체를 직접 반환하도록 수정"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            # self.api_instance.sell_order가 APIResponse 객체를 반환한다고 가정
            api_response = await self._run_in_executor(
                self.api_instance.sell_order,
                stock_code, order_qty, order_price, order_type
            )
            return api_response
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"매도 주문 실패: {e}", exc_info=True)
            return None

    async def inquire_pending_orders(self, stock_code: str = "") -> Optional[pd.DataFrame]:
        """미체결 내역 조회 (TR_ID: TTTC8001R, CCLD_DVSN: 02)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        try:
            # get_daily_ccld를 미체결(02) 조건으로 호출
            result_df = await self._run_in_executor(
                self.api_instance.get_daily_ccld,
                start_date=datetime.now().strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                stock_code=stock_code,
                sll_buy_dvsn_cd="00", # 전체
                ccld_dvsn="02" # 미체결
            )
            return result_df
        except Exception as e:
            logger.error(f"미체결 내역 조회 실패: {e}", exc_info=True)
            return None

    async def inquire_order_history(self, start_date: str, end_date: str, stock_code: str = "") -> Optional[pd.DataFrame]:
        """기간별 체결 내역 조회 (TR_ID: TTTC8001R, CCLD_DVSN: 01)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        stock_code = ""

        try:
            # --- Gemini Modification Start ---
            # API 호출 파라미터를 명확하게 로깅
            api_params = {
                "start_date": start_date,
                "end_date": end_date,
                "stock_code": stock_code,
                "sll_buy_dvsn_cd": "00", # 전체
                "ccld_dvsn": "01" # 체결
            }
            logger.info(f"체결 내역 조회를 위해 get_daily_ccld 호출. 파라미터: {api_params}")
            # --- Gemini Modification End ---

            # get_daily_ccld를 체결(01) 조건으로 호출
            result_df = await self._run_in_executor(
                self.api_instance.get_daily_ccld,
                start_date=start_date,
                end_date=end_date,
                stock_code=stock_code,
                sll_buy_dvsn_cd="00", # 전체
                ccld_dvsn="01" # 체결
            )
            
            # --- Raw Logging Start ---
            if isinstance(result_df, pd.DataFrame) and not result_df.empty:
                try:
                    raw_df = result_df.copy()
                    raw_cols = list(raw_df.columns)
                    # 핵심 후보 컬럼 위주로 샘플 구성
                    raw_key_cols = [
                        c for c in [
                            "pdno", "prdt_name", "sll_buy_dvsn_cd",
                            "ord_qty", "rmn_qty", "tot_ccld_qty",
                            "ord_unpr", "avg_prvs", "tot_ccld_amt",
                            "ord_dt", "ord_tmd", "ccld_tmd",
                            "odno", "orgn_odno", "brnno",
                        ] if c in raw_cols
                    ]
                    raw_sample = raw_df[raw_key_cols].head(5).to_dict(orient="records") if raw_key_cols else raw_df.head(5).to_dict(orient="records")
                    dtypes_map = {c: str(t) for c, t in raw_df.dtypes.to_dict().items()}
                    logger.info(
                        f"체결 내역 원본 응답 (샘플) | rows={len(raw_df)} | columns={raw_cols} | dtypes={dtypes_map} | sample={raw_sample}"
                    )
                except Exception as raw_log_err:
                    logger.warning(f"원본 응답 로깅 중 경고: {raw_log_err}")
            # --- Raw Logging End ---

            # --- Normalization Start ---
            # 응답 정규화: 수량/금액/시간 필드의 포맷을 정리하여 후속 파싱 오류(N/A, 0) 방지
            if isinstance(result_df, pd.DataFrame) and not result_df.empty:
                try:
                    df = result_df.copy()
                    # 1) 컬럼 이름 안정화 (문자열화 및 공백 제거)
                    df.columns = [str(c).strip() for c in df.columns]

                    # 2) 숫자 필드에서 콤마 제거 후 정수/실수 변환
                    numeric_like_columns = [
                        "ord_qty", "rmn_qty", "tot_ccld_qty", "ord_unpr", "avg_prvs",
                        "tot_ccld_amt", "fee", "tax"
                    ]
                    for col in numeric_like_columns:
                        if col in df.columns:
                            df[col] = (
                                df[col]
                                .astype(str)
                                .str.replace(",", "", regex=False)
                                .str.replace(" ", "", regex=False)
                            )
                            # 가격/금액은 정수로 취급 (원 단위)
                            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

                    # 3) 시간 필드 zero-pad (HHMMSS), "0" 또는 공백은 결측 처리
                    time_columns = ["ord_tmd", "ccld_tmd", "infm_tmd"]
                    for tcol in time_columns:
                        if tcol in df.columns:
                            df[tcol] = df[tcol].apply(
                                lambda v: None
                                if v is None or str(v).strip() in ("", "0", "000000")
                                else str(v).strip().zfill(6)
                            )

                    # 4) 이상한/깨진 텍스트 정리 (간헐적 인코딩 이슈 예방 - 숫자만 남김)
                    # 체결금액/체결수량 필드에 비숫자 문자가 섞여 있을 수 있음
                    cleanup_targets = {"tot_ccld_amt", "tot_ccld_qty", "avg_prvs"}
                    for col in cleanup_targets:
                        if col in df.columns and df[col].dtype == object:
                            df[col] = df[col].astype(str).str.replace(r"[^0-9]", "", regex=True)
                            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

                    # 5) 정규화된 DataFrame을 반환용으로 교체
                    result_df = df

                    # 샘플 로깅 (상위 5개, 핵심 필드만)
                    sample_cols = [
                        c for c in [
                            "pdno", "prdt_name", "sll_buy_dvsn_cd",
                            "ord_qty", "rmn_qty", "tot_ccld_qty",
                            "ord_unpr", "avg_prvs", "tot_ccld_amt",
                            "ord_dt", "ord_tmd", "ccld_tmd",
                            "odno", "orgn_odno", "brnno",
                        ] if c in result_df.columns
                    ]
                    dtypes_map_norm = {c: str(t) for c, t in result_df.dtypes.to_dict().items()}
                    logger.info(
                        f"체결 내역 응답 정규화 완료 (샘플) | rows={len(result_df)} | columns={list(result_df.columns)} | dtypes={dtypes_map_norm} | sample={result_df[sample_cols].head(5).to_dict(orient='records') if sample_cols else []}"
                    )
                except Exception as norm_err:
                    logger.warning(f"체결 내역 정규화 중 경고: {norm_err}", exc_info=True)
            else:
                logger.warning("get_daily_ccld 응답: 데이터프레임이 비어있거나 유효하지 않음.")
            # --- Normalization End ---

            row_count = len(result_df) if isinstance(result_df, pd.DataFrame) else None
            logger.info(
                "기간별 체결 내역 조회 성공",
                extra={
                    "stock_code": stock_code,
                    "start_date": start_date,
                    "end_date": end_date,
                    "row_count": row_count,
                }
            )
            return result_df
        except Exception as e:
            logger.error(f"기간별 체결 내역 조회 실패: {e}", exc_info=True)
            return None

    async def modify_order(self, branch_code: str, org_order_no: str, new_quantity: int, new_price: int) -> Optional[Any]:
        """주문 정정 (TR_ID: TTTC0803U)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        try:
            # ki_api.revise_order 호출
            result = await self._run_in_executor(
                self.api_instance.revise_order,
                org_branch_code=branch_code,
                org_order_no=org_order_no,
                order_qty=new_quantity,
                order_price=new_price
            )
            return result
        except Exception as e:
            logger.error(f"주문 정정 실패: {e}", exc_info=True)
            return None

    async def cancel_order(self, branch_code: str, org_order_no: str, cancel_quantity: int) -> Optional[Any]:
        """주문 취소 (TR_ID: TTTC0801U)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        try:
            # ki_api.cancel_order 호출
            result = await self._run_in_executor(
                self.api_instance.cancel_order,
                org_branch_code=branch_code,
                org_order_no=org_order_no,
                order_qty=cancel_quantity
            )
            return result
        except Exception as e:
            logger.error(f"주문 취소 실패: {e}", exc_info=True)
            return None
    
    async def get_minute_chart_data(self, stock_code: str) -> Optional[List[ChartCandle]]:
        """1분봉 차트 데이터 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            logger.debug(f"Calling ki_api method: {self.api_instance.get_minute_chart_data.__name__}")
            df = await self._run_in_executor(
                self.api_instance.get_minute_chart_data,
                stock_code
            )

            if df is None or df.empty:
                return []

            # 중복 제거: 일자와 시간이 같은 데이터는 첫 번째만 유지
            df = df.drop_duplicates(subset=['일자', '시간'], keep='first')
            logger.info(f"분봉 데이터 중복 제거 완료: {len(df)}개")

            chart_candles: List[ChartCandle] = []
            for _, row in df.iterrows():
                try:
                    # '일자' (YYYYMMDD)와 '시간' (HHMMSS)을 결합하여 ISO 형식의 타임스탬프 생성
                    date_str = str(row['일자'])
                    time_str = str(row['시간']).zfill(6) # HHMMSS 형식으로 6자리 채우기
                    # KIS API의 시간은 000000 ~ 235959 이므로, 240000은 다음 날 000000으로 처리
                    if time_str == "240000":
                        # 다음 날 00시 00분 00초로 처리 (날짜도 하루 증가)
                        dt_object = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                        timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")
                    else:
                        dt_object = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                        timestamp_iso = dt_object.isoformat()

                    candle = ChartCandle(
                        timestamp=timestamp_iso,
                        open=float(row['시가']),
                        high=float(row['고가']),
                        low=float(row['저가']),
                        close=float(row['종가']),
                        volume=int(row['거래량'])
                    )
                    chart_candles.append(candle)
                except Exception as e:
                    logger.warning(f"분봉 데이터 변환 중 오류 발생: {e}, 데이터: {row}")
                    continue
            
            return chart_candles
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"차트 데이터 조회 실패: {e}")
            return None

    async def get_daily_minute_chart_data(self, stock_code: str, target_date: datetime) -> Optional[List[ChartCandle]]:
        """과거 특정 날짜의 1분봉 차트 데이터 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None

        try:
            logger.info(f"과거 분봉 데이터 조회: {stock_code}, {target_date.strftime('%Y-%m-%d')}")
            df = await self._run_in_executor(
                self.api_instance.get_daily_minute_chart_data,
                stock_code,
                target_date
            )

            if df is None or df.empty:
                logger.warning(f"과거 분봉 데이터 없음: {stock_code}, {target_date.strftime('%Y-%m-%d')}")
                return []

            # 중복 제거
            df = df.drop_duplicates(subset=['일자', '시간'], keep='first')
            logger.info(f"과거 분봉 데이터 중복 제거 완료: {len(df)}개")

            chart_candles: List[ChartCandle] = []
            for _, row in df.iterrows():
                try:
                    date_str = str(row['일자'])
                    time_str = str(row['시간']).zfill(6)

                    if time_str == "240000":
                        dt_object = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                        timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")
                    else:
                        dt_object = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                        timestamp_iso = dt_object.isoformat()

                    candle = ChartCandle(
                        timestamp=timestamp_iso,
                        open=float(row['시가']),
                        high=float(row['고가']),
                        low=float(row['저가']),
                        close=float(row['종가']),
                        volume=int(row['거래량'])
                    )
                    chart_candles.append(candle)
                except Exception as e:
                    logger.warning(f"과거 분봉 데이터 변환 중 오류: {e}")
                    continue

            logger.info(f"✅ 과거 분봉 데이터 변환 완료: {len(chart_candles)}개 캔들")
            return chart_candles

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"과거 차트 데이터 조회 실패: {e}")
            return None

    async def get_minute_chart_data_from(
        self,
        stock_code: str,
        start_time: str,  # HHMMSS 형식
        target_date: Optional[datetime] = None  # ✅ 추가: 대상 날짜
    ) -> Optional[List[ChartCandle]]:
        """
        특정 시간부터 현재까지 분봉 데이터 조회 (Gap-fill 최적화)

        Args:
            stock_code: 종목 코드 (예: "005930")
            start_time: 시작 시간 HHMMSS 형식 (예: "113000" = 11:30:00)
            target_date: 대상 날짜 (datetime). None이면 오늘

        Returns:
            start_time 이후 분봉 데이터만 반환

        Example:
            # 11:30부터 현재까지만 조회 (Gap-fill 최적화)
            candles = await service.get_minute_chart_data_from("005930", "113000", target_date)
        """
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None

        try:
            # ✅ 날짜 정보 추가
            date_str = target_date.strftime('%Y-%m-%d') if target_date else "오늘"
            logger.info(f"Gap 구간 조회: {stock_code}, {date_str} {start_time}~현재")

            # ✅ 오늘 날짜인지 과거 날짜인지 판단
            is_today = target_date is None or target_date.date() == datetime.now().date()

            if is_today:
                # 오늘 데이터: 기존 방식 (start_time 사용)
                func = partial(
                    self.api_instance.get_minute_chart_data,
                    stock_code,
                    start_time=start_time,  # 🔑 Gap 시작 시간
                    max_count=None
                )
                df = await self._run_in_executor(func)
            else:
                # ✅ 과거 날짜: get_daily_minute_chart_data 사용 후 시간 필터링
                logger.info(f"과거 날짜 Gap fill: {stock_code}, {target_date.strftime('%Y-%m-%d')}")
                df = await self._run_in_executor(
                    self.api_instance.get_daily_minute_chart_data,
                    stock_code,
                    target_date
                )

                # 시간 필터링: start_time 이후 데이터만
                if df is not None and not df.empty:
                    df['시간_int'] = df['시간'].astype(str).str.zfill(6).astype(int)
                    start_time_int = int(start_time)
                    df = df[df['시간_int'] >= start_time_int].drop(columns=['시간_int'])
                    logger.info(f"시간 필터링 완료: {start_time} 이후 {len(df)}개")

            if df is None or df.empty:
                logger.info(f"Gap 구간 데이터 없음: {stock_code}, {start_time}~")
                return []

            # 중복 제거: 일자와 시간이 같은 데이터는 첫 번째만 유지
            df = df.drop_duplicates(subset=['일자', '시간'], keep='first')
            logger.info(f"Gap 데이터 수집 완료: {len(df)}개 ({start_time}~현재)")

            # DataFrame → ChartCandle 변환
            chart_candles: List[ChartCandle] = []
            for _, row in df.iterrows():
                try:
                    date_str = str(row['일자'])
                    time_str = str(row['시간']).zfill(6)  # HHMMSS 형식으로 6자리 채우기

                    # KIS API의 시간은 000000 ~ 235959 이므로, 240000은 다음 날 000000으로 처리
                    if time_str == "240000":
                        dt_object = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                        timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")
                    else:
                        dt_object = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                        timestamp_iso = dt_object.isoformat()

                    candle = ChartCandle(
                        timestamp=timestamp_iso,
                        open=float(row['시가']),
                        high=float(row['고가']),
                        low=float(row['저가']),
                        close=float(row['종가']),
                        volume=int(row['거래량'])
                    )
                    chart_candles.append(candle)
                except Exception as e:
                    logger.warning(f"Gap 데이터 변환 중 오류 발생: {e}, 데이터: {row}")
                    continue

            return chart_candles

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Gap 구간 조회 실패: {stock_code}, {start_time}~, 오류: {e}")
            return None

    async def get_daily_minute_chart_data(
        self,
        stock_code: str,
        target_date
    ):
        """
        특정 날짜의 전체 분봉 데이터 조회 (과거 날짜용)
        
        Args:
            stock_code: 종목코드
            target_date: 조회 날짜 (datetime 또는 "YYYYMMDD")
        
        Returns:
            DataFrame: 해당 날짜의 전체 분봉 데이터
        """
        try:
            # 비동기 실행자를 통해 동기 메서드 호출
            result = await self._run_in_executor(
                self.api_instance.get_daily_minute_chart_data,
                stock_code,
                target_date
            )
            return result
        except Exception as e:
            logger.error(f"❌ 과거 분봉 데이터 조회 실패: {e}")
            return None

    async def get_daily_price_chart(self, stock_code: str, start_date: str, end_date: str, period_code: str = 'D') -> Optional[pd.DataFrame]:
        """일/주/월봉 차트 데이터 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            result = await self._run_in_executor(
                self.api_instance.get_daily_price_chart,
                stock_code,
                start_date,
                end_date,
                period_code
            )
            return result
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"일/주/월봉 차트 데이터 조회 실패: {e}")
            return None

    async def get_daily_chart_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[List[ChartCandle]]:
        """일봉 데이터를 조회하여 ChartCandle 리스트로 반환합니다."""
        logger.info(f"일봉 데이터 조회 시작: {stock_code}, 기간: {start_date}~{end_date}")
        df = await self.get_daily_price_chart(stock_code, start_date, end_date, 'D')

        if df is None or df.empty:
            logger.warning(f"API로부터 일봉 데이터를 받지 못함: {stock_code}")
            return []

        chart_candles: List[ChartCandle] = []
        for _, row in df.iterrows():
            try:
                # '일자' (YYYYMMDD)를 ISO 형식의 타임스탬프로 변환
                date_str = str(row['일자'])
                dt_object = datetime.strptime(date_str, "%Y%m%d")
                timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")

                candle = ChartCandle(
                    timestamp=timestamp_iso,
                    open=float(row['시가']),
                    high=float(row['고가']),
                    low=float(row['저가']),
                    close=float(row['종가']),
                    volume=int(row['거래량'])
                )
                chart_candles.append(candle)
            except Exception as e:
                logger.warning(f"일봉 데이터 변환 중 오류 발생: {e}, 데이터: {row}")
                continue
        
        logger.info(f"일봉 데이터 변환 완료: {len(chart_candles)}개 캔들")
        return chart_candles
    
    async def get_current_price(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """현재가 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            # 실제 현재가 조회 API 호출 (구체적 메서드명은 utils.py 확인 필요)
            # 임시로 기본 구조만 제공
            result = await self._run_in_executor(
                getattr(self.api_instance, 'get_current_price', lambda x: None),
                stock_code
            )
            
            if result:
                return {
                    "stock_code": stock_code,
                    "current_price": result.get("현재가", 0),
                    "change": result.get("전일대비", 0),
                    "change_rate": result.get("등락률", 0.0),
                    "volume": result.get("거래량", 0)
                }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"현재가 조회 실패: {e}")
        
        return None

    async def get_index_current_price(
        self,
        index_code: str,
        market_code: str = "U"
    ) -> Optional[MarketIndexData]:
        """업종/지수 현재가 조회 (비동기)"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None
        
        try:
            raw_result = await self._run_in_executor(
                self.api_instance.get_index_current_price,
                market_code,
                index_code
            )
            self.last_raw_response = raw_result

            if not raw_result:
                logger.warning(
                    f"지수 현재가 조회 결과가 비어 있습니다. market_code={market_code}, index_code={index_code}"
                )
                self.last_error = "Empty response"
                return None

            if isinstance(raw_result, dict):
                ok = raw_result.get("ok", True)
                output = raw_result.get("output")
                meta = raw_result.get("meta", {})
            else:
                ok = True
                output = raw_result
                meta = {}

            if not ok:
                self.last_error = meta.get("msg1") or "Non-success response"
                logger.warning(
                    f"지수 현재가 조회 비정상 응답: market_code={market_code}, index_code={index_code}, meta={meta}"
                )

            if not output:
                return None

            parsed = self._parse_index_response(output, market_code, index_code)

            if parsed:
                self.update_cached_index(
                    parsed.index_code,
                    parsed.market_code,
                    parsed.current,
                    parsed.change,
                    parsed.change_rate,
                    meta=meta,
                    raw=raw_result,
                )
                # logger.info(
                #     "지수 조회 성공",
                #     extra={
                #         "market_code": market_code,
                #         "index_code": index_code,
                #         "meta": meta,
                #         "values": parsed.model_dump(),
                #     }
                # )
            else:
                logger.error(
                    "지수 조회 실패",
                    extra={
                        "market_code": market_code,
                        "index_code": index_code,
                        "meta": meta,
                        "raw_response": raw_result,
                    }
                )

            return parsed
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"지수 현재가 조회 실패: {e}")
            return None


    async def get_overseas_index_price(
        self,
        index_code: str,
        market_code: str = "N",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period_code: str = "D",
    ) -> Optional[MarketIndexData]:
        """해외 지수/환율 기간 시세에서 최신 값을 추출"""
        if not self.is_connected or not self.api_instance:
            logger.error("API가 연결되지 않았습니다.")
            return None

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y%m%d")
            except ValueError:
                logger.warning(
                    f"end_date 형식이 잘못되어 현재 날짜로 대체합니다. end_date={end_date}"
                )
                end_dt = datetime.now()
                end_date = end_dt.strftime("%Y%m%d")
        else:
            end_dt = datetime.now()
            end_date = end_dt.strftime("%Y%m%d")

        if start_date is None:
            start_date = (end_dt - timedelta(days=30)).strftime("%Y%m%d")

        try:
            raw_result = await self._run_in_executor(
                self.api_instance.get_overseas_daily_chartprice,
                market_code,
                index_code,
                start_date,
                end_date,
                period_code,
            )

            if not raw_result:
                raw_result = await self._run_in_executor(
                    self.api_instance.get_overseas_price_periodic,
                    market_code,
                    index_code,
                    start_date,
                    end_date,
                    period_code,
                )

            self.last_raw_response = raw_result

            if not raw_result:
                self.last_error = "Empty response"
                logger.warning(
                    "해외 지수 조회 결과가 비어 있습니다.",
                    extra={
                        "market_code": market_code,
                        "index_code": index_code,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                )
                return None

            ok = raw_result.get("ok", True)
            meta = raw_result.get("meta", {}) or {}
            output = raw_result.get("output1")

            if not ok:
                self.last_error = meta.get("msg1") or "Non-success response"
                logger.warning(
                    "해외 지수 조회 비정상 응답",
                    extra={
                        "market_code": market_code,
                        "index_code": index_code,
                        "meta": meta,
                    }
                )

            if not output:
                self.last_error = "Empty output"
                logger.warning(
                    "해외 지수 조회 output1이 비어 있습니다.",
                    extra={
                        "market_code": market_code,
                        "index_code": index_code,
                        "meta": meta,
                    }
                )
                return None

            parsed = self._parse_overseas_index_response(output, market_code, index_code)

            if parsed:
                self.update_cached_index(
                    parsed.index_code,
                    parsed.market_code,
                    parsed.current,
                    parsed.change,
                    parsed.change_rate,
                    meta=meta,
                    raw=raw_result,
                )
                # logger.info(
                #     "해외 지수 조회 성공",
                #     extra={
                #         "market_code": market_code,
                #         "index_code": index_code,
                #         "meta": meta,
                #         "values": parsed.model_dump(),
                #         "start_date": start_date,
                #         "end_date": end_date,
                #         "period_code": period_code,
                #     }
                # )
            else:
                logger.error(
                    "해외 지수 조회 실패",
                    extra={
                        "market_code": market_code,
                        "index_code": index_code,
                        "meta": meta,
                        "raw_response": raw_result,
                        "start_date": start_date,
                        "end_date": end_date,
                        "period_code": period_code,
                    }
                )

            return parsed

        except Exception as e:
            self.last_error = str(e)
            logger.error(
                f"해외 지수 조회 실패: {e}",
                exc_info=True
            )
            return None


    def _parse_index_response(
        self,
        data: Dict[str, Any],
        market_code: str,
        index_code: str
    ) -> Optional[MarketIndexData]:
        """한국투자증권 지수 응답을 숫자 값으로 변환"""
        try:
            current_str = data.get("bstp_nmix_prpr")
            change_str = data.get("bstp_nmix_prdy_vrss")
            change_rate_str = data.get("bstp_nmix_prdy_ctrt")

            if current_str is None or change_str is None or change_rate_str is None:
                raise ValueError("필수 지수 필드가 누락되었습니다")

            current = float(str(current_str).replace(",", ""))
            change = float(str(change_str).replace(",", ""))
            change_rate = float(str(change_rate_str).replace(",", ""))

            return MarketIndexData(
                index_code=index_code,
                market_code=market_code,
                current=current,
                change=change,
                change_rate=change_rate,
            )

        except Exception as parse_error:
            logger.error(
                f"지수 응답 파싱 실패: {parse_error} (market_code={market_code}, index_code={index_code}, data={data})",
                exc_info=True
            )
            self.last_error = str(parse_error)
            return None

    def _extract_float(self, data: Dict[str, Any], keys: List[str]) -> Optional[float]:
        for key in keys:
            if key not in data:
                continue

            value = data.get(key)
            if value in (None, ""):
                continue

            try:
                return float(str(value).replace(",", ""))
            except (TypeError, ValueError):
                continue
        return None

    def _parse_overseas_index_response(
        self,
        data: Dict[str, Any],
        market_code: str,
        index_code: str
    ) -> Optional[MarketIndexData]:
        if not isinstance(data, dict):
            logger.error(
                f"해외 지수 응답 형식 오류: dict가 아님 (type={type(data)})",
                extra={"market_code": market_code, "index_code": index_code}
            )
            self.last_error = "Invalid response format"
            return None

        try:
            current = self._extract_float(
                data,
                [
                    "ovrs_nmix_prpr",
                    "ovrs_prod_prpr",
                    "now_pric1",
                    "t_rate",
                ],
            )

            previous = self._extract_float(
                data,
                [
                    "ovrs_nmix_prdy_clpr",
                    "p_rate",
                ],
            )

            change = self._extract_float(
                data,
                [
                    "ovrs_nmix_prdy_vrss",
                    "prdy_vrss",
                    "t_xdif",
                ],
            )

            change_rate = self._extract_float(
                data,
                [
                    "prdy_ctrt",
                    "ovrs_nmix_prdy_ctrt",
                    "t_xrat",
                ],
            )

            if current is None and market_code == "X":
                current = self._extract_float(data, ["t_rate"])

            if current is None:
                raise ValueError("필수 해외 지수 필드가 누락되었습니다")

            if change is None and current is not None and previous is not None:
                change = current - previous

            if change_rate is None and change is not None and previous not in (None, 0.0):
                try:
                    change_rate = (change / previous) * 100 if previous else 0.0
                except ZeroDivisionError:
                    change_rate = 0.0

            change = change if change is not None else 0.0
            change_rate = change_rate if change_rate is not None else 0.0

            return MarketIndexData(
                index_code=index_code,
                market_code=market_code,
                current=current,
                change=change,
                change_rate=change_rate,
            )

        except Exception as parse_error:
            logger.error(
                f"해외 지수 응답 파싱 실패: {parse_error} (market_code={market_code}, index_code={index_code}, data={data})",
                exc_info=True
            )
            self.last_error = str(parse_error)
            return None

    def get_last_raw_response(self) -> Optional[Dict[str, Any]]:
        """가장 최근 REST 지수 호출의 원본 응답"""
        return self.last_raw_response

    def update_cached_index(
        self,
        index_code: Optional[str],
        market_code: Optional[str],
        current: Optional[float],
        change: Optional[float],
        change_rate: Optional[float],
        meta: Optional[Dict[str, Any]] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        """WebSocket 등으로 수신한 지수 값을 캐시"""
        if not index_code:
            return

        self.cached_indices[index_code] = {
            "index_code": index_code,
            "market_code": market_code,
            "current": current,
            "change": change,
            "change_rate": change_rate,
            "meta": meta,
            "raw": raw,
            "timestamp": datetime.now().isoformat(),
        }

    def get_cached_index(self, index_code: str) -> Optional[Dict[str, Any]]:
        return self.cached_indices.get(index_code)


    
    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 확인"""
        return {
            "connected": self.is_connected,
            "last_error": self.last_error,
            "api_instance": self.api_instance is not None
        }
    
    async def reconnect(self) -> bool:
        """연결 재시도"""
        try:
            self._initialize_api()
            return self.is_connected
        except Exception as e:
            logger.error(f"재연결 실패: {e}")
            return False
    
    def __del__(self):
        """소멸자"""
        if self.executor:
            self.executor.shutdown(wait=False)

    async def get_index_chart_data(
        self,
        market_code: str,
        index_code: str,
        start_date: str,
        end_date: str,
        period_code: str = "D"
    ) -> Optional[pd.DataFrame]:
        """
        국내 지수 차트 데이터 조회 (비동기 래퍼)
        """
        if not self.is_connected or not self.api_instance:
            logger.error("API 연결 안됨")
            return None

        try:
            func = partial(
                self.api_instance.get_index_chart_data,
                market_code=market_code,
                index_code=index_code,
                start_date=start_date,
                end_date=end_date,
                period_code=period_code
            )
            df = await self._run_in_executor(func)
            return df
        except Exception as e:
            logger.error(f"지수 차트 조회 실패: {e}")
            return None

    async def get_trade_history(
        self,
        start_date: str,
        end_date: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        일별 체결 내역 조회 (비동기 래퍼)
        """
        if not self.is_connected or not self.api_instance:
            return None

        try:
            func = partial(
                self.api_instance.get_daily_ccld,
                start_date=start_date,
                end_date=end_date,
                stock_code="",
                sll_buy_dvsn_cd="00"
            )
            result = await self._run_in_executor(func)
            return result
        except Exception as e:
            logger.error(f"거래 내역 조회 실패: {e}")
            return None
