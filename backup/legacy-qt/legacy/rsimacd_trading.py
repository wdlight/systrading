import os
import sys
from multiprocessing import Process, Process, Queue
import json
from base64 import b64decode
import time
from tkinter import W
import yaml
from loguru import logger
from utils import KoreaInvestEnv, KoreaInvestAPI
from Crypto.Cipher import AES
from base64 import b64decode
from Crypto.Util.Padding import pad, unpad

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QSettings, QTimer, QAbstractTableModel, QEvent
from PyQt5 import uic, QtGui

import pandas as pd
import talib as ta

form_class = uic.loadUiType("kismain.ui")[0]


def send_tr_process(korea_invest_api, tr_req_queue:Queue, tr_result_queue:Queue):
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

        #12일, 26일 단순 이동 평균(SMA) 계산
        df['EMA_fast'] = df['종가'].ewm(span=9, adjust=False).mean()
        df['EMA_slow'] = df['종가'].ewm(span=18, adjust=False).mean()
        #SMA기반 MACD 계산 ( Fast SMA - Slow SMA )
        df['MACD'] = df['EMA_fast'] - df['EMA_slow']
        #시그널 라인 : MACD의 9일 단순 이동 평균(SMA)
        df['MACD_signal'] = df['MACD'].ewm(span=6, adjust=False).mean()
        df['RSI'] = ta.RSI( df['종가'], timeperiod=14)


       # df['MACD'], df['MACD_signal'], _ = ta.MACD(df['종가'], fastperiod=9, slowperiod=18, signalperiod=6)
       # df['RSI'] = ta.RSI(df['종가'], timeperiod=14 )
        tr_result_queue.put(
          dict(
            action_id='1분봉조회',
            df=df,
            종목코드=data['종목코드'],
          )
        )


        logger.info(f"계좌조회 결과를 큐에 저장 완료 - 총잔고: {total_balance}, DataFrame 타입: {type(per_code_balance_df)}")

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
        column_name = self._data.columns[index.column()]
        value = self._data.iloc[index.row(), index.column()]
        
        # 수익률 컬럼 포맷팅
        if column_name == '수익률':
          try:
            if pd.notna(value):
              num_value = float(value)
              if num_value > 0:
                return f"(+){num_value:.2f}%"
              elif num_value < 0:
                return f"(-){abs(num_value):.2f}%"
              else:
                return f"{num_value:.2f}%"
          except (ValueError, TypeError):
            pass
        # 전일대비 등락률 소수점 2자리
        elif column_name == '전일대비':
          try:
            if pd.notna(value):
              num_value = float(value)
              return f"{num_value:.2f}"
          except (ValueError, TypeError):
            pass
        
        return str(value)
      elif role == Qt.ForegroundRole:
        # 수익률 컬럼에 색상 적용
        column_name = self._data.columns[index.column()]
        if column_name == '수익률':
          value = self._data.iloc[index.row(), index.column()]
          try:
            if pd.notna(value) and float(value) > 0:
              return QtGui.QColor(255, 0, 0)  # 빨간색 (상승)
            elif pd.notna(value) and float(value) < 0:
              return QtGui.QColor(0, 0, 255)  # 파란색 (하락)
          except (ValueError, TypeError):
            pass
      elif role == Qt.TextAlignmentRole:
        # 모든 컬럼을 우측 정렬
        return Qt.AlignRight | Qt.AlignVCenter
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



    # 타이머는 이미 __init__에서 시작됨 

          


"""
QT Designer
"""
class KISAPIForm(QMainWindow, form_class):
  def __init__(
    self,
    korea_invest_api,
    tr_req_queue: Queue,
    tr_result_queue: Queue,
  ):
    super().__init__()
    self.korea_invest_api = korea_invest_api
    self.tr_req_queue = tr_req_queue
    self.tr_result_queue = tr_result_queue
    self.setupUi(self)
    self.settings = QSettings('MyApp', 'myApp')
    self.load_settings()
    
    # self.input_groupbox_items_map_list = []
    # self.input_groubox_list = [
    #   self.groupBox1, self.groupBox2, 
    # ]

    self.index_num_to_stock_code_map = dict()
    self.stock_code_to_index_num_map = dict()
    self.stock_code_to_realtime_price_map = dict()
    self.realtime_registered_codes = set()


    self.account_info_df = pd.DataFrame(
      columns=['종목코드', '종목명', '보유수량', '매도가능수량', '매입단가', '수익률', '현재가', '전일대비', '등락']
    )

    try:
      self.realtime_watchlist_df = pd.read_pickle("realtime_watchlist_df.pkl")
    except FileNotFoundError:
      self.realtime_watchlist_df = pd.DataFrame(
        columns=['현재가', '수익률', '평균단가', "보유수량","MACD", "MACD시그널", "RSI", "트레일링스탑발동여부", "트레일링스탑발동후고가"]
      )
      logger.info("새로운 실시간 감시목록 데이터프레임 생성")

    # 타이머 설정
    self.timer1 = QTimer()
    self.timer1.timeout.connect(self.save_settings)
    self.timer1.start(10000)  # 0.1초마다 체크


    self.timer2 = QTimer()
    self.timer2.timeout.connect(self.req_balance)
    self.timer2.start(2000)

    self.timer3 = QTimer()
    self.timer3.timeout.connect(self.receive_tr_result)
    self.timer3.start(50) # 0.05초마다 한다.

    self.timer4 = QTimer()
    self.timer4.timeout.connect(self.req_ranking)
    self.timer4.start(2000)
    
  def req_ranking(self):
    self.tr_req_queue.put(dict(action_id='등락률상위'))

  def load_settings(self):
    self.resize(self.settings.value("size", self.size()))
    self.move(self.settings.value("pos", self.pos()))
    self.buyAmountLineEdit.setText(self.settings.value('buyAmountLineEdit', 100000, type=str))
    self.buyMACDTypeComboBox.setCurrentIndex(self.settings.value('buyAmountMACDTypeComboBox',0,  type=int))
    self.buyRSITypeComboBox.setCurrentIndex(self.settings.value('buyAmountRSITypeComboBox',0,  type=int))
    self.sellMACDTypeComboBox.setCurrentIndex(self.settings.value('sellAmountMACDTypeComboBox',0,  type=int))
    self.sellRSITypeComboBox.setCurrentIndex(self.settings.value('sellAmountRSITypeComboBox', 0, type=int))
    self.buyRSIValueSpinBox.setValue(self.settings.value('buyRSIValueSpinBox', 0, type=int))
    self.sellRSIValueSpinBox.setValue(self.settings.value('sellRSIValueSpinBox', 0, type=int))

  def save_settings(self):
    self.settings.setValue("size", self.size())
    self.settings.setValue("pos", self.pos())

    self.settings.setValue("buyAmountLineEdit", self.buyAmountLineEdit.text())
    self.settings.setValue("buyMACDTypeComboBox", self.buyMACDTypeComboBox.currentIndex())
    self.settings.setValue("buyRSITypeComboBox", self.buyRSITypeComboBox.currentIndex())
    self.settings.setValue("sellMACDTypeComboBox", self.sellMACDTypeComboBox.currentIndex())
    self.settings.setValue("sellRSITypeComboBox", self.sellRSITypeComboBox.currentIndex())
    self.settings.setValue("buyRSIValueSpinBox", self.buyRSIValueSpinBox.value())
    self.settings.setValue("sellRSIValueSpinBox", self.sellRSIValueSpinBox.value())

    self.realtime_watchlist_df.to_pickle("realtime_watchlist_df.pkl")

  def do_buy(self, 종목코드, 매수주문수량, 매수주문가, 주문유형="00"):
    self.tr_req_queue.put(
      dict(
        action_id="매수",
        종목코드=종목코드,
        매수주문수량=매수주문수량,
        매수주문가=매수주문가,
        주문유형=주문유형
      )
    )

  def do_sell(self, 종목코드, 매도주문수량, 매도주문가, 주문유형="00"):
    self.tr_req_queue.put(
      dict(
        action_id="매도",
        종목코드=종목코드,
        매도주문수량=매도주문수량,
        매도주문가=매도주문가,
        주문유형=주문유형
      )
    )

  def closeEvent(self, e):
    logger.info("프로그램 종료 시작")
    self.save_settings()
    self.tr_req_queue.put(
      dict( action_id="종료")
    )
    logger.info("프로그램 종료 완료")

  sys._excepthook = sys.excepthook

  def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    logger.info(f"exctype: {exctype}, value: {value}, traceback: {traceback}")
    # call the normal exception hook after
    sys._excepthook(exctype, value, traceback)


  def pop_from_realtime_tracking_list(self, stock_code=None):
    #stock_code = self.inOutStockCodeLIneEdit.text()
    self.realtime_watchlist_df.drop(stock_code, inplace=True)

  

  def push_to_Realtime_tracking_list(self):
    stock_code = self.inOutStockCodeLineEdit.text()
    self.realtime_watchlist_df.loc[stock_code] = {
      '현재가': None,
      '수익률': None,
      '평균단가': None,
      '보유수량': 0,
      '트레일링스탑발동여부': False,
      '트레일링스탑발동후고가': None
    }



  def receive_tr_result(self):
    """
    """
    if not self.tr_result_queue.empty():
      logger.info("TR 결과 큐에서 데이터 수신!")
      data = self.tr_result_queue.get()
      logger.info(f"수신된 데이터 action_id: {data.get('action_id', 'Unknown')}")

      if data['action_id'] == '계좌조회' :
        logger.info("계좌조회 결과 처리 시작")
        self.on_balance_req( data['total_balance'], data['per_code_balance_df'] )

      elif data['action_id'] == '1분봉조회' :
        logger.info("1분봉조회 결과 처리 시작")
        print(f'1분봉조회 ===================== \n{df}')
        종목코드= data['종목코드']
        df = data['df']
        종가 = df['종가'].iloc[-1] 
        전MACD = df['MACD'].iloc[-2]
        현MACD = df['MACD'].iloc[-1]
        전MACD_signal = df['MACD_signal'].iloc[-2]
        현MACD_signal = df['MACD_signal'].iloc[-1]
        전RSI = df['RSI'].iloc[-2]
        현RSI = df['RSI'].iloc[-1]


        # RSI & MACD 매수/매도 조건 체크
        if 종목코드 in self.realtime_watchlist_df.index:
          # 매도 Case

          self.realtime_watchlist_df.loc[종목코드, '현재가'] = 종가
          평균단가 = self.realtime_watchlist_df.loc[종목코드, '평균단가']
          logger.info(f"[수익률계산-매도케이스] 종목코드: {종목코드}, 종가: {종가}, 평균단가: {평균단가}")
          if not pd.isnull(평균단가):
            수익률 = round( (종가-평균단가)/ 평균단가 * 100, 2)
            self.realtime_watchlist_df.loc[종목코드, '수익률'] = 수익률
            logger.info(f"[수익률계산-매도케이스] 수익률 업데이트: {수익률}%")
          else:
            logger.info(f"[수익률계산-매도케이스] 평균단가가 None이므로 수익률 계산 불가")

          # 매도 조건
          #self.realtime_watchlist_df.loc[종목코드, '현재가'] = df['종가'].iloc[-1]
          self.realtime_watchlist_df.loc[종목코드, 'MACD'] = round( 현MACD, 2)
          self.realtime_watchlist_df.loc[종목코드, 'MACD시그널'] = round( 현MACD_signal,2)
          self.realtime_watchlist_df.loc[종목코드, 'RSI'] = round( 현RSI, 2)


          if self.sellMACDTypeComboBox.currentText() == "상향돌파":
            macd_signal = 현MACD >= 현MACD_signal and 전MACD < 전MACD_signal
          elif self.sellMACDTypeComboBox.currentText() == "하향돌파":
            macd_signal = 현MACD <= 현MACD_signal and 전MACD > 전MACD_signal
          elif self.sellMACDTypeComboBox.currentText() == "이상":
            macd_signal = 현MACD >= 현MACD_signal
          elif self.sellMACDTypeComboBox.currentText() == "이하":
            macd_signal = 현MACD <= 현MACD_signal
          else:
            raise NotImplementedError

          rsi_value = self.sellRSIValueSpinBox.value()
          if self.sellRSITypeComboBox.currentText() == "상향돌파":
            rsi_signal = 현RSI >= rsi_value and 전RSI < rsi_value
          elif self.sellRSITypeComboBox.currentText() == "하향돌파":
            rsi_signal = 현RSI <= rsi_value and 전RSI > rsi_value
          elif self.sellRSITypeComboBox.currentText() == "이상":
            rsi_signal = 현RSI >= rsi_value
          elif self.sellRSITypeComboBox.currentText() == "이하":
            rsi_signal = 현RSI <= rsi_value
          else:
            raise NotImplementedError

          if macd_signal and rsi_signal:
            logger.info(f'종목코드: {종목코드} 매도 주문!')                        
            매도주문수량 = self.realtime_watchlist_df.loc[종목코드,'보유수량']

            if 매도주문수량 == 0:
              logger.info(f'종목코드: {종목코드} 매도 주문수량: {매도주문수량}으로 매도  주문 실패!')
              return
            self.do_sell(종목코드, 매도주문수량, 0, 주문유형='01')
            self.realtime_watchlist_df.drop( 종목코드, inplace=True)



          
        else:
          # 매수 & watchlist 추가.
            
          self.realtime_watchlist_df.loc[종목코드, '현재가'] = 종가
          평균단가 = self.realtime_watchlist_df.loc[종목코드, '평균단가']
          logger.info(f"[수익률계산-매수케이스] 종목코드: {종목코드}, 종가: {종가}, 평균단가: {평균단가}")
          if not pd.isnull(평균단가):
            수익률 = round( (종가-평균단가)/ 평균단가 * 100, 2)
            self.realtime_watchlist_df.loc[종목코드, '수익률'] = 수익률
            logger.info(f"[수익률계산-매수케이스] 수익률 업데이트: {수익률}%")
          else:
            logger.info(f"[수익률계산-매수케이스] 평균단가가 None이므로 수익률 계산 불가")


          # 매수 조건          
          if self.buyMACDTypeComboBox.currentText() == "상향돌파":
            macd_signal = 현MACD >= 현MACD_signal and 전MACD < 전MACD_signal
          elif self.buyMACDTypeComboBox.currentText() == "하향돌파":
            macd_signal = 현MACD <= 현MACD_signal and 전MACD > 전MACD_signal
          elif self.buyMACDTypeComboBox.currentText() == "이상":
            macd_signal = 현MACD >= 현MACD_signal
          elif self.buyMACDTypeComboBox.currentText() == "이하":
            macd_signal = 현MACD <= 현MACD_signal
          else:
            raise NotImplementedError

          rsi_value = self.buyRSIValueSpinBox.value()
          if self.buyRSITypeComboBox.currentText() == "상향돌파":
            rsi_signal = 현RSI >= rsi_value and 전RSI < rsi_value
          elif self.buyRSITypeComboBox.currentText() == "하향돌파":
            rsi_signal = 현RSI <= rsi_value and 전RSI > rsi_value
          elif self.buyRSITypeComboBox.currentText() == "이상":
            rsi_signal = 현RSI >= rsi_value
          elif self.buyRSITypeComboBox.currentText() == "이하":
            rsi_signal = 현RSI <= rsi_value
          else:
            raise NotImplementedError

          if macd_signal and rsi_signal:
            logger.info(f'종목코드: {종목코드} 매수 주문!')
            현재가 = df['종가'].iloc[-1]
            매수주문금액 = int (self.buyAmountLineEdit.text())
            매수주문수량 = 매수주문금액 // 현재가 

            if 매수주문수량 == 0:
              logger.info(f'종목코드: {종목코드} 매수주문수량: {매수주문수량}으로 매수 주문 실패!')
              return
            self.do_buy(종목코드, 매수주문수량, 0, 주문유형='01')
            logger.info(f"[매수주문] 종목코드: {종목코드} watchlist에 추가 - 현재가: {현재가}, 매수주문수량: {매수주문수량}")
            self.realtime_watchlist_df.loc[종목코드] = {
              '현재가': 현재가,
              '수익률': 0,
              '평균단가': None,  # 매수 주문 시점에는 None
              '보유수량': 0,     # 주문 완료 전이므로 0
              'MACD': 현MACD,
              'MACD시그널': 현MACD_signal,
              'RSI': 현RSI,
              '트레일링스탑발동여부': False,
              '트레일링스탑발동후고가': None
            }

      elif data['action_id'] == '등락률상위' :
        logger.info("1분봉조회 결과 처리 시작")
        df = data['df']        
        for code in df['종목코드'] :
          self.tr_req_queue.put(
            dict(
              action_id='1분봉조회',
              종목코드=code,
            )
          )
        
        # RSI & MACD 매수/매도 조건 체크
  

      else:
        logger.warning(f"알 수 없는 action_id: {data.get('action_id', 'Unknown')}")
    # 큐가 비어있을 때는 로그 출력하지 않음 (너무 많아짐)

  def req_balance(self):
    logger.info("계좌조회 요청을 큐에 전송")
    self.tr_req_queue.put( dict( action_id="계좌조회"))
    logger.info(f"계좌조회 요청 큐 전송 완료 - 큐 크기: {self.tr_req_queue.qsize()}")


  def on_balance_req(self, total_balance, per_code_balance_df):
    logger.info(f"계좌조회 결과 처리 - 총잔고: {total_balance}")
    
    if total_balance is None:
      logger.error("총 잔고가 None입니다")
      return
    
    if per_code_balance_df is None:
      logger.error("종목별 잔고 데이터프레임이 None입니다")
      return
      
    logger.info(f"종목별 잔고 데이터 행 수: {len(per_code_balance_df)}")
    
    self.domesticCurrentBalanceLabel.setText(f"현재 평가 잔고: { total_balance: ,}원")
    logger.info(f"UI 잔고 라벨 업데이트 완료: {total_balance:,}원")
    
    self.account_info_df = per_code_balance_df[per_code_balance_df['보유수량'] != 0]
    logger.info(f"보유중인 종목 수: {len(self.account_info_df)}")
    for row in self.account_info_df.itertuples():
      stock_code = getattr(row, "종목코드")
      보유수량 = getattr(row,"보유수량")
      매입단가 = getattr(row,"매입단가")
      logger.info(f"[계좌조회] 종목코드: {stock_code}, 보유수량: {보유수량}, 매입단가: {매입단가}")

      if stock_code in self.realtime_watchlist_df.index:
        self.realtime_watchlist_df.loc[stock_code, "보유수량"] = 보유수량
        self.realtime_watchlist_df.loc[stock_code, "평균단가"] = 매입단가
        logger.info(f"[계좌조회] watchlist 업데이트: {stock_code} - 보유수량: {보유수량}, 평균단가: {매입단가}")

    logger.info(f'{self.account_info_df}')

    logger.info(f"[UI업데이트] account_info_df 내용:\n{self.account_info_df.to_string()}")
    logger.info(f"[UI업데이트] realtime_watchlist_df 내용:\n{self.realtime_watchlist_df.to_string()}")
    
    self.account_model = PandasModel(self.account_info_df)
    self.accountTableView.setModel( self.account_model)

    realtime_tracking_model = PandasModel(self.realtime_watchlist_df.copy(deep=True))
    self.watchListTableView.setModel(realtime_tracking_model)

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
            수익률 = round( (now_price - mean_buy_price) / mean_buy_price * 100, 2) # 수수료는 별도 계산
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
            트레일링스탑발동후고가 = max(self.realtime_watchlist_df.loc[stock_code, '트레일링스탑발동후고가'], now_price)
            고가대비현재등락률 = ( now_price - 트레일링스탑발동후고가 ) / 트레일링스탑발동후고가 * 100
            if 고가대비현재등락률 < -float(self.trailingStopLowerLineEdit.text()):
              logger.info(f"종목코드: {stock_code} 고가대비 현재 등락률: {고가대비현재등락률: .2f} < {self.trailingStopLowerLineEdit.text()} 으로 Trailing Stopped. Sold")
              self.realtime_watchlist_df.drop(stock_code, inplace=True)
    except Exception as e:
      logger.exception(e)




if __name__ == '__main__':
  with open("./config.yaml", "r", encoding="UTF-8") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

  env_cls = KoreaInvestEnv(config)
  base_headers = env_cls.get_base_headers()
  cfg = env_cls.get_full_config()
  korea_invest_api = KoreaInvestAPI(cfg, base_headers=base_headers)

  
  tr_req_queue = Queue() # 주문 요청 큐
  tr_result_queue = Queue() # 주문 결과 큐
  
  #ws_req_queue = Queue() # WebSocket 요청 큐
  #ws_result_queue  = Queue() # WebSocket 결과 큐

  # 주문 Process  
  proc_order_tr = Process(
    target=send_tr_process, 
    args=(korea_invest_api, tr_req_queue, tr_result_queue))
  proc_order_tr.start()

  # 실시간 WebSocket Process
  # websocket_url = cfg['paper_websocket_url'] if cfg['is_paper_trading'] else cfg['websocket_url']
  # proc_realtime_ws = Process(
  #   target=run_websocket,
  #   args=(korea_invest_api, websocket_url, ws_req_queue, ws_result_queue))
  # proc_realtime_ws.start()

  app = QApplication(sys.argv)
  main_app = KISAPIForm(
    korea_invest_api, 
    tr_req_queue, 
    tr_result_queue, 
    )
  main_app.show()
  sys.exit(app.exec_())
