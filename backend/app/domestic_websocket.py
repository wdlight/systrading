import json
import asyncio
import queue
import time
from datetime import datetime
from multiprocessing import Queue

import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64decode
from loguru import logger

from app.core.config import Settings
from app.core.korea_invest import KoreaInvestAPIService
from app.core.logging_config import setup_logging
from app.utils.performance_metrics import get_global_metrics_collector, create_circuit_breaker
from app.utils.queue_monitor import QueueMonitor

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
                {"price": 71800, "quantity": 100},
                ...  # 10개
            ],
            "bids": [
                {"price": 71700, "quantity": 150},
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
            "quantity": quantity
        })
    
    # 매수호가 파싱 (bidp1~10, bidp_rsqn1~10)
    bids = []
    for i in range(1, 11):
        price = int(body.get(f"bidp{i}", 0))
        quantity = int(body.get(f"bidp_rsqn{i}", 0))
        bids.append({
            "price": price,
            "quantity": quantity
        })
    
    # 현재가 및 시간 정보
    current_price = _safe_int(body.get("last", 0), 0)
    current_price = _resolve_current_price(
        current_price,
        asks,
        bids,
        body.get("stck_prpr"),
        body.get("new_last"),
        body.get("base"),
    )
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

def receive_realtime_hoga_domestic_new(data: str) -> dict | None:
    """
    KIS WebSocket에서 내려오는 ^ 구분자 호가 데이터를 표준 구조로 변환한다.
    데이터 예시:
    005930^142414^0^95100^95200^...^매도/매수호가^...^호가수량^...^기타 필드
    """
    try:
        values = data.split('^')
        if len(values) < 43:
            logger.warning(f"호가 데이터 길이 부족: {len(values)}, 데이터: {data[:100]}")
            return None

        stock_code = values[0]
        time_str = values[1]  # HHMMSS

        # 현재가 (필드 2 혹은 매수/매도 1호가 평균)
        current_price = _safe_int(values[2] if len(values) > 2 else 0, 0)

        asks = []
        bids = []

        # 매도 호가/수량: ask1~ask10 는 인덱스 3~12, 수량은 23~32
        for i in range(10):
            price_idx = 3 + i
            qty_idx = 23 + i
            price = int(values[price_idx]) if values[price_idx].isdigit() else 0
            quantity = int(values[qty_idx]) if values[qty_idx].lstrip('-').isdigit() else 0
            asks.append({
                "price": price,
                "quantity": quantity
            })

        # 매수 호가/수량: bid1~bid10 는 인덱스 13~22, 수량은 33~42
        for i in range(10):
            price_idx = 13 + i
            qty_idx = 33 + i
            price = int(values[price_idx]) if values[price_idx].isdigit() else 0
            quantity = int(values[qty_idx]) if values[qty_idx].lstrip('-').isdigit() else 0
            bids.append({
                "price": price,
                "quantity": quantity
            })

        timestamp = datetime.now().strftime("%Y-%m-%dT") + f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"

        current_price = _resolve_current_price(current_price, asks, bids)

        result = {
            "stock_code": stock_code,
            "asks": asks,
            "bids": bids,
            "current_price": current_price,
            "timestamp": timestamp,
            "market_data": {
                "open": 0,
                "high": 0,
                "low": 0,
                "volume": 0,
                "value": 0,
                "sign": "3",
                "change": 0,
                "drate": 0.0
            }
        }
        if current_price == 0 and stock_code:
            logger.debug(f"호가 데이터에서 현재가를 찾지 못했습니다: {stock_code}")

        return result
    except Exception as e:
        logger.error(f"호가 ^ 데이터 파싱 오류: {e}, 데이터: {data[:100]}")
        return None


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


def run_websocket(settings_data, ws_url, ws_req_queue, ws_result_queue):
  """Multiprocessing 프로세스에서 실행될 WebSocket 런너."""
  try:
    # settings 데이터 복원
    if isinstance(settings_data, dict):
      settings = Settings(**settings_data)
    elif isinstance(settings_data, Settings):
      settings = settings_data
    else:
      logger.warning(f"알 수 없는 settings 데이터 타입: {type(settings_data)}. 기본 설정을 사용합니다.")
      settings = Settings()

    logger.info("domestic_websocket 프로세스 시작 - API 인스턴스 생성 중...")
    
    try:
      korea_invest_service = KoreaInvestAPIService(settings)
      korea_invest_api = korea_invest_service.api_instance

      if not korea_invest_api:
        logger.error("KoreaInvestAPI 인스턴스 생성 실패 - api_instance가 None")
        return

      logger.info("KoreaInvestAPI 인스턴스 생성 완료")
    except Exception as api_init_error:
      logger.error(f"KoreaInvestAPIService 초기화 실패: {api_init_error}", exc_info=True)
      return

    # Circuit breaker 확인 (자식 프로세스는 초기화되어 있지 않음)
    metrics_collector = get_global_metrics_collector()
    if metrics_collector.get_circuit_breaker("websocket_connection") is None:
      logger.info("자식 프로세스에서 Circuit Breaker 초기화")
      create_circuit_breaker(
        name="websocket_connection",
        failure_threshold=5,
        timeout_seconds=60
      )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_with_circuit_breaker(korea_invest_api, ws_url, ws_req_queue, ws_result_queue))
  except Exception as e:
    logger.error(f"domestic_websocket 프로세스 시작 실패: {e}", exc_info=True)
  finally:
    try:
      if 'loop' in locals():
        loop.close()
    except Exception as loop_error:
      logger.warning(f"이벤트 루프 종료 중 오류: {loop_error}")


async def connect_with_circuit_breaker(korea_invest_api, url, ws_req_queue, ws_result_queue):
  """Circuit Breaker를 적용한 WebSocket 연결"""
  metrics_collector = get_global_metrics_collector()
  circuit_breaker = metrics_collector.get_circuit_breaker("websocket_connection")
  if circuit_breaker is None:
    logger.warning("Circuit Breaker가 존재하지 않아 기본 설정으로 생성합니다.")
    circuit_breaker = create_circuit_breaker(
      name="websocket_connection",
      failure_threshold=5,
      timeout_seconds=60
    )
  
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
    
    stop_event = asyncio.Event()

    subscribed_hoga: set[str] = set()

    async def process_queue():
      """
      multiprocessing.Queue는 blocking 호출만 제대로 동작하므로
      to_thread로 감싸 timeout을 적용하며 polling한다.
      """
      while not stop_event.is_set():
        try:
          req_data = await asyncio.to_thread(ws_req_queue.get, True, 0.5)
        except queue.Empty:
          # 500ms 동안 요청이 없으면 다시 루프 진입
          continue
        except Exception as e:
          logger.error(f"Queue 처리 중 오류: {e}")
          await asyncio.sleep(0.1)
          continue

        if not isinstance(req_data, dict):
          logger.warning(f"알 수 없는 Queue 데이터 무시: {req_data}")
          continue

        action_id = req_data.get('action_id')
        stock_code = req_data.get('종목코드')
        logger.info(f"[DEBUG] Queue에서 요청 수신: action_id={action_id}, stock_code={stock_code}")

        try:
          if action_id == "실시간체록록등록":
            logger.info(f"실시간체록록등록 {stock_code}")
            send_data = korea_invest_api.get_send_data(cmd=3, stock_code=stock_code)
            await websocket.send(send_data)

          elif action_id == "실시간호가등록":
            logger.info(f"실시간호가등록 {stock_code}")
            send_data = korea_invest_api.get_send_data(cmd=1, stock_code=stock_code)
            logger.info(f"[DEBUG] 호가 구독 데이터 전송: {send_data[:100]}...")
            await websocket.send(send_data)
            logger.info(f"[DEBUG] 호가 구독 데이터 전송 완료")
            subscribed_hoga.add(stock_code)

          elif action_id == "실시간체결통보해제":
            logger.info(f"실시간체결통보해제 {stock_code}")
            send_data = korea_invest_api.get_send_data(cmd=4, stock_code=stock_code)
            await websocket.send(send_data)

          elif action_id == "실시간호가해제":
            logger.info(f"실시간호가해제 {stock_code}")
            send_data = korea_invest_api.get_send_data(cmd=2, stock_code=stock_code)
            await websocket.send(send_data)
            subscribed_hoga.discard(stock_code)

          elif action_id == "종료":
            logger.info("종료 요청 수신 – WebSocket 종료")
            stop_event.set()
            await websocket.close()
            break
          else:
            logger.warning(f"알 수 없는 action_id: {action_id}")
        except Exception as e:
          logger.error(f"Queue 처리 중 전송 오류: action_id={action_id}, error={e}")
          await asyncio.sleep(0.1)

    queue_task = asyncio.create_task(process_queue())

    while True:
      if stop_event.is_set():
        break

      try:
        data = await asyncio.wait_for(websocket.recv(), timeout=0.5)
      except asyncio.TimeoutError:
        # Queue 태스크가 계속 동작하도록 루프 유지
        continue
      except websockets.exceptions.ConnectionClosed as e:
        logger.info(
          f"WebSocket 연결 종료 감지: code={e.code}, reason={e.reason}, was_clean={getattr(e, 'was_clean', None)}"
        )
        break
      # websocket 전달  log 활성화
      #logger.info(f"received data: {data} \n")

      if data[0] == '0':
        recvstr = data.split('|')
        trid0 = recvstr[1]

        # 📥 [WS-DATA] 모든 수신 데이터 로깅 (with special icon)
        data_preview = recvstr[3][:100] if len(recvstr) > 3 else 'N/A'
        logger.info(f"📥 [WS-DATA] trid0={trid0}, data_cnt={recvstr[2] if len(recvstr) > 2 else 'N/A'}, preview={data_preview}")

        if trid0 == "H0STCNI0" : #주식 체결 데이터 처리
          logger.info(f"✅ [H0STCNI0-ENTRY] Processing execution/tick data")
          data_cnt = int(recvstr[2])
          for cnt in range ( data_cnt):
            raw_payload = recvstr[3]
            logger.info("[H0STCNI0] raw payload: %s", raw_payload)
            data_dict = receive_realtime_tick_domestic(raw_payload)
            logger.info("[H0STCNI0] parsed data: %s", data_dict)
            
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
                  stock_code=data_dict["stock_code"],
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
          logger.info(f"✅ [H0STASP0-ENTRY] Processing orderbook data")
          # JSON 형식과 ^ 파이프 형식을 모두 지원
          data_dict = None
          if recvstr[3].startswith('{'):
            try:
              json_data = json.loads(recvstr[3])
              data_dict = parse_hoga_json(json_data)
            except json.JSONDecodeError:
              logger.error(f"호가 데이터 JSON 파싱 실패: {recvstr[3][:100]}")
              continue
          else:
            data_dict = receive_realtime_hoga_domestic_new(recvstr[3])
            if not data_dict:
              logger.error(f"호가 파이프 데이터 파싱 실패: {recvstr[3][:100]}")
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
            if jsonObject["body"].get("msg1") == "ALREADY IN SUBSCRIBE" and jsonObject["body"].get("tr_id") == "H0STASP0":
              tr_key = jsonObject["body"].get("output", {}).get("tr_key")
              if tr_key:
                try:
                  logger.info(f"기존 호가 구독 해제 후 재구독 시도: {tr_key}")
                  await websocket.send(korea_invest_api.get_send_data(cmd=2, stock_code=tr_key))
                  await asyncio.sleep(0.2)
                  await websocket.send(korea_invest_api.get_send_data(cmd=1, stock_code=tr_key))
                  logger.info(f"재구독 완료: {tr_key}")
                except Exception as retry_error:
                  logger.error(f"호가 재구독 실패: {tr_key}, {retry_error}")
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

    # 루프 종료시 Queue 태스크 정리
    stop_event.set()
    queue_task.cancel()
    try:
      await queue_task
    except asyncio.CancelledError:
      pass

    for code in subscribed_hoga:
      logger.info(f"연결 종료 - 호가 구독 재요청 예정: {code}")
      try:
        ws_req_queue.put_nowait({
          "action_id": "실시간호가등록",
          "종목코드": code
        })
      except Exception as reinject_err:
        logger.error(f"호가 재등록 큐 삽입 실패 ({code}): {reinject_err}")


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

  
def receive_realtime_tick_domestic(raw: str) -> dict:
  """
  한국투자증권 H0STCNI0 체결 채널 (^ 구분 문자열) 파싱.

  필드 순서는 docs/KIS-API/KIS-ws-H0STCNI0.spec.md 기준으로 21개이다.
  """
  values = raw.split("^")

  def _int(idx: int, default: int = 0) -> int:
    try:
      return int(values[idx]) if len(values) > idx and values[idx] else default
    except ValueError:
      return default

  def _float(idx: int, default: float = 0.0) -> float:
    try:
      return float(values[idx]) if len(values) > idx and values[idx] else default
    except ValueError:
      return default

  return {
    "stock_code": values[0] if len(values) > 0 else "",
    "executed_time": values[1] if len(values) > 1 else "",
    "price": _int(2),
    "trade_volume": _int(3),
    "change_sign": values[4] if len(values) > 4 else "",
    "change": _int(5),
    "change_rate": _float(6),
    "ask_price": _int(7),
    "bid_price": _int(8),
    "ask_qty": _int(9),
    "bid_qty": _int(10),
    "market_code": values[11] if len(values) > 11 else "",
    "total_ask_qty": _int(12),
    "total_bid_qty": _int(13),
    "volume_ratio": _float(14),
    "acc_volume": _int(15),
    "acc_value": _int(16),
    "open_price": _int(17),
    "high_price": _int(18),
    "low_price": _int(19),
    "sequence": _int(20),
    "raw_payload": raw,
  }

def _safe_int(value, default: int = 0) -> int:
    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str) and value.strip():
            return int(float(value.replace(',', '')))
    except (ValueError, TypeError):
        return default
    return default


def _resolve_current_price(
    initial_price: int,
    asks: list,
    bids: list,
    *extra_candidates
) -> int:
    """현재가 후보들 중 첫 번째 유효값을 반환한다."""
    candidates = [initial_price]
    candidates.extend(extra_candidates)

    for candidate in candidates:
        price = _safe_int(candidate, 0)
        if price > 0:
            return price

    # 우선 매수 1호가, 이후 매도 1호가 사용
    for bid in bids or []:
        price = _safe_int(bid.get("price"), 0)
        if price > 0:
            return price

    for ask in asks or []:
        price = _safe_int(ask.get("price"), 0)
        if price > 0:
            return price

    return 0
