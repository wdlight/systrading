"""
WebSocket 데이터 로깅 유틸리티
데이터가 많을 경우 샘플링해서 로그를 남기는 시스템
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict
from loguru import logger
import json


class WebSocketLogger:
    """WebSocket 데이터 로깅 관리 클래스"""
    
    def __init__(self):
        # 샘플링 설정
        self.sample_interval_seconds = 60  # 1분 간격
        self.sample_count_threshold = 100  # 100개마다
        self.max_log_size = 1000  # 최대 로그 크기
        
        # 카운터 및 시간 추적
        self.message_counts: Dict[str, int] = defaultdict(int)
        self.last_log_times: Dict[str, datetime] = {}
        self.last_log_counts: Dict[str, int] = defaultdict(int)
        
        # 로그 버퍼 (최근 메시지 저장)
        self.message_buffers: Dict[str, list] = defaultdict(list)
        
        logger.info("🔍 WebSocket 데이터 로깅 시스템 초기화됨")
    
    def should_log_message(self, message_type: str) -> bool:
        """
        메시지 로깅 여부 결정
        
        Args:
            message_type: 메시지 타입 (예: 'orderbook_update', 'price_update')
            
        Returns:
            bool: 로깅해야 하면 True
        """
        current_time = datetime.now()
        current_count = self.message_counts[message_type]
        
        # 첫 번째 메시지는 항상 로깅
        if current_count == 0:
            return True
        
        # 시간 기반 샘플링 (1분마다)
        last_log_time = self.last_log_times.get(message_type)
        if last_log_time is None:
            return True
        
        time_diff = (current_time - last_log_time).total_seconds()
        if time_diff >= self.sample_interval_seconds:
            return True
        
        # 카운트 기반 샘플링 (100개마다)
        if current_count % self.sample_count_threshold == 0:
            return True
        
        return False
    
    def log_message(self, message_type: str, data: Dict[str, Any], source: str = "unknown"):
        """
        WebSocket 메시지 로깅
        
        Args:
            message_type: 메시지 타입
            data: 메시지 데이터
            source: 메시지 소스 (예: 'backend', 'frontend')
        """
        self.message_counts[message_type] += 1
        current_time = datetime.now()
        
        # 로깅 여부 결정
        if not self.should_log_message(message_type):
            # 로깅하지 않더라도 버퍼에 저장 (샘플용)
            self._add_to_buffer(message_type, data)
            return
        
        # 로깅 실행
        self._log_message_internal(message_type, data, source, current_time)
        
        # 시간 및 카운트 업데이트
        self.last_log_times[message_type] = current_time
        self.last_log_counts[message_type] = self.message_counts[message_type]
    
    def _log_message_internal(self, message_type: str, data: Dict[str, Any], source: str, timestamp: datetime):
        """실제 로그 출력"""
        try:
            # 데이터 크기 확인
            data_str = json.dumps(data, ensure_ascii=False, default=str)
            if len(data_str) > self.max_log_size:
                data_str = data_str[:self.max_log_size] + "... (truncated)"
            
            # 로그 레벨 결정
            log_level = self._get_log_level(message_type)
            
            # 로그 메시지 구성
            count_info = f"({self.message_counts[message_type]}번째)"
            time_info = timestamp.strftime("%H:%M:%S.%f")[:-3]  # 밀리초까지
            
            log_message = f"📡 WebSocket [{source}] {message_type} {count_info} @ {time_info}"
            
            # 로그 출력
            if log_level == "DEBUG":
                logger.debug(f"{log_message}\n{data_str}")
            elif log_level == "INFO":
                logger.info(f"{log_message}\n{data_str}")
            else:
                logger.warning(f"{log_message}\n{data_str}")
                
        except Exception as e:
            logger.error(f"WebSocket 로깅 중 오류: {e}")
    
    def _get_log_level(self, message_type: str) -> str:
        """메시지 타입별 로그 레벨 결정"""
        level_map = {
            'orderbook_update': 'INFO',      # 호가 데이터 - 중요
            'price_update': 'DEBUG',         # 가격 업데이트 - 빈번
            'market_index_update': 'INFO',   # 지수 업데이트 - 중요
            'watchlist_update': 'DEBUG',     # 워치리스트 - 빈번
            'account_update': 'INFO',        # 계좌 업데이트 - 중요
            'trading_status': 'INFO',        # 거래 상태 - 중요
            'order_update': 'INFO',          # 주문 업데이트 - 중요
            'connection_status': 'WARNING',  # 연결 상태 - 중요
            'market_status_update': 'INFO',  # 시장 상태 - 중요
        }
        return level_map.get(message_type, 'DEBUG')
    
    def _add_to_buffer(self, message_type: str, data: Dict[str, Any]):
        """버퍼에 메시지 추가 (샘플용)"""
        buffer = self.message_buffers[message_type]
        
        # 최대 10개까지만 저장
        if len(buffer) >= 10:
            buffer.pop(0)
        
        buffer.append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """현재 통계 정보 반환"""
        stats = {}
        current_time = datetime.now()
        
        for msg_type, count in self.message_counts.items():
            last_log_time = self.last_log_times.get(msg_type)
            time_since_last = None
            
            if last_log_time:
                time_since_last = (current_time - last_log_time).total_seconds()
            
            stats[msg_type] = {
                'total_count': count,
                'last_log_count': self.last_log_counts.get(msg_type, 0),
                'time_since_last_log': time_since_last,
                'buffer_size': len(self.message_buffers.get(msg_type, []))
            }
        
        return stats
    
    def log_statistics(self):
        """통계 정보 로깅 (주기적으로 호출)"""
        stats = self.get_statistics()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        logger.info(f"📊 WebSocket 메시지 통계 @ {current_time}")
        
        for msg_type, stat in stats.items():
            if stat['total_count'] > 0:
                logger.info(f"  {msg_type}: {stat['total_count']}개 (마지막 로그: {stat['time_since_last_log']:.1f}초 전)")


# 전역 인스턴스
websocket_logger = WebSocketLogger()
