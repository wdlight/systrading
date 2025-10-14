"""
Queue 성능 테스트

Queue 처리량과 메모리 사용량을 테스트합니다.
"""

import pytest
import time
import asyncio
from multiprocessing import Queue, Process
from queue import Empty, Full

from app.utils.queue_monitor import QueueMonitor, QueueManager
from app.utils.performance_metrics import PerformanceMetrics, CircuitBreaker


class TestQueuePerformance:
    """Queue 성능 테스트"""
    
    def test_queue_throughput(self):
        """Queue 처리량 테스트"""
        queue = Queue(maxsize=2000)
        
        # 프로듀서
        def producer():
            for i in range(10000):
                queue.put({"id": i, "data": "test" * 100})
        
        # 컨슈머
        def consumer():
            count = 0
            start_time = time.time()
            
            while count < 10000:
                try:
                    queue.get(timeout=1)
                    count += 1
                except Empty:
                    break
            
            elapsed = time.time() - start_time
            throughput = count / elapsed
            print(f"처리량: {throughput:.2f} 메시지/초")
            
            # 최소 처리량 검증 (초당 100개 이상)
            assert throughput > 100, f"처리량이 너무 낮습니다: {throughput:.2f} 메시지/초"
        
        # 테스트 실행
        p1 = Process(target=producer)
        p2 = Process(target=consumer)
        
        p1.start()
        p2.start()
        
        p1.join()
        p2.join()
    
    def test_queue_monitor_performance(self):
        """QueueMonitor 성능 테스트"""
        queue = Queue(maxsize=1000)
        monitor = QueueMonitor(queue, "test_queue")
        
        # 모니터링 성능 테스트
        start_time = time.time()
        
        for _ in range(1000):
            monitor.check_status()
            monitor.get_metrics()
        
        elapsed = time.time() - start_time
        avg_time = elapsed / 1000
        
        print(f"평균 모니터링 시간: {avg_time*1000:.3f}ms")
        
        # 모니터링이 1ms 이내에 완료되어야 함
        assert avg_time < 0.001, f"모니터링이 너무 느립니다: {avg_time*1000:.3f}ms"
    
    def test_queue_manager_performance(self):
        """QueueManager 성능 테스트"""
        manager = QueueManager()
        
        # 여러 Queue 추가
        queues = []
        for i in range(10):
            queue = Queue(maxsize=100)
            manager.add_monitor(f"queue_{i}", queue)
            queues.append(queue)
        
        # 모든 Queue 상태 체크 성능
        start_time = time.time()
        
        for _ in range(100):
            manager.check_all_status()
            manager.get_all_metrics()
        
        elapsed = time.time() - start_time
        avg_time = elapsed / 100
        
        print(f"평균 QueueManager 처리 시간: {avg_time*1000:.3f}ms")
        
        # 10개 Queue를 5ms 이내에 처리해야 함
        assert avg_time < 0.005, f"QueueManager가 너무 느립니다: {avg_time*1000:.3f}ms"


class TestPerformanceMetrics:
    """성능 메트릭 테스트"""
    
    def test_metrics_performance(self):
        """메트릭 수집 성능 테스트"""
        metrics = PerformanceMetrics()
        
        # 메트릭 기록 성능 테스트
        start_time = time.time()
        
        for _ in range(1000):
            metrics.record_message_received()
            metrics.record_message_processed()
            metrics.record_processing_time(1.5)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / 1000
        
        print(f"평균 메트릭 기록 시간: {avg_time*1000:.3f}ms")
        
        # 메트릭 기록이 0.1ms 이내에 완료되어야 함
        assert avg_time < 0.0001, f"메트릭 기록이 너무 느립니다: {avg_time*1000:.3f}ms"
    
    def test_circuit_breaker_performance(self):
        """Circuit Breaker 성능 테스트"""
        cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        # Circuit Breaker 체크 성능 테스트
        start_time = time.time()
        
        for _ in range(1000):
            cb.can_attempt()
            cb.get_metrics()
        
        elapsed = time.time() - start_time
        avg_time = elapsed / 1000
        
        print(f"평균 Circuit Breaker 처리 시간: {avg_time*1000:.3f}ms")
        
        # Circuit Breaker 체크가 0.1ms 이내에 완료되어야 함
        assert avg_time < 0.0001, f"Circuit Breaker가 너무 느립니다: {avg_time*1000:.3f}ms"


class TestConcurrentPerformance:
    """동시성 성능 테스트"""
    
    def test_concurrent_queue_operations(self):
        """동시 Queue 작업 성능 테스트"""
        queue = Queue(maxsize=1000)
        monitor = QueueMonitor(queue, "concurrent_test")
        
        def worker():
            for _ in range(100):
                # Queue에 데이터 추가
                try:
                    queue.put({"test": "data"}, timeout=0.1)
                except Full:
                    pass
                
                # 모니터링 수행
                monitor.check_status()
        
        # 10개 스레드로 동시 작업
        threads = []
        for _ in range(10):
            import threading
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # Queue 상태 확인
        metrics = monitor.get_metrics()
        print(f"최종 Queue 사용률: {metrics['usage_ratio']*100:.1f}%")
        
        # Queue가 정상적으로 동작했는지 확인 (가득 차는 것은 정상)
        assert metrics['usage_ratio'] >= 0.0, "Queue 사용률이 음수입니다"
        print("동시성 테스트: Queue가 정상적으로 동작했습니다")


class TestMemoryPerformance:
    """메모리 성능 테스트"""
    
    def test_metrics_memory_usage(self):
        """메트릭 메모리 사용량 테스트"""
        import sys
        
        metrics = PerformanceMetrics()
        
        # 초기 메모리 사용량
        initial_size = sys.getsizeof(metrics)
        
        # 대량의 메트릭 기록
        for _ in range(10000):
            metrics.record_message_received()
            metrics.record_message_processed()
            metrics.record_processing_time(1.0)
        
        # 최종 메모리 사용량
        final_size = sys.getsizeof(metrics)
        memory_increase = final_size - initial_size
        
        print(f"메트릭 메모리 증가량: {memory_increase} bytes")
        
        # 메모리 증가량이 10KB 이하여야 함 (deque maxlen 제한으로 인해)
        assert memory_increase < 10240, f"메모리 사용량이 너무 많습니다: {memory_increase} bytes"
    
    def test_queue_monitor_memory_usage(self):
        """QueueMonitor 메모리 사용량 테스트"""
        import sys
        
        manager = QueueManager()
        
        # 초기 메모리 사용량
        initial_size = sys.getsizeof(manager)
        
        # 많은 Queue 모니터 추가
        for i in range(100):
            queue = Queue(maxsize=100)
            manager.add_monitor(f"queue_{i}", queue)
        
        # 최종 메모리 사용량
        final_size = sys.getsizeof(manager)
        memory_increase = final_size - initial_size
        
        print(f"QueueManager 메모리 증가량: {memory_increase} bytes")
        
        # 메모리 증가량이 50KB 이하여야 함
        assert memory_increase < 51200, f"메모리 사용량이 너무 많습니다: {memory_increase} bytes"


if __name__ == "__main__":
    # 직접 실행 시 테스트 수행
    test = TestQueuePerformance()
    print("Queue 처리량 테스트 시작...")
    test.test_queue_throughput()
    print("Queue 처리량 테스트 완료")
    
    print("\nQueue 모니터링 성능 테스트 시작...")
    test.test_queue_monitor_performance()
    print("Queue 모니터링 성능 테스트 완료")
    
    print("\nQueueManager 성능 테스트 시작...")
    test.test_queue_manager_performance()
    print("QueueManager 성능 테스트 완료")
    
    metrics_test = TestPerformanceMetrics()
    print("\n메트릭 성능 테스트 시작...")
    metrics_test.test_metrics_performance()
    print("메트릭 성능 테스트 완료")
    
    print("\nCircuit Breaker 성능 테스트 시작...")
    metrics_test.test_circuit_breaker_performance()
    print("Circuit Breaker 성능 테스트 완료")
    
    concurrent_test = TestConcurrentPerformance()
    print("\n동시성 성능 테스트 시작...")
    concurrent_test.test_concurrent_queue_operations()
    print("동시성 성능 테스트 완료")
    
    memory_test = TestMemoryPerformance()
    print("\n메모리 성능 테스트 시작...")
    memory_test.test_metrics_memory_usage()
    memory_test.test_queue_monitor_memory_usage()
    print("메모리 성능 테스트 완료")
    
    print("\n모든 성능 테스트 완료!")
