import os
from multiprocessing import PRocess, Process, Queue
import json
from base64 import b64decode
from tkinter import W
import yaml
import websockets
import asyncio
from loguru import logger
from utils import KoreaInvestEnv, KoreaInvestAPI
from Crypto.Cipher import AES
from base64 import b64decode
from Crypto.Util.Padding import pad, unpad

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QSettings, QTimer, QAbstractTableModel, QEvent
from PyQt5 import uic, QtGui


def send_tr_process(korea_invest_api, tr_req_queue:Queue, tr_result_queue:Queue):
  while True:
    try:
      data = tr_req_queue.get()
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
      elif data['action_id'] == "계좌조회":
        total_balance, per_code_balance_df = korea_invest_api.get_account_balance()
        tr_result_queue.put(dict(
          action_id="계좌조회",
          total_balance=total_balance,
          per_code_balance_df=per_code_balance_df
        ))

      else:
        logger.debug(f"Unknown Action! {data}")

    except Exception as e:
      logger.exception(e)
      break

class PandasModel(QAbstractTableModel):
  def __init__(self,data):
    super().__init__()
    self._data = data

  def rowCount(self, parent=None):
    return self._data.shape[0]

  def columnCount(self, parent=None):
    return self._data.shape[1]

  def data(self, index, role=Qt.DisplayRole):
    if index.isValid():
      if role == Qt.DisplayRole:
        return str(self._data.iloc[index.row(), index.coloumn()])
      return None

  def headerData(self, section, orientation, role):
    if orientation == Qt.Horizontal and role == Qt.DisplayRole:
      return self._data.columns[section]
    if orientation == Qt.Vertical and role == Qt.DisplayRole:
      return self._data.index[section]

    return None

  def setData(self, index, value, role):
    #항상 False ㄱㄷ셔구 편집 비활성화
    return False

  def flags(self, index):
    return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

  def pop_from_realtime_tracking_list(self, stock_code=None):
    #stock_code = self.inOutStockCodeLIneEdit.text()
    self.realtime_watchlist_df.drop(stock_code, inplace=True)

  

  def push_to_Realtime_tracking_list(self):
    #stock_code = self.inOutStockCodeLIneEdit.text()
    self.realtime_watchlist_df.loc[stock_code] = {
      '현재가': None,
      '수익률': None,
      '평균단가': None,
      '보유수량': 0,
      '트레일링스탑발동여부': False,
      '트레일링스탑발동후고가': None
    }


  def receive_tr_result(self):
    if not self.tr_result_queue.empty():
      data = self.tr_result_queue.get()
      if data['action_id'] == '계좌조회' :
        self.on_balance_req( data['total_balance'], data['per_code_balance_df'] )

  def req_balance(self):
    self.tr_req_queue.put( dict( action_id="계좌조회"))


  def on_balance_req(self, total_balance, per_code_balance_df):
    #self.domesticCurrentBalanceLabel.setText(f"현재 평가 잔고: { total_balance: ,}"원
    logger.info(f"현재평가잔고: {total_balance}")
    self.account_info_df = per_code_balance_df[per_code_balance_df['보유수량'] != 0]
    for row in self.account_info_df.itertuples():
      stock_code = getattr(row, "종목코드")
      if stock_code not in self.realtime_registered_codes:
        self.ws_req_queue.put(
          dict(
            action_id='실시간체결등록',
            종목코드=stock_code,
          )
        )
        self.realtime_registered_codes.add(stock_code)
      if stock_code in self.realtime_watchlist_df.index:
        self.realtime_watchlist_df.loc[stock_code, "보유수량"] = getattr(row,"보유수량")
        self.realtime_watchlist_df.loc[stock_code, "평균단가"] = getattr(row,"매입단가")

    logger.info(f'{self.account_info_df}')

    self.account_model = PandasModel(self.account_info_df)
    realtime_tracking_model = PandasModel(self.realtime_watchlist_df.copy(deep=True))

  def receive_data_from_websocket(self):
    try:
      if not self.realtime_data_out_queue.empty():
        data = self.realtime_data_out_queue.get()
        if data['action_id'] == '실시간호가':
          stock_code = data['종목코드']
          index = self.stock_code_to_index_num_map.get(stock_code, None)
          if index is not None:
            self.update_input_groupbox(index, data['data'])
        elif data['action_id'] =='실시간체결':
          stock_code = data['종목코드']
          now_price = data['data']['현재가']
          self.stock_code_to_realtime_price_map[stock_code] = now_price
          mean_buy_price = self.realtime_watchlist_df.loc[stock_code, '평균단가']
          if mean_buy_price is not None:
            수익률 = round( (now_price - mean_buy_price) / mean_buy_price * 100 - 0.21, 2) # 0.21 수수료.
            self.realtime_watchlist_df.loc[stock_code, '수익률'] = 수익률
          else:
            logger.info(f'종목코드: {stock_code}, 평균단가: {mean_buy_price} 로 return')
            return

          보유수량 = int(self.realtime_watchlist_df.loc[stock_code, "보유수량"])
          트레일링스탑발동여부 = self.realtime_watchlist_df.loc[stock_code, "트레일링스탑발동여부"]
          if self.stopLossGroupBox.isChecked() and 보유수량 > 0 and 수익률 < float( self.stopLossLineEdit.text()):
            logger.info(f"종목코드 : {stock_code} 수익률: {수익률} 으로 매도 진행")
            self.do_sell(stock_code, 매도주문수량=보유수량, 매도주문가=0, 주문유형="01") # 시장가 매도
            self.realtime_watchlist_df.drop(stock_code, inplace=True)
          elif not 트레일링스탑발동여부 and self.trailingStopGroupBox.isChecked() and 보유수량 > 0 and 수익률 > float(self.trailingStopUpperLineEdit.text()):
            self.realtime_watchlist_df.loc[stock_code, '트레일링스탑발동여부'] = True
            self.realtime_watchlist_df.loc[stock_code, '트레일링스탑발동후고가'] = now_price
            logger.info( f"종목코드: {stock_code} 수익률: {수익률} > {self.trailingStopUpperLineEdit.text()} 으로 Trailing Stopped!")
          elif 트레일링스탑발동여부 and self.trailingStopGroupBox.isChecked() and 보유수량 > 0:
            트레일링스탑발동후고가 = max(self.realtime_watchlist_df.loc[stock_code, 트레일링스탑발동후고가], now_price )
            고가대비현재등락률 = ( now_price - 트레일링스탑발동후고가 ) / 트레일링스탑발동후고가 * 100
            if 고가대비현재등락률 < -float(self.trailingStopLowerLineEidt.text()):
              logger.info(f"종목코드: {stock_code} 고가대비 현재 등락률: {고가대비현재등락률: .2f} < {self.trailingStopLowerLineEdit.text()} 으로 Trailing Stopped. Sold")
              self.realtime_watchlist_df.drop(stock_code, inplace=True)
    except Exception as e:
      logger.exception(e)

    self.timer1.start(10) # 0.01초 마다 한번 

          


# def main():
#   with open('config.yaml', 'r') as f:
#     config = yaml.load(f, Loader=yaml.FullLoader)

#   env_cls = KoreaInvestEnv(config)
#   base_headers = env_cls.get_base_headers()
#   cfg = env_cls.get_full_config()
#   korea_invest_api = KoreaInvestAPI(cfg, base_headers=base_headers)

#   websocket_url = cfg['paper_websocket_url'] if cfg['is_paper_trading'] else cfg['websocket_url']

#   run_websocket(korea_invest_api, websocket_url)

#   print(korea_invest_api)
#   print ( "------------------- Initialized -----------------\n\n")


if __name__ == '__main__':
  with open("./config.yaml", "r", encoding="UTF-8") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

  env_cls = KoreaInvestEnv(config)
  base_headers = env_cls.get_base_headers()
  cfg = env_cls.get_full_config()
  korea_invest_api = KoreaInvestAPI(cfg, base_headers=base_headers)

  
  tr_req_queue = Queue() # 주문 요청 큐
  tr_result_queue = Queue() # 주문 결과 큐
  
  ws_req_queue = Queue() # WebSocket 요청 큐
  ws_result_queue  = Queue() # WebSocket 결과 큐

  # 주문 Process  
  proc_order_tr = Process(
    target=send_tr_process, 
    args=(korea_invest_api, tr_req_queue, tr_result_queue))
  proc_order_tr.start()

  # 실시간 WebSocket Process
  websocket_url = cfg['paper_websocket_url'] if cfg['is_paper_trading'] else cfg['websocket_url']
  proc_realtime_ws = Process(
    target=run_websocket,
    args=(korea_invest_api, websocket_url, ws_req_queue, ws_result_queue))
  proc_realtime_ws.start()

  # UI - for Qt
  ###
  '''
  from PyQt5.QtWidgets import QApplication
  import sys
  from kis_stock_main_window import KoreaInvestMainWindow
  app = QApplication(sys.argv)
  main_app = KoreaInvestMainWindow(
    korea_invest_api, 
    req_in_queue, 
    tr_req_queue, 
    tr_result_queue, 
    realtime_data_out_queue)
  main_app.show()
  sys.exit(app.exec_())
  ###
  '''

  main()