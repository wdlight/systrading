"""
yfinance 기반 지수 데이터 서비스
전 세계 주요 지수 데이터를 제공합니다.
"""

import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import time
from loguru import logger

class YFinanceIndexService:
    """yfinance 기반 지수 데이터 서비스"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 30  # 30초 캐시
        
        # 전체 지수 매핑 테이블 (기존 + 추가 지수)
        self.index_mapping = {
            # 기존 주요 지수
            "kospi": "^KS11",           # KOSPI Composite Index
            "kosdaq": "^KQ11",          # Kosdaq Composite Index  
            "nasdaq": "^IXIC",          # NASDAQ Composite
            "dow": "^DJI",              # Dow Jones Industrial Average
            "sp500": "^GSPC",           # S&P 500
            "usd_krw": "USDKRW=X",      # USD/KRW 환율
            
            # 추가 지수들
            "nyse": "^NYA",             # NYSE Composite
            "russell2000": "^RUT",      # Russell 2000
            "ftse": "^FTSE",            # FTSE 100
            "dax": "^GDAXI",            # DAX
            "cac40": "^FCHI",           # CAC 40
            "nikkei225": "^N225",       # Nikkei 225
            "hangseng": "^HSI",         # Hang Seng Index
            "shanghai": "000001.SS"     # Shanghai Composite (SSE)
        }
        
        logger.info(f"YFinanceIndexService 초기화 완료 - {len(self.index_mapping)}개 지수 지원")
    
    async def get_market_indices(self) -> Dict[str, Dict[str, Any]]:
        """모든 지수 데이터 조회"""
        try:
            logger.info("전체 지수 데이터 조회 시작")
            indices = {}
            
            # 캐시 확인
            cache_key = "all_indices"
            now = time.time()
            
            if cache_key in self.cache:
                cached_time, cached_data = self.cache[cache_key]
                if now - cached_time < self.cache_duration:
                    logger.info("캐시된 지수 데이터 사용")
                    return cached_data
            
            # 각 지수별로 데이터 조회 (순차 처리)
            for index_name, ticker in self.index_mapping.items():
                try:
                    result = await self._fetch_and_format_index(index_name, ticker)
                    if result:
                        indices[index_name] = result
                    else:
                        logger.warning(f"{index_name} ({ticker}) 데이터 조회 실패: 결과 없음")
                        indices[index_name] = self._get_default_data(index_name, ticker)
                except Exception as e:
                    logger.error(f"{index_name} ({ticker}) 처리 중 예외 발생: {e}")
                    indices[index_name] = self._get_default_data(index_name, ticker)
            
            # 캐시 저장
            self.cache[cache_key] = (now, indices)
            
            logger.info(f"지수 데이터 조회 완료 - {len(indices)}개 지수")
            return indices
            
        except Exception as e:
            logger.error(f"지수 데이터 조회 실패: {e}")
            return self._get_all_default_data()
    
    async def get_market_indices_by_region(self, region: str) -> Dict[str, Dict[str, Any]]:
        """지역별 지수 데이터 조회"""
        region_mapping = {
            "asia": ["kospi", "kosdaq", "nikkei225", "hangseng", "shanghai"],
            "europe": ["ftse", "dax", "cac40"],
            "americas": ["nasdaq", "dow", "sp500", "nyse", "russell2000"],
            "forex": ["usd_krw"]
        }
        
        if region not in region_mapping:
            raise ValueError(f"지원하지 않는 지역: {region}. 지원 지역: {list(region_mapping.keys())}")
        
        target_indices = region_mapping[region]
        all_indices = await self.get_market_indices()
        
        return {name: all_indices.get(name, self._get_default_data(name, "")) 
                for name in target_indices}
    
    async def _fetch_and_format_index(self, index_name: str, ticker: str) -> Optional[Dict[str, Any]]:
        """개별 지수 데이터 조회 및 포맷팅"""
        try:
            data = await self._fetch_index_data(ticker)
            if data:
                return self._format_index_data(index_name, ticker, data)
            return None
        except Exception as e:
            logger.warning(f"{index_name} ({ticker}) 처리 실패: {e}")
            return None
    
    async def _fetch_index_data(self, ticker: str) -> Optional[Dict]:
        """개별 지수 데이터 조회"""
        try:
            # 비동기로 yfinance 호출
            loop = asyncio.get_event_loop()
            
            def fetch_data():
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                return info
            
            info = await loop.run_in_executor(None, fetch_data)
            return info
        except Exception as e:
            logger.error(f"{ticker} 데이터 조회 실패: {e}")
            return None
    
    def _format_index_data(self, index_name: str, ticker: str, data: Dict) -> Dict[str, Any]:
        """yfinance 데이터를 기존 형식으로 변환"""
        try:
            # 다양한 필드명으로 현재가 시도
            current = (data.get("regularMarketPrice") or 
                      data.get("currentPrice") or 
                      data.get("price") or 
                      data.get("lastPrice") or 0.0)
            
            # 이전 종가 시도
            previous_close = (data.get("previousClose") or 
                             data.get("previousPrice") or 
                             data.get("regularMarketPreviousClose") or 
                             current)
            
            # 변화량 계산
            change = current - previous_close if previous_close and current else 0.0
            change_rate = (change / previous_close * 100) if previous_close and previous_close != 0 else 0.0
            
            # 기존 형식에 맞춰 변환
            formatted_data = {
                "code": self._get_index_code(index_name),
                "market": self._get_market_code(index_name),
                "current": round(float(current), 2),
                "change": round(float(change), 2),
                "change_rate": round(float(change_rate), 2),
                "ticker": ticker,  # 디버깅용 티커 정보 추가
                "last_updated": datetime.now().isoformat()
            }
            
            logger.debug(f"{index_name} 데이터 포맷팅 완료: {formatted_data}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"{index_name} 데이터 포맷팅 실패: {e}")
            return self._get_default_data(index_name, ticker)
    
    def _get_index_code(self, index_name: str) -> str:
        """지수 코드 매핑"""
        code_mapping = {
            # 기존 지수
            "kospi": "0001",
            "kosdaq": "1001", 
            "nasdaq": "NDX",
            "dow": "DJI",
            "sp500": "US500",
            "usd_krw": "USDKRW",
            
            # 추가 지수
            "nyse": "NYA",
            "russell2000": "RUT",
            "ftse": "FTSE",
            "dax": "GDAXI",
            "cac40": "FCHI",
            "nikkei225": "N225",
            "hangseng": "HSI",
            "shanghai": "SSEC"
        }
        return code_mapping.get(index_name, "UNKNOWN")
    
    def _get_market_code(self, index_name: str) -> str:
        """시장 코드 매핑"""
        market_mapping = {
            # 기존 지수
            "kospi": "U",
            "kosdaq": "K",
            "nasdaq": "N", 
            "dow": "N",
            "sp500": "N",
            "usd_krw": "X",
            
            # 추가 지수
            "nyse": "N",          # 미국
            "russell2000": "N",   # 미국
            "ftse": "E",          # 유럽
            "dax": "E",           # 유럽
            "cac40": "E",         # 유럽
            "nikkei225": "A",     # 아시아
            "hangseng": "A",      # 아시아
            "shanghai": "A"       # 아시아
        }
        return market_mapping.get(index_name, "U")
    
    def _get_default_data(self, index_name: str, ticker: str) -> Dict[str, Any]:
        """기본값 데이터 반환"""
        return {
            "code": self._get_index_code(index_name),
            "market": self._get_market_code(index_name),
            "current": 0.0,
            "change": 0.0,
            "change_rate": 0.0,
            "ticker": ticker,
            "last_updated": datetime.now().isoformat(),
            "error": "데이터 조회 실패"
        }
    
    def _get_all_default_data(self) -> Dict[str, Dict[str, Any]]:
        """모든 지수의 기본값 데이터"""
        return {name: self._get_default_data(name, ticker) 
                for name, ticker in self.index_mapping.items()}
    
    def get_supported_indices(self) -> Dict[str, str]:
        """지원하는 지수 목록 반환"""
        return self.index_mapping.copy()
    
    def get_supported_regions(self) -> Dict[str, list]:
        """지원하는 지역별 지수 목록 반환"""
        return {
            "asia": ["kospi", "kosdaq", "nikkei225", "hangseng", "shanghai"],
            "europe": ["ftse", "dax", "cac40"],
            "americas": ["nasdaq", "dow", "sp500", "nyse", "russell2000"],
            "forex": ["usd_krw"]
        }
