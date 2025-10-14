"""
Queue 모니터링 유틸리티

Queue 상태를 실시간으로 모니터링하여 성능 문제를 예방합니다.
"""

import logging
from typing import Dict, Any, Optional
from queue import Queue, Empty
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class QueueMonitor:
    """Queue 상태 모니터링"""
    
    def __init__(self, queue: Queue, name: str, warning_threshold: float = 0.8):
        """
        QueueMonitor 초기화
        
        Args:
            queue: 모니터링할 Queue 객체
            name: Queue 이름 (로그용)
            warning_threshold: 경고 임계값 (0.0 ~ 1.0)
        """
        self.queue = queue
        self.name = name
        self.warning_threshold = warning_threshold
        self.max_size = getattr(queue, '_maxsize', 0)  # Queue 최대 크기
        self.last_warning_time = 0  # 마지막 경고 시간
        self.warning_cooldown = 5  # 경고 쿨다운 (초)
        
        logger.info(f"QueueMonitor 초기화: {name} (max_size: {self.max_size})")
    
    def check_status(self) -> str:
        """
        Queue 상태 확인
        
        Returns:
            str: "ok", "warning", "critical"
        """
        current_size = self.queue.qsize()
        current_time = time.time()
        
        if self.max_size <= 0:
            # 무제한 Queue
            return "ok"
        
        usage_ratio = current_size / self.max_size
        
        if usage_ratio > 0.95:
            # 임계 상태
            if current_time - self.last_warning_time > self.warning_cooldown:
                logger.error(
                    f"[{self.name}] Queue 임계 상태: "
                    f"{current_size}/{self.max_size} ({usage_ratio*100:.1f}%)"
                )
                self.last_warning_time = current_time
            return "critical"
        
        elif usage_ratio > self.warning_threshold:
            # 경고 상태
            if current_time - self.last_warning_time > self.warning_cooldown:
                logger.warning(
                    f"[{self.name}] Queue 사용률 높음: "
                    f"{current_size}/{self.max_size} ({usage_ratio*100:.1f}%)"
                )
                self.last_warning_time = current_time
            return "warning"
        
        return "ok"
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Queue 메트릭 반환
        
        Returns:
            Dict[str, Any]: 메트릭 정보
        """
        current_size = self.queue.qsize()
        usage_ratio = current_size / self.max_size if self.max_size > 0 else 0
        
        return {
            "name": self.name,
            "current_size": current_size,
            "max_size": self.max_size,
            "usage_ratio": usage_ratio,
            "status": self.check_status(),
            "timestamp": datetime.now().isoformat()
        }
    
    def is_healthy(self) -> bool:
        """
        Queue 건강 상태 확인
        
        Returns:
            bool: True if healthy, False otherwise
        """
        status = self.check_status()
        return status in ["ok", "warning"]  # critical이 아니면 healthy


class QueueManager:
    """여러 Queue를 통합 관리"""
    
    def __init__(self):
        """QueueManager 초기화"""
        self.monitors: Dict[str, QueueMonitor] = {}
        logger.info("QueueManager 초기화")
    
    def add_monitor(self, name: str, queue: Queue, warning_threshold: float = 0.8):
        """
        Queue 모니터 추가
        
        Args:
            name: Queue 이름
            queue: Queue 객체
            warning_threshold: 경고 임계값
        """
        monitor = QueueMonitor(queue, name, warning_threshold)
        self.monitors[name] = monitor
        logger.info(f"Queue 모니터 추가: {name}")
    
    def check_all_status(self) -> Dict[str, str]:
        """
        모든 Queue 상태 확인
        
        Returns:
            Dict[str, str]: Queue별 상태
        """
        status_map = {}
        for name, monitor in self.monitors.items():
            status_map[name] = monitor.check_status()
        return status_map
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 Queue 메트릭 반환
        
        Returns:
            Dict[str, Dict[str, Any]]: Queue별 메트릭
        """
        metrics_map = {}
        for name, monitor in self.monitors.items():
            metrics_map[name] = monitor.get_metrics()
        return metrics_map
    
    def is_system_healthy(self) -> bool:
        """
        시스템 전체 건강 상태 확인
        
        Returns:
            bool: 모든 Queue가 healthy하면 True
        """
        for monitor in self.monitors.values():
            if not monitor.is_healthy():
                return False
        return True
    
    def get_critical_queues(self) -> list:
        """
        임계 상태인 Queue 목록 반환
        
        Returns:
            list: 임계 상태인 Queue 이름 목록
        """
        critical_queues = []
        for name, monitor in self.monitors.items():
            if monitor.check_status() == "critical":
                critical_queues.append(name)
        return critical_queues
    
    def get_warning_queues(self) -> list:
        """
        경고 상태인 Queue 목록 반환
        
        Returns:
            list: 경고 상태인 Queue 이름 목록
        """
        warning_queues = []
        for name, monitor in self.monitors.items():
            if monitor.check_status() == "warning":
                warning_queues.append(name)
        return warning_queues


class QueueHealthChecker:
    """Queue 건강 상태를 주기적으로 체크"""
    
    def __init__(self, queue_manager: QueueManager, check_interval: float = 10.0):
        """
        QueueHealthChecker 초기화
        
        Args:
            queue_manager: QueueManager 인스턴스
            check_interval: 체크 간격 (초)
        """
        self.queue_manager = queue_manager
        self.check_interval = check_interval
        self.is_running = False
        logger.info(f"QueueHealthChecker 초기화 (interval: {check_interval}s)")
    
    async def start_monitoring(self):
        """모니터링 시작"""
        self.is_running = True
        logger.info("Queue 건강 상태 모니터링 시작")
        
        while self.is_running:
            try:
                # 모든 Queue 상태 체크
                status_map = self.queue_manager.check_all_status()
                
                # 임계 상태 Queue 확인
                critical_queues = self.queue_manager.get_critical_queues()
                if critical_queues:
                    logger.error(f"임계 상태 Queue: {critical_queues}")
                
                # 경고 상태 Queue 확인
                warning_queues = self.queue_manager.get_warning_queues()
                if warning_queues:
                    logger.warning(f"경고 상태 Queue: {warning_queues}")
                
                # 시스템 전체 건강 상태
                if not self.queue_manager.is_system_healthy():
                    logger.error("시스템 Queue 건강 상태 불량")
                else:
                    logger.debug("시스템 Queue 건강 상태 양호")
                
            except Exception as e:
                logger.error(f"Queue 상태 체크 오류: {e}")
            
            # 다음 체크까지 대기
            await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        logger.info("Queue 건강 상태 모니터링 중지")


# 편의 함수들
def create_queue_monitor(queue: Queue, name: str, warning_threshold: float = 0.8) -> QueueMonitor:
    """
    QueueMonitor 생성 편의 함수
    
    Args:
        queue: Queue 객체
        name: Queue 이름
        warning_threshold: 경고 임계값
    
    Returns:
        QueueMonitor: 생성된 모니터
    """
    return QueueMonitor(queue, name, warning_threshold)


def create_queue_manager() -> QueueManager:
    """
    QueueManager 생성 편의 함수
    
    Returns:
        QueueManager: 생성된 매니저
    """
    return QueueManager()


# 임포트 에러 방지
try:
    import asyncio
except ImportError:
    logger.warning("asyncio 모듈을 사용할 수 없습니다. 비동기 기능이 제한됩니다.")
