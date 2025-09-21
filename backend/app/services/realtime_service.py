"""
실시간 데이터 서비스
기존 PyQt5의 타이머 기반 로직을 async/await로 변환
"""

import asyncio
import pandas as pd
from datetime import datetime
from loguru import logger
from typing import Dict, Any, Optional, List
from queue import Queue, Empty

from app.websocket.connection import ConnectionManager
from app.core.korea_invest import KoreaInvestAPIService



class RealtimeDataService:
    """실시간 데이터 처리 서비스"""
    
    def __init__(self, korea_invest_service: KoreaInvestAPIService, connection_manager: ConnectionManager, ws_result_queue: Queue):
        self.korea_invest_service = korea_invest_service
        self.connection_manager = connection_manager
        self.ws_result_queue = ws_result_queue  # 웹소켓 결과 수신 큐
        self.is_running = False
        self.tasks = []
        
        # 기존 DataFrame 구조 유지
        self.realtime_watchlist_df = pd.DataFrame(columns=[
            '현재가', '수익률', '평균단가', '보유수량', 'MACD', 'MACD시그널', 
            'RSI', '트레일링스탑발동여부', '트레일링스탑발동후고가'
        ])
        self.account_info_df = pd.DataFrame()
        
        # 설정값들 (기존 PyQt5 애플리케이션에서 가져올 예정)
        self.trading_conditions = {
            "buy_conditions": {
                "amount": 100000,
                "macd_type": "상향돌파",
                "rsi_value": 30,
                "rsi_type": "이상"
            },
            "sell_conditions": {
                "macd_type": "하향돌파", 
                "rsi_value": 70,
                "rsi_type": "이하"
            }
        }
        
        logger.info("실시간 데이터 서비스가 초기화되었습니다.")
    
    async def start(self):
        """실시간 데이터 서비스 시작"""
        if self.is_running:
            logger.warning("실시간 서비스가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        logger.info("실시간 데이터 서비스를 시작합니다.")
        
        try:
            # 기존 타이머들을 async task로 변환
            self.tasks = [
                asyncio.create_task(self._account_update_loop()),     # 2초 주기 (timer2)
                asyncio.create_task(self._tr_result_loop()),          # 0.05초 주기 (timer3)  
                asyncio.create_task(self._market_data_loop()),        # 2초 주기 (timer4)
                asyncio.create_task(self._settings_save_loop()),      # 10초 주기 (timer1)
                asyncio.create_task(self._heartbeat_loop())           # 30초 주기 (하트비트)
            ]
            
            # 모든 태스크가 완료될 때까지 대기 (실제로는 무한 루프)
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"실시간 서비스 실행 중 오류: {str(e)}")
            await self.stop()
    
    async def stop(self):
        """실시간 데이터 서비스 중지"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("실시간 데이터 서비스를 중지합니다.")
        
        # 모든 태스크 취소
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # 태스크 완료 대기
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks = []
        logger.info("실시간 데이터 서비스가 중지되었습니다.")
    
    async def _account_update_loop(self):
        """계좌 정보 업데이트 루프 (기존 timer2 로직)"""
        logger.info("계좌 업데이트 루프 시작 (2초 주기)")
        
        while self.is_running:
            try:
                # 기존 update_account_info() 로직
                account_data = await self._update_account_info()
                
                if account_data:
                    # WebSocket으로 계좌 정보 브로드캐스트
                    await self.connection_manager.broadcast({
                        "type": "account_update",
                        "data": account_data,
                        "timestamp": datetime.now().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"계좌 업데이트 중 오류: {str(e)}")
            
            await asyncio.sleep(2)  # 2초 대기
    
    async def _tr_result_loop(self):
        """TR 결과 처리 루프 (기존 timer3 로직)"""
        # logger.info("TR 결과 처리 루프 시작 (0.05초 주기)") # 로그가 너무 많이 쌓이므로 주석 처리
        
        while self.is_running:
            try:
                # 기존 receive_tr_result() 로직
                await self._process_tr_results()
                
            except Exception as e:
                logger.error(f"TR 결과 처리 중 오류: {str(e)}")
            
            await asyncio.sleep(0.05)  # 0.05초 대기
    
    async def _market_data_loop(self):
        """시장 데이터 업데이트 루프 (기존 timer4 로직)"""
        logger.info("시장 데이터 업데이트 루프 시작 (2초 주기)")
        
        while self.is_running:
            try:
                # 워치리스트 업데이트 및 브로드캐스트
                watchlist_data = await self._update_watchlist()
                
                if watchlist_data:
                    await self.connection_manager.broadcast({
                        "type": "watchlist_update",
                        "data": watchlist_data,
                        "timestamp": datetime.now().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"시장 데이터 업데이트 중 오류: {str(e)}")
            
            await asyncio.sleep(2)  # 2초 대기
    
    async def _settings_save_loop(self):
        """설정 저장 루프 (기존 timer1 로직)"""
        logger.info("설정 저장 루프 시작 (10초 주기)")
        
        while self.is_running:
            try:
                # 기존 save_setting() 로직
                await self._save_settings()
                
            except Exception as e:
                logger.error(f"설정 저장 중 오류: {str(e)}")
            
            await asyncio.sleep(10)  # 10초 대기
    
    async def _heartbeat_loop(self):
        """하트비트 루프 (연결 상태 확인)"""
        logger.info("하트비트 루프 시작 (30초 주기)")
        
        while self.is_running:
            try:
                await self.connection_manager.send_heartbeat()
                
            except Exception as e:
                logger.error(f"하트비트 전송 중 오류: {str(e)}")
            
            await asyncio.sleep(30)  # 30초 대기
    
    async def _update_account_info(self) -> Optional[Dict[str, Any]]:
        """계좌 정보 업데이트 (기존 update_account_info 로직)"""
        try:
            # 한국투자증권 API 호출
            balance_data = await self.korea_invest_service.get_account_balance()
            
            if balance_data and isinstance(balance_data.get("dataframe"), pd.DataFrame):
                self.account_info_df = balance_data["dataframe"]
                
                # 워치리스트 평균단가, 보유수량 업데이트
                for stock_code in self.realtime_watchlist_df.index:
                    if stock_code in self.account_info_df.index:
                        row = self.account_info_df.loc[stock_code]
                        avg_price = row.get("매입단가", 0)
                        quantity = row.get("보유수량", 0)
                        
                        if avg_price and avg_price > 0:
                            self.realtime_watchlist_df.loc[stock_code, "평균단가"] = avg_price
                        if quantity and quantity > 0:
                            self.realtime_watchlist_df.loc[stock_code, "보유수량"] = quantity

                return {
                    "total_value": balance_data["total_value"],
                    "available_cash": balance_data["available_cash"],
                    "total_purchase_amount": self.account_info_df['매입금액'].sum() if '매입금액' in self.account_info_df else 0,
                    "total_evaluation_amount": self.account_info_df['평가금액'].sum() if '평가금액' in self.account_info_df else 0,
                    "total_profit_loss": self.account_info_df['평가손익'].sum() if '평가손익' in self.account_info_df else 0,
                    "total_profit_loss_rate": balance_data.get("total_profit_loss_rate", 0),
                    "positions": balance_data["positions"]
                }
            
        except Exception as e:
            logger.error(f"계좌 정보 업데이트 실패: {e}")
        
        return None
    
    async def _process_tr_results(self):
        """TR 결과 처리 (큐에서 데이터 가져와 DF 업데이트)"""
        try:
            result = self.ws_result_queue.get_nowait()
        except Empty:
            return

        action_id = result.get('action_id')
        
        try:
            if action_id == '실시간호가' or action_id == '실시간체결': # domestic_websocket.py와 ID 일치 필요
                data = result.get('data', {})
                stock_code = data.get('종목코드')
                
                # '현재가' 키가 있는지 확인
                if '현재가' not in data:
                    return

                current_price_str = data.get('현재가')

                if stock_code and current_price_str and stock_code in self.realtime_watchlist_df.index:
                    current_price = abs(int(current_price_str))
                    self.realtime_watchlist_df.loc[stock_code, '현재가'] = current_price
                    
                    # 수익률 계산
                    avg_price = self.realtime_watchlist_df.loc[stock_code, '평균단가']
                    if avg_price and pd.notna(avg_price) and avg_price > 0:
                        profit_rate = ((current_price - avg_price) / avg_price) * 100
                        self.realtime_watchlist_df.loc[stock_code, '수익률'] = profit_rate

            elif action_id == '주문체결통보':
                logger.info(f"주문체결통보 수신: {result}")
                # 계좌 정보 즉시 업데이트 요청
                await self._update_account_info()

        except (ValueError, TypeError) as e:
            logger.error(f"실시간 데이터 처리 중 오류: {e} - 데이터: {result}")
        except Exception as e:
            logger.error(f"TR 결과 처리 중 예상치 못한 오류: {e}")
    
    async def _update_watchlist(self) -> List[Dict[str, Any]]:
        """워치리스트 DataFrame을 API 응답 형태로 변환"""
        try:
            watchlist_data = []
            
            for stock_code in self.realtime_watchlist_df.index:
                row = self.realtime_watchlist_df.loc[stock_code]
                
                item = {
                    "stock_code": stock_code,
                    "stock_name": row.get("종목명", ""), # 종목명 추가
                    "current_price": int(row.get("현재가", 0)),
                    "profit_rate": round(float(row.get("수익률", 0.0)), 2),
                    "avg_price": int(row.get("평균단가", 0)) if pd.notna(row.get("평균단가")) else None,
                    "quantity": int(row.get("보유수량", 0)),
                    "macd": float(row.get("MACD", 0.0)),
                    "macd_signal": float(row.get("MACD시그널", 0.0)),
                    "rsi": float(row.get("RSI", 0.0)),
                    "trailing_stop_activated": bool(row.get("트레일링스탑발동여부", False)),
                    "trailing_stop_high": int(row.get("트레일링스탑발동후고가", 0)) if pd.notna(row.get("트레일링스탑발동후고가")) else None,
                    "volume": int(row.get("거래량", 0)),
                    "change_amount": int(row.get("전일대비", 0)),
                    "change_rate": float(row.get("등락률", 0.0)),
                    "updated_at": datetime.now().isoformat()
                }
                
                watchlist_data.append(item)
            
            return watchlist_data
            
        except Exception as e:
            logger.error(f"워치리스트 업데이트 실패: {str(e)}")
            return []
    
    async def _save_settings(self):
        """설정 저장"""
        # 필요시 구현
        pass
    
    # 외부에서 호출할 수 있는 메서드들
    
    async def add_to_watchlist(self, stock_code: str, stock_name: str = "") -> bool:
        """워치리스트에 종목 추가"""
        try:
            if stock_code not in self.realtime_watchlist_df.index:
                self.realtime_watchlist_df.loc[stock_code] = {
                    '현재가': 0, '수익률': 0, '평균단가': None, '보유수량': 0,
                    'MACD': 0.0, 'MACD시그널': 0.0, 'RSI': 0.0,
                    '트레일링스탑발동여부': False, '트레일링스탑발동후고가': None,
                    '종목명': stock_name, '거래량': 0, '전일대비': 0, '등락률': 0.0
                }
                logger.info(f"워치리스트에 종목 {stock_code} ({stock_name}) 추가")
                # TODO: domestic_websocket에 실시간 시세 등록 요청 보내기
                return True
            else:
                logger.warning(f"종목 {stock_code}은 이미 워치리스트에 있습니다.")
                return False
                
        except Exception as e:
            logger.error(f"워치리스트 추가 실패: {str(e)}")
            return False
    
    async def remove_from_watchlist(self, stock_code: str) -> bool:
        """워치리스트에서 종목 제거"""
        try:
            if stock_code in self.realtime_watchlist_df.index:
                self.realtime_watchlist_df.drop(stock_code, inplace=True)
                logger.info(f"워치리스트에서 종목 {stock_code} 제거")
                # TODO: domestic_websocket에 실시간 시세 해제 요청 보내기
                return True
            else:
                logger.warning(f"종목 {stock_code}이 워치리스트에 없습니다.")
                return False
                
        except Exception as e:
            logger.error(f"워치리스트 제거 실패: {str(e)}")
            return False
