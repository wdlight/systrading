"""
워치리스트 관리 서비스
PyQt5 rsimacd_trading.py의 워치리스트 관련 기능을 서비스로 분리
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging
import pandas as pd
import numpy as np
from copy import deepcopy

from app.models.watchlist_models import (
    WatchlistItem, 
    AddStockRequest, 
    PriceUpdateEvent,
    WatchlistUpdateEvent,
    WatchlistSummary,
    TechnicalIndicators,
    BuyConditions,
    SellConditions,
    TradingConditions,
    TradeExecutionResult,
    MarketDataSnapshot
)
from app.core.korea_invest import KoreaInvestAPIService
from app.services.technical_analysis_service import TechnicalAnalysisService

logger = logging.getLogger(__name__)

class WatchlistService:
    """워치리스트 관련 서비스"""
    
    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest_service = korea_invest_service
        
        # 워치리스트 데이터 (기존 realtime_watchlist_df와 동일한 구조)
        self.watchlist_df = pd.DataFrame(columns=[
            '현재가', '수익률', '평균단가', '보유수량', 'MACD', 'MACD시그널', 
            'RSI', '트레일링스탑발동여부', '트레일링스탑발동후고가'
        ])
        
        # 가격 히스토리 (기술적 지표 계산용)
        self.price_history = {}  # {stock_code: DataFrame}
        
        self.last_update = None
    
    async def get_watchlist(self) -> List[WatchlistItem]:
        """워치리스트 조회"""
        try:
            items = []
            
            for stock_code in self.watchlist_df.index:
                item = await self._create_watchlist_item(stock_code)
                if item:
                    items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"워치리스트 조회 실패: {str(e)}")
            return []
    
    async def get_watchlist_item(self, stock_code: str) -> Optional[WatchlistItem]:
        """특정 종목 정보 조회"""
        try:
            if stock_code not in self.watchlist_df.index:
                return None
            
            return await self._create_watchlist_item(stock_code)
            
        except Exception as e:
            logger.error(f"종목 {stock_code} 조회 실패: {str(e)}")
            return None
    
    async def _create_watchlist_item(self, stock_code: str) -> Optional[WatchlistItem]:
        """워치리스트 아이템 생성"""
        try:
            if stock_code not in self.watchlist_df.index:
                return None
            
            row = self.watchlist_df.loc[stock_code]
            
            return WatchlistItem(
                stock_code=stock_code,
                current_price=float(row.get("현재가", 0)),
                profit_rate=float(row.get("수익률", 0.0)),
                avg_price=float(row.get("평균단가", 0)) if pd.notna(row.get("평균단가")) else None,
                quantity=int(row.get("보유수량", 0)),
                macd=float(row.get("MACD", 0.0)),
                macd_signal=float(row.get("MACD시그널", 0.0)),
                rsi=float(row.get("RSI", 0.0)),
                trailing_stop_active=bool(row.get("트레일링스탑발동여부", False)),
                trailing_stop_high=float(row.get("트레일링스탑발동후고가", 0)) if pd.notna(row.get("트레일링스탑발동후고가")) else None
            )
            
        except Exception as e:
            logger.error(f"워치리스트 아이템 생성 실패 ({stock_code}): {str(e)}")
            return None
    
    async def add_stock(self, stock_code: str) -> Dict[str, Any]:
        """워치리스트에 종목 추가"""
        try:
            if stock_code in self.watchlist_df.index:
                return {
                    "success": False,
                    "message": f"종목 {stock_code}은 이미 워치리스트에 있습니다."
                }
            
            # 현재가 조회
            current_price_data = await self.korea_invest_service.get_current_price(stock_code)
            current_price = current_price_data["current_price"] if current_price_data else 0
            
            # 새로운 행 추가 (기존 로직과 동일 - 평균단가 None 문제 지점)
            self.watchlist_df.loc[stock_code] = {
                '현재가': current_price,
                '수익률': 0.0,
                '평균단가': current_price,  # 🔥 수정: None 대신 현재가 사용
                '보유수량': 0,
                'MACD': 0.0,
                'MACD시그널': 0.0,
                'RSI': 0.0,
                '트레일링스탑발동여부': False,
                '트레일링스탑발동후고가': None
            }
            
            # 가격 히스토리 초기화
            self.price_history[stock_code] = pd.DataFrame(columns=['close', 'timestamp'])
            
            logger.info(f"워치리스트에 종목 {stock_code} 추가 (초기 평균단가: {current_price})")
            
            return {
                "success": True,
                "message": f"종목 {stock_code}이 워치리스트에 추가되었습니다."
            }
            
        except Exception as e:
            logger.error(f"종목 {stock_code} 추가 실패: {str(e)}")
            return {
                "success": False,
                "message": f"종목 추가 실패: {str(e)}"
            }
    
    async def remove_stock(self, stock_code: str) -> Dict[str, Any]:
        """워치리스트에서 종목 제거"""
        try:
            if stock_code not in self.watchlist_df.index:
                return {
                    "success": False,
                    "message": f"종목 {stock_code}이 워치리스트에 없습니다."
                }
            
            # DataFrame에서 제거
            self.watchlist_df.drop(stock_code, inplace=True)
            
            # 가격 히스토리 제거
            if stock_code in self.price_history:
                del self.price_history[stock_code]
            
            logger.info(f"워치리스트에서 종목 {stock_code} 제거")
            
            return {
                "success": True,
                "message": f"종목 {stock_code}이 워치리스트에서 제거되었습니다."
            }
            
        except Exception as e:
            logger.error(f"종목 {stock_code} 제거 실패: {str(e)}")
            return {
                "success": False,
                "message": f"종목 제거 실패: {str(e)}"
            }
    
    async def get_technical_indicators(self, stock_code: str) -> Optional[TechnicalIndicators]:
        """기술적 지표 조회"""
        try:
            if stock_code not in self.watchlist_df.index:
                return None
            
            row = self.watchlist_df.loc[stock_code]
            
            return TechnicalIndicators(
                rsi=float(row.get("RSI", 0.0)),
                macd=float(row.get("MACD", 0.0)),
                macd_signal=float(row.get("MACD시그널", 0.0)),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"기술적 지표 조회 실패 ({stock_code}): {str(e)}")
            return None
    
    async def get_stock_price(self, stock_code: str) -> Optional[MarketDataSnapshot]:
        """실시간 가격 조회"""
        try:
            price_data = await self.korea_invest_service.get_current_price(stock_code)
            
            if price_data:
                return MarketDataSnapshot(
                    stock_code=stock_code,
                    open_price=price_data.get("open_price", price_data["current_price"]),
                    high_price=price_data.get("high_price", price_data["current_price"]),
                    low_price=price_data.get("low_price", price_data["current_price"]),
                    close_price=price_data["current_price"],
                    volume=price_data["volume"],
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"가격 조회 실패 ({stock_code}): {str(e)}")
            return None
    
    async def update_stock_data(self, stock_code: str, price: int) -> bool:
        """종목 데이터 업데이트 (실시간 가격 반영)"""
        try:
            if stock_code not in self.watchlist_df.index:
                return False
            
            # 현재가 업데이트
            self.watchlist_df.loc[stock_code, '현재가'] = price
            
            # 수익률 계산
            평균단가 = self.watchlist_df.loc[stock_code, '평균단가']
            if pd.notna(평균단가) and 평균단가 > 0:
                수익률 = round((price - 평균단가) / 평균단가 * 100, 2)
                self.watchlist_df.loc[stock_code, '수익률'] = 수익률
            
            # 가격 히스토리 업데이트
            if stock_code in self.price_history:
                new_row = pd.DataFrame({
                    'close': [price],
                    'timestamp': [datetime.now()]
                })
                self.price_history[stock_code] = pd.concat([
                    self.price_history[stock_code], new_row
                ], ignore_index=True)
                
                # 최근 200개 데이터만 유지 (메모리 관리)
                if len(self.price_history[stock_code]) > 200:
                    self.price_history[stock_code] = self.price_history[stock_code].tail(200)
                
                # 기술적 지표 계산
                await self._calculate_technical_indicators(stock_code)
            
            return True
            
        except Exception as e:
            logger.error(f"종목 데이터 업데이트 실패 ({stock_code}): {str(e)}")
            return False
    
    async def _calculate_technical_indicators(self, stock_code: str):
        """기술적 지표 계산 - TechnicalAnalysisService 사용"""
        try:
            if stock_code not in self.price_history:
                return
            
            df = self.price_history[stock_code]
            if len(df) < 20:  # 최소 데이터 개수 확인
                return
            
            # DataFrame 구조를 TechnicalAnalysisService에 맞게 변환
            minute_data = df.rename(columns={'close': '종가'})
            
            # 기술적 지표 계산
            indicators = TechnicalAnalysisService.calculate_all_indicators(minute_data)
            
            # 결과 업데이트
            if not np.isnan(indicators['rsi']):
                self.watchlist_df.loc[stock_code, 'RSI'] = indicators['rsi']
            if not np.isnan(indicators['macd']):
                self.watchlist_df.loc[stock_code, 'MACD'] = indicators['macd']
            if not np.isnan(indicators['macd_signal']):
                self.watchlist_df.loc[stock_code, 'MACD시그널'] = indicators['macd_signal']
            
        except Exception as e:
            logger.error(f"기술적 지표 계산 실패 ({stock_code}): {str(e)}")
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """RSI 계산"""
        try:
            if len(prices) < period + 1:
                return np.nan
            
            deltas = np.diff(prices)
            gain = np.where(deltas > 0, deltas, 0)
            loss = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gain[-period:])
            avg_loss = np.mean(loss[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception:
            return np.nan
    
    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """MACD 계산"""
        try:
            if len(prices) < slow:
                return np.nan, np.nan
            
            # EMA 계산
            def ema(data, period):
                alpha = 2 / (period + 1)
                ema_values = []
                ema_values.append(data[0])
                
                for i in range(1, len(data)):
                    ema_val = alpha * data[i] + (1 - alpha) * ema_values[-1]
                    ema_values.append(ema_val)
                
                return np.array(ema_values)
            
            ema_fast = ema(prices, fast)
            ema_slow = ema(prices, slow)
            
            macd_line = ema_fast - ema_slow
            macd_signal_line = ema(macd_line, signal)
            
            return macd_line[-1], macd_signal_line[-1]
            
        except Exception:
            return np.nan, np.nan
    
    async def refresh_all_data(self) -> Dict[str, Any]:
        """모든 워치리스트 데이터 갱신"""
        try:
            updated_count = 0
            
            for stock_code in self.watchlist_df.index:
                price_data = await self.korea_invest_service.get_current_price(stock_code)
                if price_data:
                    success = await self.update_stock_data(stock_code, price_data["current_price"])
                    if success:
                        updated_count += 1
            
            self.last_update = datetime.now()
            
            logger.info(f"워치리스트 데이터 갱신 완료: {updated_count}개 종목")
            
            return {
                "success": True,
                "updated_count": updated_count,
                "last_update": self.last_update.isoformat()
            }
            
        except Exception as e:
            logger.error(f"워치리스트 갱신 실패: {str(e)}")
            return {
                "success": False,
                "updated_count": 0,
                "error": str(e)
            }
    
    async def clear_watchlist(self) -> Dict[str, Any]:
        """워치리스트 초기화"""
        try:
            removed_count = len(self.watchlist_df)
            
            self.watchlist_df = pd.DataFrame(columns=[
                '현재가', '수익률', '평균단가', '보유수량', 'MACD', 'MACD시그널', 
                'RSI', '트레일링스탑발동여부', '트레일링스탑발동후고가'
            ])
            
            self.price_history = {}
            
            logger.info(f"워치리스트 초기화 완료: {removed_count}개 종목 제거")
            
            return {
                "success": True,
                "removed_count": removed_count
            }
            
        except Exception as e:
            logger.error(f"워치리스트 초기화 실패: {str(e)}")
            return {
                "success": False,
                "removed_count": 0,
                "error": str(e)
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """워치리스트 통계 조회"""
        try:
            total_stocks = len(self.watchlist_df)
            
            if total_stocks == 0:
                return {
                    "total_stocks": 0,
                    "profit_stocks": 0,
                    "loss_stocks": 0,
                    "avg_profit_rate": 0.0,
                    "last_update": None
                }
            
            profit_stocks = len(self.watchlist_df[self.watchlist_df['수익률'] > 0])
            loss_stocks = len(self.watchlist_df[self.watchlist_df['수익률'] < 0])
            avg_profit_rate = self.watchlist_df['수익률'].mean()
            
            return {
                "total_stocks": total_stocks,
                "profit_stocks": profit_stocks,
                "loss_stocks": loss_stocks,
                "neutral_stocks": total_stocks - profit_stocks - loss_stocks,
                "avg_profit_rate": round(avg_profit_rate, 2),
                "max_profit_rate": round(self.watchlist_df['수익률'].max(), 2),
                "min_profit_rate": round(self.watchlist_df['수익률'].min(), 2),
                "last_update": self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            logger.error(f"워치리스트 통계 조회 실패: {str(e)}")
            return {
                "error": f"통계 조회 실패: {str(e)}"
            }