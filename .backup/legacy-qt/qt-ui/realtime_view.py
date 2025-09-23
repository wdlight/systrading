import json
from base64 import b64decode
import yaml
import websockets
import asyncio
from loguru import logger
from utils import KoreaInvestEnv, KoreaInvestAPI
from Crypto.Cipher import AES
from base64 import b64decode
from Crypto.Util.Padding import pad, unpad

def run_websocket(korea_invest_api, ws_url):
  #이벤트 루프 초기화
  loop = asyncio.get_event_loop()
  loop.run_until_complete(connect(korea_invest_api, ws_url))
  loop.close()
  
def aes_cbc_base64_dec(key, iv, cipher_text):
  """
  :param key = str type AES256 secret key value
  :param iv = str type AES256 initialize Vector
  :param cipher_text = str type Base64 encoded AES256 str
  :return: Base64-AES256 decodec str
  """
  cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8)'))
  return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size()))

def receive_signing_notice(data, key, iv, account_num=""):
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
  거부여부 = values[18]
  시간    = values[11]
  주문수량 = 0 if len(values[16]) == 0 else int ( values[16])

  if values[13] == '1':
    주문가격 = 0 if len(values[10])== 0 else int(values[10])
  else:
    주문가격 = 0 if len(values[22])== 0 else int(values[22])

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
  

def receive_realtime_hoga_domestic(data):
  """ 
  https://wikidocs.net/170516
  """
  values = data.split('^')
  data_dict = dict()
  data_dict["종목코드"] = values[0]
  for i in range(1,11):
    data_dict[f"매수{i}호가"] = values[i + 12]
    data_dict[f"매수{i}호가수량"] = values[i + 32]
    data_dict[f"매수{i}호가"] = values[i + 2]
    data_dict[f"매수{i}호가수량"] = values[i + 22]
  return data_dict


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


async def connect(korea_invest_api, url):
  logger.info("한국투자증권 API Web Socket 연결 try!")
  running_account_number = korea_invest_api.stock_account_number

  
  async with websockets.connect( url, ping_interval=None) as websocket:
    stock_code = "005930" # 삼성전자. 
    
    # 데이터 수신 카운터
    tick_count = 0
    hoga_count = 0
    max_data_count = 10  # 10번 데이터 수신 후 해제
    
    send_data = korea_invest_api.get_send_data(cmd=3, stock_code=stock_code) # 체결 등록
    logger.info(f"[실시간 체결 등록] 종목코드: {stock_code}")
    await websocket.send(send_data)
    send_data = korea_invest_api.get_send_data(cmd=1, stock_code=stock_code) # 호가 등록
    logger.info(f"[실시간 호가 등록] 종목코드: {stock_code}")
    await websocket.send(send_data)

    while True:
      data = await websocket.recv()
      logger.info(f"received data: {data} \n")
      if data[0] == '0':  # 실시간 호가 데이터, 체결 데이터
        recvstr = data.split('|')
        trid0 = recvstr[1]

        if trid0 == "H0STCNT0": # 주식 체결 데이터 처리
          data_cnt = int( recvstr[2]) # 체결 데이터 개수
          for cnt in range( data_cnt):
            data_dict = receive_realtime_tick_domestic(recvstr[3])
            tick_count += 1
            logger.info(f"주식 체결 데이터 ({tick_count}회): {data_dict}")
            
            # 10번 데이터 수신 후 해제
            if tick_count >= max_data_count:
              send_data = korea_invest_api.get_send_data(cmd=4, stock_code= stock_code)  #체결 해제
              logger.info(f"[실시간 체결 해제] 종목코드: {stock_code} (총 {tick_count}회 수신)")
              await websocket.send(send_data)
              tick_count = 0  # 카운터 리셋
              
        elif trid0 == "H0STASP0":
            data_dict = receive_realtime_hoga_domestic(recvstr[3])
            hoga_count += 1
            formatted_data = "\n".join([f"  {key}: {value}" for key, value in data_dict.items()])
            logger.info(f"주식 호가 데이터 ({hoga_count}회):\n{formatted_data}")
            
            # 10번 데이터 수신 후 해제
            if hoga_count >= max_data_count:
              send_data = korea_invest_api.get_send_data(cmd=2, stock_code= stock_code)  #호가 해제
              logger.info(f"[실시간 호가 해제] 종목코드: {stock_code} (총 {hoga_count}회 수신)")
              await websocket.send(send_data)
              hoga_count = 0  # 카운터 리셋
      else:
        jsonObject = json.loads(data)
        trid = jsonObject["header"]["tr_id"]

        if trid != "PINGPONG":
          rt_cd = jsonObject["body"]["rt_cd"]

          if rt_cd == '1': # 에러일 경우 처리
            logger.info(f"### ERROR RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
          elif rt_cd == '0': # 정상일 경우 처리
            logger.info(f"### RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
            # 체결 통보 처리를 위한 AES256 KEY, IV 처리 단계
            if trid in ("H0STCNI0", "H0STCNI9"):
              aes_key = jsonObject["body"]["output"]["key"]
              aes_iv = jsonObject["body"]["output"]["iv"]
              logger.info(f"### TRID [{trid}] KEY[{aes_key}] IV[{aes_iv}]")

        elif trid == "PINGPONG":
          logger.info(f"### RECV [PINGPONG] [{data}]")
          await websocket.send(data)
          logger.info(f"### SEND [PINGPONG] [{data}]")




def main():
  with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

  env_cls = KoreaInvestEnv(config)
  base_headers = env_cls.get_base_headers()
  cfg = env_cls.get_full_config()
  korea_invest_api = KoreaInvestAPI(cfg, base_headers=base_headers)

  websocket_url = cfg['paper_websocket_url'] if cfg['is_paper_trading'] else cfg['websocket_url']

  run_websocket(korea_invest_api, websocket_url)

  print(korea_invest_api)
  print ( "------------------- Initialized -----------------\n\n")


  # print ( "------------------- 삼성전자(005930) 현재가 -----------------")
  
  # price_info_map = korea_invest_api.get_current_price("005930")
  # print (price_info_map)

  # print ( "\n\n------------------- 매도 호가 -----------------\n\n")
  # price_info_map = korea_invest_api.get_hoga_info("005930")
  # print (price_info_map)

  # print ( "\n\n------------------- 종목별 잔고 -----------------\n\n")
  # account_balance, details_df = korea_invest_api.get_acct_balance()
  # print('$$$$$$$ 종목별 잔고 $$$$$$$$')
  # print( details_df)


  # print ( "\n\n------------------- 등락율 순위 -----------------\n\n")
  # ranking_df = korea_invest_api.get_fluctuation_ranking()
  # print(ranking_df)


  # print ( "\n\n------------------- 매수 test -----------------\n\n")
  # res = korea_invest_api.buy_order("005930", order_qty=1, order_price=50000, order_type="01") # 삼성전자?
  # print(f"주문 접수 결과: {res.get_body()}")

  # print ( "\n\n------------------- 매도 test -----------------\n\n")
  # res = korea_invest_api.buy_order("005930", order_qty=1, order_price=60000, order_type="01") # 삼성전자?
  # print(f"주문 접수 결과: {res.get_body()}")
  




if __name__ == '__main__':
  main()