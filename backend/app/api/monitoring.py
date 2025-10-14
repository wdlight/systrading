"""
모니터링 API 엔드포인트

WebSocket 시스템의 성능 메트릭과 건강 상태를 조회할 수 있는 API를 제공합니다.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.utils.performance_metrics import get_global_metrics_collector, MetricsCollector
from app.utils.queue_monitor import QueueManager
from app.utils.websocket_logger import websocket_logger
from app.websocket.connection import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Pydantic 모델들
class QueueMetrics(BaseModel):
    """Queue 메트릭 모델"""
    name: str
    current_size: int
    max_size: int
    usage_ratio: float
    status: str
    timestamp: str


class PerformanceMetricsResponse(BaseModel):
    """성능 메트릭 응답 모델"""
    messages_received: int
    messages_processed: int
    messages_dropped: int
    parse_errors: int
    broadcast_errors: int
    connection_errors: int
    avg_processing_time_ms: float
    throughput_per_sec: float
    receive_rate_per_sec: float
    error_rate_percent: float
    drop_rate_percent: float
    timestamp: str


class CircuitBreakerMetrics(BaseModel):
    """Circuit Breaker 메트릭 모델"""
    name: str
    state: str
    failure_count: int
    failure_threshold: int
    half_open_calls: int
    last_failure_time: str = None
    last_success_time: str = None
    timeout_seconds: float


class HealthStatus(BaseModel):
    """건강 상태 모델"""
    is_healthy: bool
    open_circuits: List[str]
    half_open_circuits: List[str]
    error_rate: float
    drop_rate: float
    timestamp: str


class WebSocketMetrics(BaseModel):
    """WebSocket 메트릭 모델"""
    active_connections: int
    total_connections: int
    stock_subscriptions: Dict[str, int]


class SystemMetrics(BaseModel):
    """시스템 전체 메트릭 모델"""
    timestamp: str
    performance: PerformanceMetricsResponse
    circuit_breakers: Dict[str, CircuitBreakerMetrics]
    health: HealthStatus
    websocket: WebSocketMetrics
    queues: Dict[str, QueueMetrics]


# 의존성 함수들
def get_metrics_collector() -> MetricsCollector:
    """메트릭 수집기 의존성"""
    return get_global_metrics_collector()


def get_queue_manager() -> QueueManager:
    """Queue 매니저 의존성 (실제 구현에서는 싱글톤 사용)"""
    # 실제 구현에서는 전역 QueueManager 인스턴스를 반환
    from app.main import get_queue_manager as _get_queue_manager
    return _get_queue_manager()


def get_connection_manager() -> ConnectionManager:
    """Connection 매니저 의존성"""
    # 실제 구현에서는 전역 ConnectionManager 인스턴스를 반환
    from app.main import get_connection_manager as _get_connection_manager
    return _get_connection_manager()


@router.get("/health", response_model=HealthStatus)
async def get_health_status(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """
    시스템 건강 상태 조회
    
    Returns:
        HealthStatus: 시스템 건강 상태 정보
    """
    try:
        health_data = metrics_collector.get_health_status()
        return HealthStatus(**health_data)
    except Exception as e:
        logger.error(f"건강 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="건강 상태 조회 실패")


@router.get("/metrics/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """
    성능 메트릭 조회
    
    Returns:
        PerformanceMetricsResponse: 성능 메트릭 정보
    """
    try:
        metrics_data = metrics_collector.metrics.get_metrics_summary()
        return PerformanceMetricsResponse(**metrics_data)
    except Exception as e:
        logger.error(f"성능 메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="성능 메트릭 조회 실패")


@router.get("/metrics/circuit-breakers", response_model=Dict[str, CircuitBreakerMetrics])
async def get_circuit_breaker_metrics(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """
    Circuit Breaker 메트릭 조회
    
    Returns:
        Dict[str, CircuitBreakerMetrics]: Circuit Breaker별 메트릭
    """
    try:
        all_metrics = metrics_collector.get_all_metrics()
        circuit_breakers = all_metrics.get("circuit_breakers", {})
        
        result = {}
        for name, data in circuit_breakers.items():
            result[name] = CircuitBreakerMetrics(**data)
        
        return result
    except Exception as e:
        logger.error(f"Circuit Breaker 메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="Circuit Breaker 메트릭 조회 실패")


@router.get("/metrics/websocket", response_model=WebSocketMetrics)
async def get_websocket_metrics(
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    WebSocket 메트릭 조회
    
    Returns:
        WebSocketMetrics: WebSocket 연결 정보
    """
    try:
        # 실제 구현에서는 ConnectionManager에서 메트릭을 가져옴
        active_connections = len(connection_manager.active_connections)
        
        # 종목별 구독자 수 계산
        stock_subscriptions = {}
        if hasattr(connection_manager, 'stock_subscribers'):
            for stock_code, subscribers in connection_manager.stock_subscribers.items():
                stock_subscriptions[stock_code] = len(subscribers)
        
        return WebSocketMetrics(
            active_connections=active_connections,
            total_connections=active_connections,  # 실제로는 히스토리 관리 필요
            stock_subscriptions=stock_subscriptions
        )
    except Exception as e:
        logger.error(f"WebSocket 메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="WebSocket 메트릭 조회 실패")


@router.get("/metrics/queues", response_model=Dict[str, QueueMetrics])
async def get_queue_metrics(
    queue_manager: QueueManager = Depends(get_queue_manager)
):
    """
    Queue 메트릭 조회
    
    Returns:
        Dict[str, QueueMetrics]: Queue별 메트릭
    """
    try:
        all_metrics = queue_manager.get_all_metrics()
        
        result = {}
        for name, data in all_metrics.items():
            result[name] = QueueMetrics(**data)
        
        return result
    except Exception as e:
        logger.error(f"Queue 메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="Queue 메트릭 조회 실패")


@router.get("/metrics/all", response_model=SystemMetrics)
async def get_all_metrics(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector),
    queue_manager: QueueManager = Depends(get_queue_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    시스템 전체 메트릭 조회
    
    Returns:
        SystemMetrics: 시스템 전체 메트릭 정보
    """
    try:
        # 모든 메트릭 수집
        all_metrics = metrics_collector.get_all_metrics()
        health_data = metrics_collector.get_health_status()
        queue_metrics = queue_manager.get_all_metrics()
        
        # WebSocket 메트릭
        active_connections = len(connection_manager.active_connections)
        stock_subscriptions = {}
        if hasattr(connection_manager, 'stock_subscribers'):
            for stock_code, subscribers in connection_manager.stock_subscribers.items():
                stock_subscriptions[stock_code] = len(subscribers)
        
        websocket_metrics = WebSocketMetrics(
            active_connections=active_connections,
            total_connections=active_connections,
            stock_subscriptions=stock_subscriptions
        )
        
        # Circuit Breaker 메트릭 변환
        circuit_breakers = {}
        for name, data in all_metrics.get("circuit_breakers", {}).items():
            circuit_breakers[name] = CircuitBreakerMetrics(**data)
        
        # Queue 메트릭 변환
        queues = {}
        for name, data in queue_metrics.items():
            queues[name] = QueueMetrics(**data)
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            performance=PerformanceMetricsResponse(**all_metrics["performance"]),
            circuit_breakers=circuit_breakers,
            health=HealthStatus(**health_data),
            websocket=websocket_metrics,
            queues=queues
        )
    except Exception as e:
        logger.error(f"전체 메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="전체 메트릭 조회 실패")


@router.post("/reset")
async def reset_metrics(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """
    모든 메트릭 초기화
    
    Returns:
        dict: 초기화 결과
    """
    try:
        metrics_collector.reset_all()
        logger.info("모든 메트릭이 초기화되었습니다")
        return {"message": "메트릭 초기화 완료", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"메트릭 초기화 오류: {e}")
        raise HTTPException(status_code=500, detail="메트릭 초기화 실패")


@router.post("/circuit-breaker/{name}/reset")
async def reset_circuit_breaker(
    name: str,
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """
    특정 Circuit Breaker 초기화
    
    Args:
        name: Circuit Breaker 이름
    
    Returns:
        dict: 초기화 결과
    """
    try:
        cb = metrics_collector.get_circuit_breaker(name)
        if cb is None:
            raise HTTPException(status_code=404, detail=f"Circuit Breaker '{name}'를 찾을 수 없습니다")
        
        cb.reset()
        logger.info(f"Circuit Breaker '{name}'가 초기화되었습니다")
        return {"message": f"Circuit Breaker '{name}' 초기화 완료", "timestamp": datetime.now().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Circuit Breaker 초기화 오류: {e}")
        raise HTTPException(status_code=500, detail="Circuit Breaker 초기화 실패")


@router.get("/status")
async def get_system_status():
    """
    시스템 상태 요약 조회
    
    Returns:
        dict: 시스템 상태 요약
    """
    try:
        metrics_collector = get_metrics_collector()
        health_data = metrics_collector.get_health_status()
        
        # 간단한 상태 요약
        status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if health_data["is_healthy"] else "unhealthy",
            "summary": {
                "circuit_breakers_open": len(health_data["open_circuits"]),
                "circuit_breakers_half_open": len(health_data["half_open_circuits"]),
                "error_rate": health_data["error_rate"],
                "drop_rate": health_data["drop_rate"]
            },
            "alerts": []
        }
        
        # 알림 생성
        if health_data["open_circuits"]:
            status["alerts"].append(f"열린 Circuit Breaker: {', '.join(health_data['open_circuits'])}")
        
        if health_data["error_rate"] > 10.0:
            status["alerts"].append(f"높은 에러율: {health_data['error_rate']:.1f}%")
        
        if health_data["drop_rate"] > 5.0:
            status["alerts"].append(f"높은 드롭률: {health_data['drop_rate']:.1f}%")
        
        return status
    except Exception as e:
        logger.error(f"시스템 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="시스템 상태 조회 실패")


@router.get("/websocket-stats")
async def get_websocket_stats():
    """WebSocket 메시지 통계 조회"""
    try:
        stats = websocket_logger.get_statistics()
        
        # 전체 통계 요약
        total_messages = sum(stat['total_count'] for stat in stats.values())
        
        summary = {
            "total_messages": total_messages,
            "message_types": len(stats),
            "timestamp": datetime.now().isoformat(),
            "details": stats
        }
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"WebSocket 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="WebSocket 통계 조회 실패")


@router.post("/websocket-stats/reset")
async def reset_websocket_stats():
    """WebSocket 메시지 통계 초기화"""
    try:
        # 통계 초기화
        websocket_logger.message_counts.clear()
        websocket_logger.last_log_times.clear()
        websocket_logger.last_log_counts.clear()
        websocket_logger.message_buffers.clear()
        
        return {
            "success": True,
            "message": "WebSocket 통계가 초기화되었습니다."
        }
    except Exception as e:
        logger.error(f"WebSocket 통계 초기화 오류: {e}")
        raise HTTPException(status_code=500, detail="WebSocket 통계 초기화 실패")
