# 주문 처리 프로세스 모듈
# rsimacd_trading.py에서 이동된 send_tr_process 함수

from multiprocessing import Queue
import time
from loguru import logger
import talib as ta

def send_tr_process(korea_invest_api, tr_req_queue: Queue, tr_result_queue: Queue):
    """
    주문 처리 프로세스 함수
    큐에서 주문 요청을 받아 처리하고 결과를 반환
    
    Args:
        korea_invest_api: 증권사 API 인스턴스
        tr_req_queue: 주문 요청 큐
        tr_result_queue: 주문 결과 큐
    """
    while True:
        try:
            data = tr_req_queue.get()
            time.sleep(0.01)
            logger.debug(f"data: {data}")
            
            if data['action_id'] == "종료":
                logger.info(f"Order Process End!")
                break
                
            elif data['action_id'] == "매수":
                korea_invest_api.buy_order(
                    data['종목코드'], 
                    order_qty=data['매수주문수량'], 
                    order_price=data['매수주문가'],
                    order_type=data['주문유형']
                )
                logger.debug(f"Buy Order Sent! {data}")
                
            elif data['action_id'] == "매도":
                korea_invest_api.sell_order(
                    data['종목코드'], 
                    order_qty=data['매도주문수량'], 
                    order_price=data['매도주문가'],
                    order_type=data['주문유형']
                )
                logger.debug(f"Sell Order Sent! {data}")
                
            elif data['action_id'] == "정정":
                korea_invest_api.revise_order(
                    data['종목코드'], 
                    order_qty=data['정정주문수량'], 
                    order_price=data['정정주문가'],
                    order_type=data['주문유형']
                )
                logger.debug(f"Revise Order Sent! {data}")
                
            elif data['action_id'] == "취소":
                korea_invest_api.cancel_order(
                    data['종목코드'], 
                    order_qty=data['취소주문수량'], 
                    order_price=data['취소주문가'],
                    order_type=data['주문유형']
                )
                logger.debug(f"Cancel Order Sent! {data}")
            
            elif data['action_id'] == "1분봉조회":
                logger.info("1분봉조회 요청 처리 시작")
                df = korea_invest_api.get_minute_chart_data(data['종목코드'])

                # RSI/MACD 계산 (현재는 여기서 처리, 향후 TradingEngine으로 이동 예정)
                df['EMA_fast'] = df['종가'].ewm(span=9, adjust=False).mean()
                df['EMA_slow'] = df['종가'].ewm(span=18, adjust=False).mean()
                df['MACD'] = df['EMA_fast'] - df['EMA_slow']
                df['MACD_signal'] = df['MACD'].ewm(span=6, adjust=False).mean()
                df['RSI'] = ta.RSI(df['종가'], timeperiod=14)

                tr_result_queue.put(
                    dict(
                        action_id='1분봉조회',
                        df=df,
                        종목코드=data['종목코드'],
                    )
                )
                
            elif data['action_id'] == "계좌조회":
                logger.info("계좌조회 요청 처리 시작")
                total_balance, per_code_balance_df = korea_invest_api.get_acct_balance()
                logger.info(f"계좌조회 API 호출 완료 - 총잔고: {total_balance}, 보유종목수: {len(per_code_balance_df) if per_code_balance_df is not None else 0}")
                
                result_data = dict(
                    action_id="계좌조회",
                    total_balance=total_balance,
                    per_code_balance_df=per_code_balance_df
                )
                tr_result_queue.put(result_data)
                logger.info(f"계좌조회 결과를 큐에 저장 완료 - 총잔고: {total_balance}, DataFrame 타입: {type(per_code_balance_df)}")

            else:
                logger.debug(f"Unknown Action! {data}")

        except Exception as e:
            logger.exception(e)
            break