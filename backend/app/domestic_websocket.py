import json
import websockets
import asyncio
from multiprocessing import Queue
import queue
import time
from datetime import datetime

from loguru import logger
from app.core.logging_config import setup_logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64decode

# 성능 모니터링 임포트
from app.utils.queue_monitor import QueueMonitor
from app.utils.performance_metrics import get_global_metrics_collector


# 자식 프로세스에서도 중앙 로깅 설정 적용
setup_logging()


def aes_cbc_base64_dec(key, iv, cipher_text):
  """
  :param key = str type AES256 secret key value
  :param iv = str type AES256 initialize Vector
  :param cipher_text = str type Base64 encoded AES256 str
  :return: Base64-AES256 decodec str
  """
  cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
  return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size()))


def parse_hoga_json(json_data: dict) -> dict:
    """
    KIS API JSON 형식 호가 데이터 파싱
    
    Args:
        json_data: {
            "header": {"tr_id": "H0STASP0", "tr_key": "005930"},
            "body": {
                "askp1": "71800", "askp_rsqn1": "100", ...
                "bidp1": "71700", "bidp_rsqn1": "150", ...
                "last": "71700", "time": "180015", ...
            }
        }
    
    Returns:
        {
            "stock_code": "005930",
            "asks": [
                {"price": 71800, "quantity": 100, "order_count": 0},
                ...  # 10개
            ],
            "bids": [
                {"price": 71700, "quantity": 150, "order_count": 0},
                ...  # 10개
            ],
            "current_price": 71700,
            "timestamp": "2025-10-14T18:00:15",
            "market_data": {
                "open": 71000, "high": 72500, "low": 70500,
                "volume": 1234567, "value": 78900000000,
                "sign": "2", "change": 500, "drate": 0.70
            }
        }
    """
    body = json_data.get("body", {})
    header = json_data.get("header", {})
    stock_code = header.get("tr_key", "")
    
    # 매도호가 파싱 (askp1~10, askp_rsqn1~10)
    asks = []
    for i in range(1, 11):
        price = int(body.get(f"askp{i}", 0))
        quantity = int(body.get(f"askp_rsqn{i}", 0))
        asks.append({
            "price": price,
            "quantity": quantity,
            "order_count": 0  # KIS API에서 제공하지 않음
        })
    
    # 매수호가 파싱 (bidp1~10, bidp_rsqn1~10)
    bids = []
    for i in range(1, 11):
        price = int(body.get(f"bidp{i}", 0))
        quantity = int(body.get(f"bidp_rsqn{i}", 0))
        bids.append({
            "price": price,
            "quantity": quantity,
            "order_count": 0
        })
    
    # 현재가 및 시간 정보
    current_price = int(body.get("last", 0))
    time_str = body.get("time", "000000")  # HHMMSS
    date_str = body.get("date", datetime.now().strftime("%Y%m%d"))  # YYYYMMDD
    
    # ISO 8601 형식으로 변환
    timestamp = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
    
    return {
        "stock_code": stock_code,
        "asks": asks,
        "bids": bids,
        "current_price": current_price,
        "timestamp": timestamp,
        "market_data": {
            "open": int(body.get("open", 0)),
            "high": int(body.get("high", 0)),
            "low": int(body.get("low", 0)),
            "volume": int(body.get("vol", 0)),
            "value": int(body.get("value", 0)),
            "sign": body.get("sign", "3"),
            "change": int(body.get("change", 0)),
            "drate": float(body.get("drate", 0.0))
        }
    }


def receive_realtime_hoga_domestic(data):
  """ 
  한국투자증권 실시간 호가 데이터 파싱 (파이프 구분자 형식 - 기존 호환성 유지)
  데이터 형식: 종목코드^매수10호가^...^매수1호가^매도1호가^...^매도10호가^매수10호가수량^...^매수1호가수량^매도1호가수량^...^매도10호가수량
  """
  values = data.split('^')
  data_dict = dict()
  
  if len(values) < 41:  # 최소 필요한 필드 수 확인
    logger.warning(f"호가 데이터 길이 부족: {len(values)}")
    return {"종목코드": values[0] if values else ""}
  
  data_dict["종목코드"] = values[0]
  
  # 매수호가 (10호가부터 1호가까지, 역순)
  for i in range(1, 11):
    bid_price_idx = 11 - i  # 10호가=1, 9호가=2, ..., 1호가=10
    bid_qty_idx = 30 + i    # 10호가수량=31, 9호가수량=32, ..., 1호가수량=40
    
    if bid_price_idx < len(values) and bid_qty_idx < len(values):
      data_dict[f"매수{i}호가"] = values[bid_price_idx]
      data_dict[f"매수{i}호가수량"] = values[bid_qty_idx]
  
  # 매도호가 (1호가부터 10호가까지)
  for i in range(1, 11):
    ask_price_idx = 10 + i  # 1호가=11, 2호가=12, ..., 10호가=20
    ask_qty_idx = 20 + i    # 1호가수량=21, 2호가수량=22, ..., 10호가수량=30
    
    if ask_price_idx < len(values) and ask_qty_idx < len(values):
      data_dict[f"매도{i}호가"] = values[ask_price_idx]
      data_dict[f"매도{i}호가수량"] = values[ask_qty_idx]
  
  return data_dict


def run_websocket(korea_invest_api, ws_url, ws_req_queue, ws_result_queue):
  #이벤트 루프 초기화
  loop = asyncio.get_event_loop()
  loop.run_until_complete(connect_with_circuit_breaker(korea_invest_api, ws_url, ws_req_queue, ws_result_queue))
  loop.close()


async def connect_with_circuit_breaker(korea_invest_api, url, ws_req_queue, ws_result_queue):
  """Circuit Breaker를 적용한 WebSocket 연결"""
  metrics_collector = get_global_metrics_collector()
  circuit_breaker = metrics_collector.get_circuit_breaker("websocket_connection")
  
  while True:
    if not circuit_breaker.can_attempt():
      logger.warning("Circuit Breaker OPEN. 60초 대기...")
      await asyncio.sleep(60)
      continue
    
    try:
      await connect(korea_invest_api, url, ws_req_queue, ws_result_queue)
      circuit_breaker.record_success()
      logger.info("WebSocket 연결 성공")
      
    except Exception as e:
      logger.error(f"WebSocket 연결 오류: {e}")
      circuit_breaker.record_failure()
      metrics_collector.metrics.record_connection_error()
      await asyncio.sleep(5)
  


async def connect(korea_invest_api, url, ws_req_queue, ws_result_queue):
  logger.info("한국투자증권 API Web Socket 연결 try!")
  running_account_number = korea_invest_api.stock_account_number
  aes_key = None
  aes_iv = None
  
  # 성능 모니터링 초기화
  result_monitor = QueueMonitor(ws_result_queue, "ws_result_queue")
  metrics_collector = get_global_metrics_collector()
  dropped_messages_count = 0
  last_warning_time = 0

  
  async with websockets.connect( url, ping_interval=None) as websocket:
        
    # 데이터 수신 카운터
    tick_count = 0
    hoga_count = 0
    max_data_count = 10  # 10번 데이터 수신 후 해제

    ### 주문 접수/체결 통보 등록    
    send_data = korea_invest_api.get_send_data(cmd=5, stock_code=None) #주문 접수/체결 통보 등록
    logger.info(f"[실시간 체결 통보 등록]")
    await websocket.send(send_data)

    # 지수 실시간 구독 등록 (KOSPI 001, KOSDAQ 201)
    for tr_key in ["001", "201"]:
      try:
        index_send_data = korea_invest_api.get_index_send_data(tr_key)
        logger.info(f"[실시간 지수 등록] tr_key={tr_key}")
        await websocket.send(index_send_data)
      except Exception as e:
        logger.error(f"실시간 지수 등록 실패 tr_key={tr_key}: {e}")
    
    while True:
      if not ws_req_queue.empty():
        req_data = ws_req_queue.get()
        action_id = req_data['action_id']
        stock_code = req_data.get('종목코드') # stock_code가 항상 있을 것이라고 가정하지 않음

        if action_id == "실시간체록록등록":
          logger.info(f"실시간체록록등록 {stock_code}")
          send_data = korea_invest_api.get_send_data(cmd=3, stock_code=stock_code) #실시간체결통보 등록
          await websocket.send(send_data)
          
        elif action_id == "실시간호가등록":
          logger.info(f"실시간호가등록 {stock_code}")
          send_data = korea_invest_api.get_send_data(cmd=1, stock_code=stock_code) #실시간호가등록
          await websocket.send(send_data)

        elif action_id == "실시간체결통보해제":
          logger.info(f"실시간체결통보해제 {stock_code}")
          send_data = korea_invest_api.get_send_data(cmd=4, stock_code=stock_code) #실시간체결통보해제
          await websocket.send(send_data)
          
        elif action_id == "실시간호가해제":
          logger.info(f"실시간호가해제 {stock_code}")
          send_data = korea_invest_api.get_send_data(cmd=2, stock_code=stock_code) #실시간호가해제
          await websocket.send(send_data)

        elif action_id == "종료":
          logger.info(f"종료")
          break
          

      data = await websocket.recv()
      logger.info(f"received data: {data} \n")

      if data[0] == '0':  
        recvstr = data.split('|')
        trid0 = recvstr[1]

        if trid0 == "H0STCNI0" : #주식 체결 데이터 처리
          data_cnt = int(recvstr[2])
          for cnt in range ( data_cnt):
            data_dict = receive_realtime_tick_domestic(recvstr[3])
            
            # 백프레셔 처리: Queue 상태 확인
            status = result_monitor.check_status()
            if status == "critical":
              # Queue가 가득 차면 데이터 수신 속도 조절
              current_time = time.time()
              if current_time - last_warning_time > 5:  # 5초마다 경고
                logger.warning("Queue 가득 참. 100ms 대기...")
                last_warning_time = current_time
              await asyncio.sleep(0.1)
              continue
            
            # Queue에 추가 (타임아웃 설정)
            try:
              ws_result_queue.put(
                dict(
                  action_id='실시간체결',
                  종목코드=data_dict["종목코드"],
                  data=data_dict
                ), 
                block=True, 
                timeout=1.0
              )
              metrics_collector.metrics.record_message_received()
            except queue.Full:
              logger.error("Queue 가득 참. 데이터 드롭!")
              dropped_messages_count += 1
              metrics_collector.metrics.record_message_dropped()
            
        elif trid0 == "H0STASP0":   # 주식호가 데이터 처리
          # JSON 파싱으로 변경
          try:
            json_data = json.loads(recvstr[3])
            data_dict = parse_hoga_json(json_data)
          except json.JSONDecodeError:
            logger.error(f"호가 데이터 JSON 파싱 실패: {recvstr[3][:100]}")
            continue
          
          # 백프레셔 처리: Queue 상태 확인
          status = result_monitor.check_status()
          if status == "critical":
            # Queue가 가득 차면 데이터 수신 속도 조절
            current_time = time.time()
            if current_time - last_warning_time > 5:  # 5초마다 경고
              logger.warning("Queue 가득 참. 100ms 대기...")
              last_warning_time = current_time
            await asyncio.sleep(0.1)
            continue
          
          # Queue에 추가 (타임아웃 설정)
          try:
            ws_result_queue.put(
              dict(
                action_id="실시간호가",
                stock_code=data_dict["stock_code"],
                data=data_dict
              ),
              block=True,
              timeout=1.0
            )
            metrics_collector.metrics.record_message_received()
          except queue.Full:
            logger.error("Queue 가득 참. 호가 데이터 드롭!")
            dropped_messages_count += 1
            metrics_collector.metrics.record_message_dropped()
          


      elif data[0] == '1': # 실시간 체결 데이터
        recv_str = data.split('|')
        trid0 = recv_str[1]


        if trid0 in ("H0STCNI0", "H0STCNI9" ): # 주식 체결 통부 처리
          receive_signing_notice( recv_str[3], aes_key, aes_iv, running_account_number, ws_result_queue)
      else:
        jsonObject = json.loads(data)
        trid = jsonObject["header"]["tr_id"]

        if trid != "PINGPONG":  
          rt_cd = jsonObject["body"]["rt_cd"]
          if rt_cd == "1": # 에러일 경우
            logger.info(f"### ERROR Return Code [{rt_cd}] MSG [{jsonObject["body"]["msg1"]}]")
          elif rt_cd =="0":
            logger.info(f"### SUCCESS Return Code [{rt_cd}] MSG [{jsonObject["body"]["msg1"]}]")
            #체결통보 ㅓㅊ리를 위한 AES256 KEY, IV 처리
            if trid in("H0STCNI0","H0STCNI9"):
              aes_key = jsonObject["body"]["output"]["key"]
              aes_iv = jsonObject["body"]["output"]["iv"]
              logger.info(f"### TRID [{trid}] KEY[{aes_key}] IV[{aes_iv}]")

          if trid == "H0STISE0":
            body = jsonObject.get("body", {})
            output = body.get("output", {})
            input_info = body.get("input", {})
            index_code = (
              output.get("tr_key")
              or output.get("idx_clsf_cd")
              or input_info.get("tr_key")
              or output.get("index_code")
            )

            ws_result_queue.put({
              "action_id": "실시간지수",
              "index_code": index_code,
              "data": output,
              "meta": {
                "rt_cd": body.get("rt_cd"),
                "msg_cd": body.get("msg_cd"),
                "msg1": body.get("msg1"),
              }
            })

            continue

        if trid == "PINGPONG":
          logger.info(f"### RECV [PINGPONG] [{data}]")
          await websocket.send(data)
          logger.info(f"### SEND [PINGPONG] [{data}]")


def receive_signing_notice(data, key, iv, account_num="", ws_result_queue=None):
  """

  """
  #AES256 처리 
  aes_dec_str = aes_cbc_base64_dec(key, iv, data)
  values = aes_dec_str.split('^')
  계좌번호 = values[1]
  if 계좌번호[:8] != account_num:
    return

  거부여부 = values[12]
  if 거부여부 != "0":
    logger.info(f"Got 거부 TR!")
    return

  체결여부 = values[13]
  종목코드 = values[8]
  종목명 = values[18]
  시간    = values[11]
  주문수량 = 0 if len(values[16]) == 0 else int ( values[16])

  if values[13] == '1':
    주문가격 = 0 if len(values[10])== 0 else int(values[10])
  else:
    주문가격 = 0 if len(values[22])== 0 else int(values[22])
  체결수량 = 0 if len(values[9]) ==0 or 체결여부 == "1" else int(values[9])
  if values[13] == '1':
    체결가격 = 0
  else:
    체결가격 = 0 if len(values[10])== 0 else int(values[10])
  
  매도매수구분 = values[4]
  정정구분 = values[5]


  if 매도매수구분 == '02' and 정정구분 != "0":
    주문구분 = "매수정정"
  elif 매도매수구분 == '01' and 정정구분 != "0":
    주문구분 = "매도정정"
  elif 매도매수구분 == '02':
    주문구분 = "매수"
  elif 매도매수구분 == '01':
    주문구분 = "매도"
  else:
    raise ValueError(f"주문구분 실패! 매도매수구분; {매도매수구분}, 정정구분: {정정구분} ")

  주문번호 = values[2]
  원주문번호 = values[3]
  logger.info(f"Received chejandata! 시간: {시간}"
              f"종목코드 : {종목코드}, 종목명: {종목명}, 주문수량: {주문수량}"
              f"주문가격 : {주문가격}, 체결수량: {체결수량}, 체결가격: {체결가격}"
              f"주문구분 : {주문구분}, 주문번호: {주문번호}, "
              f"원주호번호 : {원주문번호}, 체결여부부 {체결여부}"
              
  )
  ws_result_queue.put(
    dict(
      action_id='주문체결통보',
      시간=시간, 
      종목코드=종목코드,
      종목명=종목명,
      주문수량=주문수량,
      체결가격=체결가격,
      주문구분=주문구분,
      주문번호=주문번호,
      원주문번호=원주문번호,
      체결여부=체결여부,
    )
  )

  
def receive_realtime_tick_domestic(data):
  """
  메뉴 순서는 '|'로 분리 해서 하나씩 접근함.
  유가 증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|
  매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|
  매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|
  신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|종매도호가잔량|총매수호가잔량|거래량회전율|전일동시간누적거래량|전일동시간누적거래량비율|
  시간구분코드|임의종료구분코드|정적VI발동기준가
  """
  values = data.split('^')
  종목코드 = values[0]
  체결시간 = values[1]
  현재가 = values[2]
  return dict( 
    종목코드=종목코드,
    체결결간=체결시간,
    현재가=현재가,
  )
