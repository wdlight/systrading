"""
성능 메트릭 및 Circuit Breaker 유틸리티

WebSocket 시스템의 성능을 모니터링하고 장애 복구를 위한 Circuit Breaker 패턴을 제공합니다.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
from typing import Dict, Any, Optional, List
import threading

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit Breaker 상태"""
    CLOSED = "closed"        # 정상 상태
    OPEN = "open"            # 차단 상태
    HALF_OPEN = "half_open"  # 복구 시도 상태


@dataclass
class PerformanceMetrics:
    """성능 메트릭 수집"""
    
    # 기본 카운터
    messages_received: int = 0
    messages_processed: int = 0
    messages_dropped: int = 0
    parse_errors: int = 0
    broadcast_errors: int = 0
    connection_errors: int = 0
    
    # 처리 시간 추적 (최근 100개)
    processing_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # 시간 기반 카운터 (60초 윈도우)
    received_timestamps: deque = field(default_factory=lambda: deque(maxlen=600))  # 10분간
    processed_timestamps: deque = field(default_factory=lambda: deque(maxlen=600))
    
    # 락 (스레드 안전성)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def record_message_received(self):
        """메시지 수신 기록"""
        with self._lock:
            self.messages_received += 1
            self.received_timestamps.append(time.time())
    
    def record_message_processed(self):
        """메시지 처리 완료 기록"""
        with self._lock:
            self.messages_processed += 1
            self.processed_timestamps.append(time.time())
    
    def record_message_dropped(self):
        """메시지 드롭 기록"""
        with self._lock:
            self.messages_dropped += 1
    
    def record_parse_error(self):
        """파싱 에러 기록"""
        with self._lock:
            self.parse_errors += 1
    
    def record_broadcast_error(self):
        """브로드캐스트 에러 기록"""
        with self._lock:
            self.broadcast_errors += 1
    
    def record_connection_error(self):
        """연결 에러 기록"""
        with self._lock:
            self.connection_errors += 1
    
    def record_processing_time(self, duration_ms: float):
        """처리 시간 기록"""
        with self._lock:
            self.processing_times.append(duration_ms)
    
    def get_avg_processing_time(self) -> float:
        """평균 처리 시간 (ms)"""
        with self._lock:
            if not self.processing_times:
                return 0.0
            return sum(self.processing_times) / len(self.processing_times)
    
    def get_throughput(self, window_seconds: int = 60) -> float:
        """처리량 (메시지/초)"""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - window_seconds
            
            # 윈도우 내 처리된 메시지 수
            processed_count = sum(
                1 for timestamp in self.processed_timestamps
                if timestamp >= cutoff_time
            )
            
            return processed_count / window_seconds if window_seconds > 0 else 0.0
    
    def get_receive_rate(self, window_seconds: int = 60) -> float:
        """수신률 (메시지/초)"""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - window_seconds
            
            # 윈도우 내 수신된 메시지 수
            received_count = sum(
                1 for timestamp in self.received_timestamps
                if timestamp >= cutoff_time
            )
            
            return received_count / window_seconds if window_seconds > 0 else 0.0
    
    def get_error_rate(self) -> float:
        """에러율 (%)"""
        with self._lock:
            total_errors = (
                self.parse_errors + 
                self.broadcast_errors + 
                self.connection_errors
            )
            total_operations = self.messages_received + total_errors
            
            if total_operations == 0:
                return 0.0
            
            return (total_errors / total_operations) * 100
    
    def get_drop_rate(self) -> float:
        """드롭률 (%)"""
        with self._lock:
            if self.messages_received == 0:
                return 0.0
            return (self.messages_dropped / self.messages_received) * 100
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약 반환"""
        with self._lock:
            return {
                "messages_received": self.messages_received,
                "messages_processed": self.messages_processed,
                "messages_dropped": self.messages_dropped,
                "parse_errors": self.parse_errors,
                "broadcast_errors": self.broadcast_errors,
                "connection_errors": self.connection_errors,
                "avg_processing_time_ms": self.get_avg_processing_time(),
                "throughput_per_sec": self.get_throughput(),
                "receive_rate_per_sec": self.get_receive_rate(),
                "error_rate_percent": self.get_error_rate(),
                "drop_rate_percent": self.get_drop_rate(),
                "timestamp": datetime.now().isoformat()
            }
    
    def reset(self):
        """메트릭 초기화"""
        with self._lock:
            self.messages_received = 0
            self.messages_processed = 0
            self.messages_dropped = 0
            self.parse_errors = 0
            self.broadcast_errors = 0
            self.connection_errors = 0
            self.processing_times.clear()
            self.received_timestamps.clear()
            self.processed_timestamps.clear()
            logger.info("성능 메트릭이 초기화되었습니다")


class CircuitBreaker:
    """Circuit Breaker 패턴 구현"""
    
    def __init__(
        self, 
        failure_threshold: int = 5, 
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3,
        name: str = "CircuitBreaker"
    ):
        """
        CircuitBreaker 초기화
        
        Args:
            failure_threshold: 실패 임계값
            timeout_seconds: 타임아웃 시간 (초)
            half_open_max_calls: HALF_OPEN 상태에서 최대 시도 횟수
            name: Circuit Breaker 이름
        """
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.half_open_max_calls = half_open_max_calls
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
        self.last_success_time: Optional[datetime] = None
        
        self._lock = threading.Lock()
        
        logger.info(f"CircuitBreaker 초기화: {name} (threshold: {failure_threshold}, timeout: {timeout_seconds}s)")
    
    def record_success(self):
        """성공 기록"""
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            self.half_open_calls = 0
            self.last_success_time = datetime.now()
            
            logger.debug(f"[{self.name}] 성공 기록 - 상태: {self.state.value}")
    
    def record_failure(self):
        """실패 기록"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"[{self.name}] Circuit Breaker OPEN: "
                    f"{self.failure_count}회 실패 (임계값: {self.failure_threshold})"
                )
            else:
                logger.warning(
                    f"[{self.name}] 실패 기록: {self.failure_count}/{self.failure_threshold}"
                )
    
    def can_attempt(self) -> bool:
        """시도 가능 여부"""
        with self._lock:
            current_time = datetime.now()
            
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # 타임아웃 경과 확인
                if self.last_failure_time and (current_time - self.last_failure_time) > self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"[{self.name}] Circuit Breaker HALF_OPEN: 복구 시도")
                    return True
                return False
            
            elif self.state == CircuitState.HALF_OPEN:
                # HALF_OPEN 상태에서는 제한된 시도만 허용
                if self.half_open_calls < self.half_open_max_calls:
                    return True
                else:
                    # 최대 시도 횟수 초과 시 다시 OPEN
                    self.state = CircuitState.OPEN
                    logger.error(f"[{self.name}] HALF_OPEN 시도 횟수 초과. 다시 OPEN 상태")
                    return False
            
            return False
    
    def get_state(self) -> CircuitState:
        """현재 상태 반환"""
        with self._lock:
            return self.state
    
    def get_metrics(self) -> Dict[str, Any]:
        """Circuit Breaker 메트릭 반환"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "half_open_calls": self.half_open_calls,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
                "timeout_seconds": self.timeout.total_seconds()
            }
    
    def reset(self):
        """Circuit Breaker 초기화"""
        with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
            self.half_open_calls = 0
            self.last_success_time = None
            logger.info(f"[{self.name}] Circuit Breaker 초기화")


class MetricsCollector:
    """여러 메트릭을 통합 수집"""
    
    def __init__(self):
        """MetricsCollector 초기화"""
        self.metrics = PerformanceMetrics()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
        logger.info("MetricsCollector 초기화")
    
    def add_circuit_breaker(self, name: str, cb: CircuitBreaker):
        """Circuit Breaker 추가"""
        with self._lock:
            self.circuit_breakers[name] = cb
            logger.info(f"Circuit Breaker 추가: {name}")
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Circuit Breaker 조회"""
        with self._lock:
            return self.circuit_breakers.get(name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """모든 메트릭 반환"""
        with self._lock:
            result = {
                "performance": self.metrics.get_metrics_summary(),
                "circuit_breakers": {}
            }
            
            for name, cb in self.circuit_breakers.items():
                result["circuit_breakers"][name] = cb.get_metrics()
            
            return result
    
    def get_health_status(self) -> Dict[str, Any]:
        """시스템 건강 상태 반환"""
        with self._lock:
            # Circuit Breaker 상태 확인
            open_circuits = []
            half_open_circuits = []
            
            for name, cb in self.circuit_breakers.items():
                state = cb.get_state()
                if state == CircuitState.OPEN:
                    open_circuits.append(name)
                elif state == CircuitState.HALF_OPEN:
                    half_open_circuits.append(name)
            
            # 성능 메트릭 확인
            error_rate = self.metrics.get_error_rate()
            drop_rate = self.metrics.get_drop_rate()
            
            # 전체 건강 상태 결정
            is_healthy = (
                len(open_circuits) == 0 and  # 열린 Circuit Breaker 없음
                error_rate < 10.0 and        # 에러율 10% 미만
                drop_rate < 5.0             # 드롭률 5% 미만
            )
            
            return {
                "is_healthy": is_healthy,
                "open_circuits": open_circuits,
                "half_open_circuits": half_open_circuits,
                "error_rate": error_rate,
                "drop_rate": drop_rate,
                "timestamp": datetime.now().isoformat()
            }
    
    def reset_all(self):
        """모든 메트릭 초기화"""
        with self._lock:
            self.metrics.reset()
            for cb in self.circuit_breakers.values():
                cb.reset()
            logger.info("모든 메트릭이 초기화되었습니다")


# 전역 메트릭 수집기 인스턴스
_global_metrics_collector: Optional[MetricsCollector] = None
_collector_lock = threading.Lock()


def get_global_metrics_collector() -> MetricsCollector:
    """전역 메트릭 수집기 반환"""
    global _global_metrics_collector
    
    if _global_metrics_collector is None:
        with _collector_lock:
            if _global_metrics_collector is None:
                _global_metrics_collector = MetricsCollector()
    
    return _global_metrics_collector


def create_circuit_breaker(
    name: str, 
    failure_threshold: int = 5, 
    timeout_seconds: int = 60
) -> CircuitBreaker:
    """
    Circuit Breaker 생성 편의 함수
    
    Args:
        name: Circuit Breaker 이름
        failure_threshold: 실패 임계값
        timeout_seconds: 타임아웃 시간
    
    Returns:
        CircuitBreaker: 생성된 Circuit Breaker
    """
    cb = CircuitBreaker(failure_threshold, timeout_seconds, name=name)
    get_global_metrics_collector().add_circuit_breaker(name, cb)
    return cb


# 데코레이터들
def track_performance(func):
    """함수 실행 시간을 추적하는 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            # 성공 시 메트릭 기록
            get_global_metrics_collector().metrics.record_message_processed()
            return result
        except Exception as e:
            # 실패 시 에러 기록
            get_global_metrics_collector().metrics.record_parse_error()
            raise
        finally:
            # 처리 시간 기록
            duration_ms = (time.time() - start_time) * 1000
            get_global_metrics_collector().metrics.record_processing_time(duration_ms)
    
    return wrapper


def with_circuit_breaker(circuit_breaker_name: str):
    """Circuit Breaker를 적용하는 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            collector = get_global_metrics_collector()
            cb = collector.get_circuit_breaker(circuit_breaker_name)
            
            if cb is None:
                logger.error(f"Circuit Breaker '{circuit_breaker_name}'를 찾을 수 없습니다")
                return func(*args, **kwargs)
            
            if not cb.can_attempt():
                raise Exception(f"Circuit Breaker '{circuit_breaker_name}' is OPEN")
            
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
        
        return wrapper
    return decorator
