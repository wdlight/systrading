"""
실시간 데이터 서비스
기존 PyQt5의 타이머 기반 로직을 async/await로 변환
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable
from queue import Queue, Empty
import time
from pathlib import Path

from app.websocket.connection import ConnectionManager
from app.core.korea_invest import KoreaInvestAPIService
from app.models.schemas import ChartCandle
from app.models.realtime_minute import MinuteCandleState
from app.utils.performance_metrics import get_global_metrics_collector
from app.utils.time import parse_kis_time
from app.utils.websocket_logger import websocket_logger



class RealtimeDataService:
    """실시간 데이터 처리 서비스"""
    
    def __init__(self, korea_invest_service: KoreaInvestAPIService, connection_manager: ConnectionManager, ws_result_queue: Queue):
        self.korea_invest_service = korea_invest_service
        self.connection_manager = connection_manager
        self.ws_result_queue = ws_result_queue  # 웹소켓 결과 수신 큐
        self.is_running = False
        self.tasks = []
        
        # 성능 모니터링
        self.metrics_collector = get_global_metrics_collector()
        
        # 배치 처리 설정
        self.batch_size = 10  # 한 번에 처리할 메시지 수
        self.batch_timeout = 0.001  # 배치 타임아웃 (초)
        
        # 기존 DataFrame 구조 유지
        self.realtime_watchlist_df = pd.DataFrame(columns=[
            '현재가', '수익률', '평균단가', '보유수량', 'MACD', 'MACD시그널', 
            'RSI', '트레일링스탑발동여부', '트레일링스탑발동후고가'
        ])
        self.account_info_df = pd.DataFrame()
        
        # 최신 지수 값 캐시 (WebSocket → REST fallback에 활용)
        self.latest_market_indices: Dict[str, Dict[str, Any]] = {}

        # 호가 데이터 캐시 추가
        self.orderbook_cache: Dict[str, Dict[str, Any]] = {}  # {stock_code: OrderBookData}
        self.orderbook_cache_ttl = 300  # 5분 TTL (초)
        self.last_orderbook_update: Dict[str, float] = {}  # {stock_code: timestamp}

        # 실시간 분봉 집계 상태
        self.minute_candle_state: Dict[str, MinuteCandleState] = {}
        self.minute_state_lock = asyncio.Lock()
        self.minute_state_ttl = timedelta(minutes=10)
        self._last_acc_volume: Dict[str, int] = {}
        self.minute_finalize_queue: asyncio.Queue[Tuple[str, ChartCandle]] = asyncio.Queue(maxsize=200)
        self._minute_persist_handler: Optional[Callable[[str, ChartCandle], Awaitable[None]]] = None

        # 분봉 샘플 로그 설정
        sample_log_path = Path("logs/minute_candle_samples.log")
        sample_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.minute_log_handle = logger.add(
            sample_log_path,
            level="DEBUG",
            rotation="10 MB",
            enqueue=True,
            filter=lambda record: record["extra"].get("channel") == "minute_candle"
        )
        self.minute_logger = logger.bind(channel="minute_candle")
        self._sample_log_enabled = True
        self._sample_log_limit = 50
        self._sample_log_counter = 0

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
        
        logger.info("실시간 데이터 서비스가 초기화되었습니다 (호가 캐시 포함).")
    
    async def start(self):
        """실시간 데이터 서비스 시작"""
        if self.is_running:
            logger.warning("실시간 서비스가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        logger.info("실시간 데이터 서비스를 시작합니다.")
        
        # [2025-09-29 Gemini] IndentationError 수정 및 과도한 로그 발생시키는 _account_update_loop 주석 처리
        # --- 기존 코드 시작 (주석 처리) ---
        # try:
        #     # 기존 타이머들을 async task로 변환
        #             self.tasks = [
        #                 # asyncio.create_task(self._account_update_loop()),     # 2초 주기 (timer2) - 너무 많은 로그를 발생시켜 임시 주석 처리
        #                 asyncio.create_task(self._tr_result_loop()),          # 0.05초 주기 (timer3)                  asyncio.create_task(self._market_data_loop()),        # 2초 주기 (timer4)
        #         asyncio.create_task(self._settings_save_loop()),      # 10초 주기 (timer1)
        #         asyncio.create_task(self._heartbeat_loop())           # 30초 주기 (하트비트)
        #     ]
        #     
        #     # 모든 태스크가 완료될 때까지 대기 (실제로는 무한 루프)
        #     await asyncio.gather(*self.tasks, return_exceptions=True)
        #     
        # except Exception as e:
        #     logger.error(f"실시간 서비스 실행 중 오류: {str(e)}")
        #     await self.stop()
        # --- 기존 코드 끝 ---

        try:
            # 기존 타이머들을 async task로 변환
            self.tasks = [
                # asyncio.create_task(self._account_update_loop()),     # 2초 주기 (timer2) - 과도한 로그로 임시 주석 처리
                asyncio.create_task(self._tr_result_loop()),          # 0.05초 주기 (timer3)
                asyncio.create_task(self._market_data_loop()),        # 2초 주기 (timer4)
                asyncio.create_task(self._settings_save_loop()),      # 10초 주기 (timer1)
                asyncio.create_task(self._heartbeat_loop()),          # 30초 주기 (하트비트)
                asyncio.create_task(self._minute_persistence_worker()),
                asyncio.create_task(self._minute_state_cleanup_loop()),
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
        self._sample_log_enabled = False
        if hasattr(self, "minute_log_handle") and self.minute_log_handle is not None:
            try:
                logger.remove(self.minute_log_handle)
            except ValueError:
                pass
            self.minute_log_handle = None
        logger.info("실시간 데이터 서비스가 중지되었습니다.")

    def _extract_index_values(self, payload: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """WebSocket 지수 페이로드에서 현재가/변동값 추출"""
        if not payload:
            return None

        candidate_keys = [
            ("bstp_nmix_prpr", "bstp_nmix_prdy_vrss", "bstp_nmix_prdy_ctrt"),
            ("bstp_idx_prpr", "bstp_idx_prdy_vrss", "bstp_idx_prdy_ctrt"),
            ("bstp_undn_prpr", "bstp_undn_prdy_vrss", "bstp_undn_prdy_ctrt"),
        ]

        for current_key, change_key, rate_key in candidate_keys:
            current = payload.get(current_key)
            change = payload.get(change_key)
            rate = payload.get(rate_key)

            if current is None and change is None and rate is None:
                continue

            try:
                current_val = float(str(current).replace(",", "")) if current is not None else None
                change_val = float(str(change).replace(",", "")) if change is not None else None
                rate_val = float(str(rate).replace(",", "")) if rate is not None else None

                return {
                    "current": current_val,
                    "change": change_val,
                    "change_rate": rate_val,
                }
            except (TypeError, ValueError):
                continue

        return None

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
        """최적화된 TR 결과 처리 루프 (배치 처리)"""
        # logger.info("TR 결과 처리 루프 시작 (0.05초 주기)") # 로그가 너무 많이 쌓이므로 주석 처리
        
        while self.is_running:
            try:
                # 배치 처리로 메시지 수집
                messages = []
                
                # 배치로 메시지 수집 (최대 batch_size개)
                for _ in range(self.batch_size):
                    try:
                        message = self.ws_result_queue.get_nowait()
                        messages.append(message)
                        self.metrics_collector.metrics.record_message_received()
                    except Empty:
                        break
                
                if messages:
                    # 배치 처리
                    await self._process_message_batch(messages)
                
            except Exception as e:
                logger.error(f"TR 결과 처리 중 오류: {str(e)}")
                self.metrics_collector.metrics.record_parse_error()
            
            # 메시지가 없으면 대기 시간 증가
            if not messages:
                await asyncio.sleep(0.05)
            else:
                # 메시지가 있으면 즉시 다음 배치 처리
                await asyncio.sleep(self.batch_timeout)
    
    async def _process_message_batch(self, messages: List[Dict[str, Any]]):
        """메시지 배치 처리"""
        start_time = time.time()
        
        try:
            tasks = []
            
            for message in messages:
                action_id = message.get("action_id")
                
                if action_id == "실시간호가":
                    task = self._handle_hoga_data(message)
                    tasks.append(task)
                elif action_id == "실시간체결":
                    task = self._handle_tick_data(message)
                    tasks.append(task)
                elif action_id == "WEBSOCKET_PROCESS_ERROR":
                    # 치명적인 오류는 즉시 처리
                    logger.critical("!!! WebSocket 프로세스에서 치명적인 오류가 발생했습니다 !!!")
                    logger.error(f"오류: {message.get('error')}")
                    logger.error(f"Traceback:\n{message.get('traceback')}")
                    continue
                # 기타 타입 처리...
            
            # 병렬 처리
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # 처리 완료 메트릭 기록
                for _ in messages:
                    self.metrics_collector.metrics.record_message_processed()
        
        except Exception as e:
            logger.error(f"배치 처리 중 오류: {e}")
            self.metrics_collector.metrics.record_parse_error()
        
        finally:
            # 처리 시간 기록
            processing_time_ms = (time.time() - start_time) * 1000
            self.metrics_collector.metrics.record_processing_time(processing_time_ms)
    
    async def _handle_hoga_data(self, message: Dict[str, Any]):
        """
        실시간 호가 데이터 처리 및 캐시 저장
        
        Args:
            message: {
                "action_id": "실시간호가",
                "stock_code": "005930",
                "data": {
                    "stock_code": "005930",
                    "asks": [...],
                    "bids": [...],
                    "current_price": 71700,
                    "timestamp": "2025-10-14T18:00:15",
                    "market_data": {...}
                }
            }
        """
        try:
            stock_code = message.get("stock_code")
            hoga_data = message.get("data", {})
            
            if not stock_code or not hoga_data:
                logger.warning(f"호가 데이터 누락: {message}")
                return
            
            # 장 시간 체크
            from app.utils.trading_hours import TradingHoursManager
            from datetime import datetime
            if not TradingHoursManager.is_trading_hours(datetime.now()):
                logger.debug(f"장 시간 외 호가 데이터 무시: {stock_code}")
                return
            
            # 캐시에 저장
            current_time = time.time()
            logger.info(f"📊 호가 데이터 처리: {stock_code}, 현재가={hoga_data.get('current_price')}, 매도1={hoga_data.get('asks', [{}])[0].get('price', 0)}, 매수1={hoga_data.get('bids', [{}])[0].get('price', 0)}")
            logger.info(f" RAW Data: {hoga_data}")
            self.orderbook_cache[stock_code] = {
                "stock_code": stock_code,
                "current_price": hoga_data.get("current_price"),
                "asks": hoga_data.get("asks", []),
                "bids": hoga_data.get("bids", []),
                "timestamp": hoga_data.get("timestamp"),
                "market_status": "open",
                "market_data": hoga_data.get("market_data", {})
            }
            self.last_orderbook_update[stock_code] = current_time
            
            # Frontend로 브로드캐스트 (구독자에게만)
            broadcast_message = {
                "type": "orderbook_update",
                "stock_code": stock_code,
                "data": {
                    "asks": hoga_data.get("asks", []),
                    "bids": hoga_data.get("bids", []),
                    "current_price": hoga_data.get("current_price"),
                    "timestamp": hoga_data.get("timestamp")
                },
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"📡 호가 데이터 브로드캐스트: {stock_code}")
            await self.connection_manager.broadcast_to_stock_subscribers(
                stock_code,
                broadcast_message
            )
            
            self.metrics_collector.metrics.record_message_processed()
            logger.debug(f"호가 데이터 처리 완료: {stock_code}")
            
        except Exception as e:
            logger.error(f"호가 데이터 처리 중 오류: {e}")
            self.metrics_collector.metrics.record_broadcast_error()

    def get_cached_orderbook(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        캐시된 호가 데이터 조회
        
        Args:
            stock_code: 종목 코드
        
        Returns:
            캐시된 호가 데이터 또는 None (만료/없음)
        """
        current_time = time.time()
        
        # 캐시 존재 여부 확인
        if stock_code not in self.orderbook_cache:
            return None
        
        # TTL 체크
        last_update = self.last_orderbook_update.get(stock_code, 0)
        if current_time - last_update > self.orderbook_cache_ttl:
            # 만료된 캐시 삭제
            del self.orderbook_cache[stock_code]
            del self.last_orderbook_update[stock_code]
            logger.debug(f"호가 캐시 만료: {stock_code}")
            return None
        
        return self.orderbook_cache[stock_code]

    def invalidate_orderbook_cache(self, stock_code: str) -> None:
        """
        특정 종목의 호가 캐시 즉시 무효화 (개선)
        
        Args:
            stock_code: 종목 코드
        
        Note:
            클라이언트가 구독 해제(unsubscribe) 시 호출하여
            stale 데이터 반환을 방지합니다.
        
        Example:
            # 구독 해제 시
            realtime_service.invalidate_orderbook_cache("005930")
        """
        if stock_code in self.orderbook_cache:
            del self.orderbook_cache[stock_code]
            logger.info(f"호가 캐시 무효화: {stock_code}")
        
        if stock_code in self.last_orderbook_update:
            del self.last_orderbook_update[stock_code]
    
    async def _handle_tick_data(self, message: Dict[str, Any]):
        """체결 데이터 처리 및 분봉 집계"""
        try:
            data = message.get("data", {})
            stock_code = message.get("stock_code") or data.get("stock_code")

            if not stock_code:
                return

            price = float(data.get("price", 0) or 0)
            if price <= 0:
                return

            executed_time = data.get("executed_time")
            if not executed_time:
                return

            trade_volume = int(data.get("trade_volume", 0) or 0)
            acc_volume = int(data.get("acc_volume", 0) or 0)

            # Fallback: 누적 거래량 증분으로 체결량 계산
            previous_acc = self._last_acc_volume.get(stock_code)
            if trade_volume <= 0 and previous_acc is not None and acc_volume >= previous_acc:
                trade_volume = acc_volume - previous_acc
            if trade_volume < 0:
                logger.warning(f"음수 체결량 감지 → 0으로 보정: {stock_code}, delta={trade_volume}")
                trade_volume = 0
            if acc_volume > 0:
                self._last_acc_volume[stock_code] = acc_volume

            executed_ts = parse_kis_time(executed_time)
            minute_key = executed_ts.strftime("%Y-%m-%dT%H:%M:00")

            # 샘플 로그
            if getattr(self, "_sample_log_enabled", False) and self._sample_log_counter < self._sample_log_limit:
                self._sample_log_counter += 1
                self.minute_logger.debug(
                    "tick sample | stock={stock} minute={minute} payload={payload}",
                    stock=stock_code,
                    minute=minute_key,
                    payload=data.get("raw_payload") or message.get("raw_payload")
                )
                if self._sample_log_counter >= self._sample_log_limit:
                    self._sample_log_enabled = False

            # 분봉 상태 갱신
            async with self.minute_state_lock:
                state = self.minute_candle_state.get(stock_code)

                if state and state.minute_key != minute_key:
                    await self._flush_closed_candle(stock_code, state)
                    state = None

                if not state:
                    state = MinuteCandleState(
                        minute_key=minute_key,
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                        volume=trade_volume,
                        start_ts=executed_ts,
                        last_tick_ts=executed_ts,
                    )
                    self.minute_candle_state[stock_code] = state
                else:
                    state.apply_tick(price, trade_volume, executed_ts)

            await self._broadcast_minute_snapshot(stock_code, state)

            # 워치리스트 가격 갱신 (기존 기능 유지)
            if stock_code in self.realtime_watchlist_df.index:
                self.realtime_watchlist_df.loc[stock_code, "현재가"] = price
                await self.connection_manager.broadcast({
                    "type": "tick_update",
                    "stock_code": stock_code,
                    "current_price": price,
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            logger.error(f"체결 데이터 처리 오류: {e}")
            self.metrics_collector.metrics.record_broadcast_error()

    async def _broadcast_minute_snapshot(self, stock_code: str, state: MinuteCandleState):
        """현재 진행 중인 분봉 스냅샷 브로드캐스트"""
        payload = {
            "type": "minute_candle_update",
            "stock_code": stock_code,
            "data": {
                "timestamp": state.minute_key,
                "open": state.open,
                "high": state.high,
                "low": state.low,
                "close": state.close,
                "volume": state.volume,
                "last_tick": state.last_tick_ts.isoformat(),
            }
        }
        await self.connection_manager.broadcast(payload)

    async def _flush_closed_candle(self, stock_code: str, state: MinuteCandleState) -> None:
        """분 경계 통과 시 완료된 캔들을 확정하고 persistence 큐로 전달"""
        candle = state.to_chart_candle()
        await self._enqueue_candle_for_persistence(stock_code, candle)
        await self.connection_manager.broadcast({
            "type": "minute_candle_finalize",
            "stock_code": stock_code,
            "data": candle.model_dump(),
        })
        self.minute_candle_state.pop(stock_code, None)

    async def _enqueue_candle_for_persistence(self, stock_code: str, candle: ChartCandle) -> None:
        try:
            self.minute_finalize_queue.put_nowait((stock_code, candle))
        except asyncio.QueueFull:
            logger.warning(f"minute_finalize_queue 가득 참: {stock_code}, {candle.timestamp}")

    async def _minute_persistence_worker(self):
        logger.info("분봉 persistence worker 시작")
        try:
            while self.is_running or not self.minute_finalize_queue.empty():
                try:
                    stock_code, candle = await asyncio.wait_for(self.minute_finalize_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

                try:
                    if self._minute_persist_handler:
                        await self._minute_persist_handler(stock_code, candle)
                    else:
                        logger.debug(f"분봉 persistence handler 미설정 - {stock_code} {candle.timestamp}")
                except Exception as exc:
                    logger.error(f"분봉 persistence 처리 실패: {exc}")
                finally:
                    self.minute_finalize_queue.task_done()
        finally:
            logger.info("분봉 persistence worker 종료")

    async def _minute_state_cleanup_loop(self):
        logger.info("분봉 상태 정리 루프 시작 (60초 주기)")
        try:
            while self.is_running:
                await asyncio.sleep(60)
                await self._drain_stale_states()
        except asyncio.CancelledError:
            logger.info("분봉 상태 정리 루프가 취소되었습니다.")

    async def _drain_stale_states(self):
        cutoff = datetime.now() - self.minute_state_ttl
        async with self.minute_state_lock:
            stale_keys = [
                code for code, state in self.minute_candle_state.items()
                if state.last_tick_ts < cutoff
            ]
            for code in stale_keys:
                logger.debug(f"분봉 상태 정리: {code}")
                self.minute_candle_state.pop(code, None)
                self._last_acc_volume.pop(code, None)

    def set_minute_persist_handler(self, handler: Callable[[str, ChartCandle], Awaitable[None]]) -> None:
        """외부에서 persistence 핸들러를 주입"""
        self._minute_persist_handler = handler
    
    async def _market_data_loop(self):
        """시장 데이터 업데이트 루프 (기존 timer4 로직)"""
        logger.info("시장 데이터 업데이트 루프 시작 (2초 주기)")
        
        while self.is_running:
            try:
                from app.utils.trading_hours import TradingHoursManager
                current_time = datetime.now()
                
                # 장 시간 체크
                if TradingHoursManager.is_trading_hours(current_time, include_extended=True):
                    # 장 시간: 상태 변경 체크 및 정상 워치리스트 업데이트
                    session = TradingHoursManager.get_session(current_time)
                    
                    # 장 시간 진입 시 상태 변경 알림
                    if not hasattr(self, '_last_market_session') or self._last_market_session != session.value:
                        self._last_market_session = session.value
                        
                        status_message = {
                            "type": "market_status_update",
                            "data": {
                                "status": "open",
                                "session": session.value,
                                "message": self._get_after_hours_message(session),
                                "next_open": None,
                                "last_data_timestamp": None
                            },
                            "timestamp": current_time.isoformat()
                        }
                        
                        await self.connection_manager.broadcast(status_message)
                        logger.info(f"시장 상태 변경 알림 전송: {session.value}")
                    
                    # 정상 워치리스트 업데이트
                    watchlist_data = await self._update_watchlist()
                    
                    if watchlist_data:
                        await self.connection_manager.broadcast({
                            "type": "watchlist_update",
                            "data": watchlist_data,
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    # 장 시간 외: 마지막 데이터 유지 및 상태 메시지 전송
                    await self._handle_after_hours_update()
                
            except Exception as e:
                logger.error(f"시장 데이터 업데이트 중 오류: {str(e)}")
            
            await asyncio.sleep(2)  # 2초 대기

    async def _handle_after_hours_update(self):
        """장 시간 외 업데이트 처리"""
        try:
            from app.utils.trading_hours import TradingHoursManager
            
            current_time = datetime.now()
            session = TradingHoursManager.get_session(current_time)
            
            # 상태 변경 시에만 메시지 전송
            if not hasattr(self, '_last_market_session') or self._last_market_session != session.value:
                self._last_market_session = session.value
                
                status_message = {
                    "type": "market_status_update",
                    "data": {
                        "status": "closed",
                        "session": session.value,
                        "message": self._get_after_hours_message(session),
                        "next_open": self._get_next_market_open_time(),
                        "last_data_timestamp": self._get_last_data_timestamp()
                    },
                    "timestamp": current_time.isoformat()
                }
                
                await self.connection_manager.broadcast(status_message)
                logger.info(f"시장 상태 변경 알림 전송: {session.value}")
            
            # 마지막 데이터가 있으면 30초마다만 전송
            if hasattr(self, '_last_watchlist_data') and self._last_watchlist_data:
                last_send_time = getattr(self, '_last_watchlist_send_time', None)
                if not last_send_time or (current_time - last_send_time).total_seconds() >= 30:
                    self._last_watchlist_send_time = current_time
                    
                    await self.connection_manager.broadcast({
                        "type": "watchlist_update",
                        "data": self._last_watchlist_data,
                        "timestamp": current_time.isoformat(),
                        "note": "장 시간 외 - 마지막 데이터"
                    })
                    logger.debug("장 시간 외 마지막 데이터 전송")
                
        except Exception as e:
            logger.error(f"장 시간 외 업데이트 처리 중 오류: {e}")

    def _get_after_hours_message(self, session) -> str:
        """장 시간 외 상태 메시지 생성"""
        messages = {
            "closed": "장 시간 외입니다. 다음 거래일 09:00에 다시 시작됩니다.",
            "pre_market": "장 시작 전입니다. 09:00에 정규 장이 시작됩니다.",
            "after_market": "장 종료 후 시간외 거래 시간입니다. 16:00에 완전 종료됩니다.",
            "regular": "정규 장 시간입니다."
        }
        return messages.get(session.value, "거래 시간 정보를 확인할 수 없습니다.")

    def _get_next_market_open_time(self) -> str:
        """다음 장 시작 시간 계산"""
        from datetime import timedelta
        from app.utils.trading_hours import TradingHoursManager
        
        current_time = datetime.now()
        tomorrow = current_time + timedelta(days=1)
        next_open = datetime.combine(tomorrow.date(), TradingHoursManager.REGULAR_MARKET_START)
        
        return next_open.isoformat()

    def _get_last_data_timestamp(self) -> Optional[str]:
        """마지막 데이터 타임스탬프 반환"""
        if hasattr(self, '_last_watchlist_data') and self._last_watchlist_data:
            return self._last_watchlist_data.get('timestamp')
        return None
    
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
    
    async def _websocket_stats_loop(self):
        """WebSocket 통계 로깅 루프 (5분마다)"""
        logger.info("WebSocket 통계 로깅 루프 시작 (5분 주기)")
        
        while self.is_running:
            try:
                # WebSocket 통계 로깅
                websocket_logger.log_statistics()
                
            except Exception as e:
                logger.error(f"WebSocket 통계 로깅 중 오류: {str(e)}")
            
            await asyncio.sleep(300)  # 5분 대기
    
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
    
    def get_metrics(self):
        """메트릭 수집기 반환"""
        return self.metrics_collector
    
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
            
            # 마지막 데이터 저장 (장 시간 외에 사용)
            if watchlist_data:
                self._last_watchlist_data = {
                    "data": watchlist_data,
                    "timestamp": datetime.now().isoformat()
                }
            
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
