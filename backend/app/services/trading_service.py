"""
매매 서비스
자동매매 설정, 주문 처리 등 매매 관련 비즈니스 로직 처리
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime, timedelta
import json
import os

from app.models.schemas import OrderHistory, ChartCandle
from app.models.watchlist_models import (
    TradingConditions, TradeExecutionResult, WatchlistItem,
    BuyConditions, SellConditions, TechnicalIndicators
)
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.chart_cache_service import ChartCacheService
from app.core.korea_invest import KoreaInvestAPIService
from app.utils.trading_hours import TradingHoursManager
from app.utils.trading_calendar import get_default_calendar


class TradingService:
    """매매 관련 서비스"""
    
    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest_service = korea_invest_service
        self.is_trading_active = False
        self.trading_start_time = None
        self.trading_conditions = None
        self.order_history = []
        self.trading_stats = {
            "total_trades": 0,
            "profit_trades": 0,
            "loss_trades": 0,
            "total_profit_loss": 0.0
        }

        # 차트 데이터 캐시 서비스 초기화
        self.chart_cache_service = ChartCacheService(cache_dir="kordata")

        # 설정 파일 경로
        self.settings_file = "trading_settings.json"
        self._load_settings()

    async def get_minute_chart_data(
        self,
        stock_code: str,
        target_date: Optional[datetime] = None,
        include_extended_hours: bool = False,
        regular_hours_only: bool = True
    ) -> Optional[List[ChartCandle]]:
        """
        분봉 차트 데이터를 조회합니다 (캐시 우선, 거래시간 필터링 포함)

        Args:
            stock_code: 종목 코드
            target_date: 조회할 날짜 (None이면 오늘)
            include_extended_hours: 시간외 거래 포함 여부 (8:30~16:00)
            regular_hours_only: 정규 장만 (9:00~15:30)

        Returns:
            필터링된 분봉 데이터 리스트
        """
        # 날짜 설정 (None이면 오늘)
        query_date = target_date if target_date else datetime.now()

        # 오늘 데이터 요청 시 비거래일이면 최근 거래일로 변경
        calendar = get_default_calendar()
        if target_date is None and not calendar.is_trading_day(query_date):
            try:
                last_trading_day = calendar.get_previous_trading_days(query_date, 1)[0]
                logger.info(f"오늘은 비거래일입니다. 최근 거래일({last_trading_day.strftime('%Y-%m-%d')}) 데이터로 대체합니다.")
                query_date = last_trading_day
            except IndexError:
                logger.warning("이전 거래일을 찾을 수 없습니다.")
                # 특별한 처리 없이 그대로 진행 (데이터 없음으로 응답될 것)
                pass

        # ✅ 오늘 vs 과거 날짜 판별
        is_today = query_date.date() == datetime.now().date()

        logger.info(f"📊 분봉 조회: {stock_code}, 날짜={query_date.strftime('%Y-%m-%d')}, 오늘여부={is_today}")

        if is_today:
            # 기존 로직: 실시간 API + Gap-fill
            raw_data = await self.chart_cache_service.get_minute_candles(
                stock_code=stock_code,
                target_date=query_date,
                korea_invest_service=self.korea_invest_service  # ✅ 직접 service 전달
            )
        else:
            # ✅ 신규 로직: 과거 날짜 전체 조회
            raw_data = await self.chart_cache_service.get_historical_minute_candles(
                stock_code=stock_code,
                target_date=query_date,
                korea_invest_service=self.korea_invest_service
            )

        if not raw_data:
            logger.warning(f"⚠️ 데이터 없음: {stock_code}, {query_date.strftime('%Y-%m-%d')}")
            return None

        # ✅ 수정: raw_data에서 실제 데이터의 날짜를 확인하여 필터링 기준 결정
        # (비거래일의 경우 이전 거래일 데이터가 반환되므로, 첫 번째 캔들의 날짜를 기준으로 함)
        actual_data_date = None
        if raw_data and len(raw_data) > 0:
            try:
                first_candle_time = datetime.fromisoformat(raw_data[0].timestamp)
                actual_data_date = first_candle_time.date()
                logger.info(f"실제 데이터 날짜: {actual_data_date}, 요청 날짜: {query_date.date()}")
            except:
                pass

        # 필터링 로직
        filtered_data = []

        for candle in raw_data:
            try:
                # 타임스탬프 파싱
                candle_time = datetime.fromisoformat(candle.timestamp)
            except ValueError:
                logger.warning(f"잘못된 타임스탬프 형식: {candle.timestamp}")
                continue

            # ✅ 수정: 날짜 필터링 - actual_data_date 기준으로 필터링
            if target_date:
                # 특정 날짜 지정된 경우
                # 비거래일의 경우 이전 거래일 데이터를 받으므로, actual_data_date와 비교
                if actual_data_date and candle_time.date() != actual_data_date:
                    continue
                elif not actual_data_date and candle_time.date() != target_date.date():
                    continue
            else:
                # 날짜 미지정 시 - 비거래일이면 이전 거래일 데이터 허용
                if actual_data_date:
                    # actual_data_date가 있으면 해당 날짜 데이터만 허용
                    if candle_time.date() != actual_data_date:
                        continue
                else:
                    # actual_data_date가 없으면 오늘 데이터만
                    if not TradingHoursManager.is_today(candle_time):
                        continue

            # 거래시간 필터링
            if regular_hours_only:
                # 정규 장만 (9:00 ~ 15:30)
                if not TradingHoursManager.is_regular_hours(candle_time):
                    continue
            elif not include_extended_hours:
                # 시간외 미포함, 정규장만
                if not TradingHoursManager.is_regular_hours(candle_time):
                    continue
            else:
                # 시간외 포함 (8:30 ~ 16:00)
                if not TradingHoursManager.is_trading_hours(candle_time, include_extended=True):
                    continue

            filtered_data.append(candle)

        logger.info(f"분봉 데이터 필터링: {len(raw_data)}개 → {len(filtered_data)}개 (정규장: {regular_hours_only}, 시간외: {include_extended_hours})")
        return filtered_data

    async def get_day_chart_data(
        self,
        stock_code: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[List[ChartCandle]]:
        """
        일봉 차트 데이터를 조회합니다 (캐시 우선)
        """
        logger.info(f"일봉 데이터 서비스 요청: {stock_code}, {start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}")
        try:
            daily_candles = await self.chart_cache_service.get_daily_candles(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                korea_invest_service=self.korea_invest_service
            )
            if daily_candles is None:
                daily_candles = []

            today = datetime.now().date()
            calendar = get_default_calendar()
            if calendar.is_trading_day(today) and start_date.date() <= today <= end_date.date():
                intraday_candle = await self._build_daily_candle_from_minutes(
                    stock_code,
                    datetime.combine(today, datetime.min.time())
                )
                if intraday_candle:
                    today_str = intraday_candle.timestamp[:10]
                    daily_candles = [
                        candle for candle in daily_candles
                        if candle.timestamp[:10] != today_str
                    ]
                    daily_candles.append(intraday_candle)
                    daily_candles.sort(key=lambda c: c.timestamp)

            return daily_candles
        except Exception as e:
            logger.error(f"일봉 데이터 서비스 처리 중 오류 발생: {e}")
            return None

    async def _build_daily_candle_from_minutes(
        self,
        stock_code: str,
        target_date: datetime
    ) -> Optional[ChartCandle]:
        """
        분봉 데이터를 기반으로 당일 일봉을 실시간 생성
        """
        minute_candles = await self.get_minute_chart_data(
            stock_code=stock_code,
            target_date=target_date,
            include_extended_hours=False,
            regular_hours_only=True
        )

        if not minute_candles:
            logger.info(
                f"실시간 일봉 생성 실패: 분봉 데이터 없음 ({stock_code}, {target_date.strftime('%Y-%m-%d')})"
            )
            return None

        minute_candles = sorted(
            minute_candles,
            key=lambda c: datetime.fromisoformat(c.timestamp)
        )

        open_price = minute_candles[0].open
        close_price = minute_candles[-1].close
        high_price = max(c.high for c in minute_candles)
        low_price = min(c.low for c in minute_candles)
        total_volume = sum(c.volume or 0 for c in minute_candles)

        intraday_candle = ChartCandle(
            timestamp=target_date.strftime("%Y-%m-%dT00:00:00"),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=int(total_volume),
        )

        logger.info(
            f"실시간 일봉 생성: {stock_code} {intraday_candle.timestamp} "
            f"O:{open_price} H:{high_price} L:{low_price} C:{close_price} V:{total_volume}"
        )

        return intraday_candle

    async def get_full_day_candles(
        self,
        stock_code: str,
        target_date: Optional[datetime] = None,
        days: int = 3
    ) -> Optional[List[ChartCandle]]:
        """
        최근 N일치 전체 거래시간(9:00~15:30) 분봉 데이터 반환
        
        - 실제 거래된 시간: 실제 OHLCV 데이터
        - 미래 시간 또는 거래 없는 시간: 직전 종가로 채움 (volume=0)
        - 기본 3일치 데이터 반환 (약 1173개 캔들)
        
        Args:
            stock_code: 종목 코드
            target_date: 조회 종료 날짜 (None이면 오늘)
            days: 조회할 일수 (기본 3일)
            
        Returns:
            최근 N일치 전체 분봉 데이터
        """
        from datetime import timedelta, timezone
        
        KST = timezone(timedelta(hours=9))

        # 날짜 설정 (timezone-aware)
        if target_date:
            if target_date.tzinfo is None:
                end_date = target_date.replace(tzinfo=KST)
            else:
                end_date = target_date.astimezone(KST)
        else:
            end_date = datetime.now(KST)
        
        # ✅ N일치 데이터 수집
        all_candles = []
        
        for day_offset in range(days - 1, -1, -1):  # 3일이면: 2, 1, 0 (과거→현재 순서)
            query_date = end_date - timedelta(days=day_offset)
            
            logger.info(f"📅 Day {days - day_offset}/{days}: {query_date.strftime('%Y-%m-%d')} 데이터 로드 중...")
            
            # 캐시를 통해 실제 데이터 조회 (skip_cache_save=True로 중간 저장 방지)
            raw_data = await self.chart_cache_service.get_minute_candles(
                stock_code=stock_code,
                target_date=query_date,
                korea_invest_service=self.korea_invest_service,
                skip_cache_save=True
            )

            if not raw_data:
                logger.warning(f"차트 데이터 없음: {stock_code}, {query_date.strftime('%Y-%m-%d')}")
                continue

            # ✅ 비거래일 처리: 이전 거래일 데이터를 그대로 반환
            # raw_data의 첫 번째 캔들 날짜를 확인하여 실제 데이터 날짜 파악
            if raw_data:
                first_candle_date = datetime.fromisoformat(raw_data[0].timestamp).date()
                query_date_only = query_date.date()

                # 요청한 날짜와 실제 데이터 날짜가 다르면 비거래일
                if first_candle_date != query_date_only:
                    logger.info(
                        f"📅 비거래일 감지: 요청={query_date_only}, 실제 데이터={first_candle_date}, "
                        f"이전 거래일 데이터 그대로 반환 ({len(raw_data)}개 캔들)"
                    )
                    # 이전 거래일의 전체 데이터를 그대로 반환 (타임라인 재생성 없이)
                    all_candles.extend(raw_data)
                    continue

            # 거래일인 경우: 전체 거래시간 타임라인 생성
            trading_start = query_date.replace(hour=9, minute=0, second=0, microsecond=0)

            now = datetime.now(KST)
            is_today = query_date.date() == now.date()

            if is_today:
                # 당일: 현재 시간까지만 (초/마이크로초 제거)
                trading_end = now.replace(second=0, microsecond=0)

                # 장 시작 전이면 전일 데이터 사용 (09:00 기준)
                market_open = query_date.replace(hour=9, minute=0, second=0, microsecond=0)
                if trading_end < market_open:
                    logger.info(f"장 시작 전 (현재: {trading_end.strftime('%H:%M')}), 이전 거래일 데이터 그대로 반환")
                    all_candles.extend(raw_data)
                    continue

                # 거래시간 이후면 15:30으로 제한
                market_close = query_date.replace(hour=15, minute=30, second=0, microsecond=0)
                if trading_end > market_close:
                    trading_end = market_close
                logger.info(f"당일 타임라인 생성: 9:00 ~ {trading_end.strftime('%H:%M')}")
            else:
                # 과거: 전체 거래시간
                trading_end = query_date.replace(hour=15, minute=30, second=0, microsecond=0)
                logger.info(f"과거 타임라인 생성: 9:00 ~ 15:30")

            # 1분 간격 타임스탬프 생성
            timeline = []
            current_time = trading_start
            while current_time <= trading_end:
                timeline.append(current_time)
                current_time += timedelta(minutes=1)

            logger.info(f"타임라인 생성 완료: {len(timeline)}개 캔들")
            
            # 실제 데이터를 딕셔너리로 변환 (빠른 검색)
            data_dict = {}
            for candle in raw_data:
                try:
                    candle_time = datetime.fromisoformat(candle.timestamp)
                    # 시간만 비교 (초/마이크로초 제거)
                    key_time = candle_time.replace(second=0, microsecond=0)
                    data_dict[key_time] = candle
                except ValueError:
                    logger.warning(f"잘못된 타임스탬프 형식: {candle.timestamp}")
                    continue
            
            logger.info(f"실제 데이터: {len(data_dict)}개")
            
            # 전체 타임라인에 데이터 채우기
            day_candles = []
            last_close = None

            # 첫 번째 실제 데이터 시간 확인
            first_data_time = None
            if data_dict:
                first_data_time = min(data_dict.keys())
                logger.info(f"첫 실제 데이터 시각: {first_data_time.strftime('%H:%M')}")

            for ts in timeline:
                if ts in data_dict:
                    # 실제 데이터 존재
                    candle = data_dict[ts]
                    last_close = candle.close
                    day_candles.append(candle)
                else:
                    # 데이터 없음 → 채우기 여부 판단
                    # ✅ 수정: 첫 실제 데이터 이전 시간은 skip (더미 데이터 생성 방지)
                    if first_data_time and ts < first_data_time:
                        # 실제 거래 데이터 이전 시간대는 채우지 않음
                        continue

                    # 미래 시간(현재 분 이후)만 last_close로 채우기
                    if last_close is not None:
                        day_candles.append(ChartCandle(
                            timestamp=ts.isoformat(),
                            open=last_close,
                            high=last_close,
                            low=last_close,
                            close=last_close,
                            volume=0  # volume=0으로 미래/거래없음 표시
                        ))
                    # else: 데이터가 전혀 없는 경우 skip
            
            logger.info(f"Day {days - day_offset} candles 생성 완료: {len(day_candles)}개 (실제: {len(data_dict)}, 채움: {len(day_candles) - len(data_dict)})")

            # 데이터 검증 로깅
            expected_count = len(timeline)  # 당일/과거 구분에 따른 예상 개수
            if len(day_candles) != expected_count:
                logger.warning(
                    f"⚠️ VALIDATION: Expected {expected_count} candles, got {len(day_candles)} "
                    f"({'당일 9:00~현재' if is_today else '과거 9:00~15:30'})"
                )

            volume_zero_count = sum(1 for c in day_candles if c.volume == 0)
            logger.info(
                f"✅ VALIDATION: {len(day_candles)} candles total | "
                f"{volume_zero_count} filled | {len(day_candles) - volume_zero_count} actual | "
                f"기간: {trading_start.strftime('%H:%M')}~{trading_end.strftime('%H:%M')} "
                f"({'당일' if is_today else '과거'})"
            )

            # 하루치 데이터를 전체 리스트에 추가
            all_candles.extend(day_candles)

            # Full Day 데이터를 캐시에 저장 (기존 부분 데이터 덮어쓰기)
            if day_candles:
                self.chart_cache_service._save_to_cache(stock_code, query_date, day_candles)
                logger.info(f"Full day candles 캐시 저장 완료: {stock_code}, {query_date.strftime('%Y-%m-%d')}")
        
        if not all_candles:
            logger.warning(f"전체 기간 데이터 없음: {stock_code}, {days}일")
            return None
        
        logger.info(f"🎯 최종 {days}일치 데이터 반환: 총 {len(all_candles)}개 캔들")
        return all_candles

    async def get_current_minute_candle(
        self,
        stock_code: str
    ) -> Optional[ChartCandle]:
        """
        현재 분(minute)의 최신 캔들 데이터 조회

        - 한투 API에서 최신 분봉 데이터 fetch
        - 매 분마다 호출 가능
        - 실시간 업데이트용

        Args:
            stock_code: 종목 코드

        Returns:
            현재 분의 ChartCandle 또는 None
        """
        try:
            # API에서 전체 분봉 데이터 조회 (최신 포함)
            raw_data = await self.korea_invest_service.get_minute_chart_data(stock_code)

            if not raw_data or len(raw_data) == 0:
                logger.warning(f"현재 분봉 데이터 없음: {stock_code}")
                return None

            # 가장 최신 캔들 찾기 (timestamp 기준 정렬)
            # timestamp를 datetime으로 변환하여 비교
            latest_candle = max(raw_data, key=lambda c: datetime.fromisoformat(c.timestamp))

            logger.info(f"최신 분봉 조회 완료: {stock_code}, timestamp={latest_candle.timestamp}, volume={latest_candle.volume}")

            return latest_candle

        except Exception as e:
            logger.error(f"현재 분봉 조회 실패: {stock_code}, 오류: {e}")
            return None

    async def update_minute_candle(
        self,
        stock_code: str,
        target_date: datetime,
        candle_data: ChartCandle
    ) -> bool:
        """
        특정 분봉 데이터만 업데이트 (Cache 파일 부분 갱신)

        - 기존 391개 candle 로드
        - 해당 timestamp 찾아서 교체
        - Cache 파일 저장

        Args:
            stock_code: 종목 코드
            target_date: 날짜
            candle_data: 업데이트할 캔들 데이터

        Returns:
            업데이트 성공 여부
        """
        try:
            # 1. 기존 391개 candle 로드
            cached_candles = self.chart_cache_service._load_from_cache(stock_code, target_date)

            if not cached_candles:
                logger.warning(f"Cache 파일 없음: {stock_code}, {target_date.strftime('%Y-%m-%d')}")
                return False

            # 2. 해당 timestamp 찾아서 업데이트 또는 추가
            updated = False
            candle_timestamp = candle_data.timestamp

            for i, candle in enumerate(cached_candles):
                if candle.timestamp == candle_timestamp:
                    cached_candles[i] = candle_data
                    updated = True
                    logger.info(f"분봉 업데이트: {stock_code}, {candle_timestamp}, volume={candle_data.volume}")
                    break

            if not updated:
                # timestamp가 없으면 새로 추가 (실시간 데이터)
                cached_candles.append(candle_data)
                logger.info(f"분봉 추가: {stock_code}, {candle_timestamp}, volume={candle_data.volume}")

                # 시간순 정렬
                cached_candles.sort(key=lambda c: datetime.fromisoformat(c.timestamp))

            # 3. Cache 파일 저장
            self.chart_cache_service._save_to_cache(stock_code, target_date, cached_candles)

            logger.info(f"Cache 업데이트 완료: {stock_code}, {target_date.strftime('%Y-%m-%d')}")

            return True

        except Exception as e:
            logger.error(f"분봉 업데이트 실패: {stock_code}, 오류: {e}")
            return False

    def _load_settings(self):
        """설정 파일에서 매매 조건 로드"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "trading_conditions" in data:
                        # dict를 Pydantic 모델로 변환
                        self.trading_conditions = TradingConditions(**data["trading_conditions"])
                        logger.info("매매 설정을 파일에서 로드했습니다.")
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {str(e)}")
        
        # 기본 설정 적용
        if not self.trading_conditions:
            self.trading_conditions = TradingConditions()
    
    def _save_settings(self):
        """설정을 파일에 저장"""
        try:
            data = {
                "trading_conditions": self.trading_conditions.dict() if self.trading_conditions else None,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {str(e)}")
    
    async def get_trading_conditions(self) -> TradingConditions:
        """현재 매매 조건 조회"""
        return self.trading_conditions
    
    async def update_trading_conditions(self, conditions: TradingConditions):
        """매매 조건 업데이트"""
        try:
            self.trading_conditions = conditions
            self._save_settings()
            logger.info("매매 조건이 업데이트되었습니다.")
            
        except Exception as e:
            logger.error(f"매매 조건 업데이트 실패: {str(e)}")
            raise
    
    async def start_trading(self) -> Dict[str, Any]:
        """자동매매 시작"""
        try:
            if self.is_trading_active:
                return {
                    "success": False,
                    "message": "자동매매가 이미 실행 중입니다."
                }
            
            if not self.trading_conditions:
                return {
                    "success": False,
                    "message": "매매 조건이 설정되지 않았습니다."
                }
            
            # 연결 상태 확인
            status = self.korea_invest_service.get_connection_status()
            if not status["connected"]:
                return {
                    "success": False,
                    "message": "한국투자증권 API가 연결되지 않았습니다."
                }
            
            self.is_trading_active = True
            self.trading_start_time = datetime.now()
            
            logger.info("자동매매가 시작되었습니다.")
            
            return {
                "success": True,
                "message": "자동매매가 시작되었습니다.",
                "start_time": self.trading_start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"자동매매 시작 실패: {str(e)}")
            return {
                "success": False,
                "message": f"자동매매 시작 실패: {str(e)}"
            }
    
    async def stop_trading(self) -> Dict[str, Any]:
        """자동매매 중지"""
        try:
            if not self.is_trading_active:
                return {
                    "success": False,
                    "message": "자동매매가 실행되지 않고 있습니다."
                }
            
            self.is_trading_active = False
            
            logger.info("자동매매가 중지되었습니다.")
            
            return {
                "success": True,
                "message": "자동매매가 중지되었습니다."
            }
            
        except Exception as e:
            logger.error(f"자동매매 중지 실패: {str(e)}")
            return {
                "success": False,
                "message": f"자동매매 중지 실패: {str(e)}"
            }
    
    async def get_trading_status(self) -> Dict[str, Any]:
        """매매 상태 조회"""
        return {
            "is_running": self.is_trading_active,
            "start_time": self.trading_start_time.isoformat() if self.trading_start_time else None,
            "total_trades": self.trading_stats["total_trades"],
            "profit_trades": self.trading_stats["profit_trades"],
            "loss_trades": self.trading_stats["loss_trades"],
            "auto_trading_enabled": self.trading_conditions.auto_trading_enabled if self.trading_conditions else False
        }
    
    async def check_buy_conditions(self, stock_code: str, analysis_result: Dict[str, Any]) -> bool:
        """
        매수 조건 체크
        PyQt5의 매수 조건 체크 로직과 동일
        """
        try:
            if not self.trading_conditions.buy_conditions.enabled:
                return False
            
            # 기술적 지표 기반 매매 신호 체크
            signals = TechnicalAnalysisService.get_trading_signals(
                analysis_result,
                self.trading_conditions.buy_conditions.dict(),
                self.trading_conditions.sell_conditions.dict()
            )
            
            return signals.get('buy_signal', False)
            
        except Exception as e:
            logger.error(f"매수 조건 체크 실패 ({stock_code}): {str(e)}")
            return False
    
    async def check_sell_conditions(self, stock_code: str, analysis_result: Dict[str, Any], 
                                  current_item: WatchlistItem) -> bool:
        """
        매도 조건 체크
        PyQt5의 매도 조건 체크 로직과 동일
        """
        try:
            if not self.trading_conditions.sell_conditions.enabled:
                return False
            
            # 기술적 지표 기반 매매 신호 체크
            signals = TechnicalAnalysisService.get_trading_signals(
                analysis_result,
                self.trading_conditions.buy_conditions.dict(),
                self.trading_conditions.sell_conditions.dict()
            )
            
            # 기술적 지표 조건
            tech_signal = signals.get('sell_signal', False)
            
            # 수익률 조건 체크
            profit_condition = self._check_profit_conditions(current_item)
            
            # 트레일링스탑 조건 체크
            trailing_stop_condition = self._check_trailing_stop(current_item)
            
            return tech_signal or profit_condition or trailing_stop_condition
            
        except Exception as e:
            logger.error(f"매도 조건 체크 실패 ({stock_code}): {str(e)}")
            return False
    
    def _check_profit_conditions(self, item: WatchlistItem) -> bool:
        """수익률 기반 매도 조건 체크"""
        try:
            # 목표 수익률 달성
            if (self.trading_conditions.sell_conditions.profit_target and 
                item.profit_rate and 
                item.profit_rate >= self.trading_conditions.sell_conditions.profit_target):
                logger.info(f"목표 수익률 달성: {item.profit_rate}% >= {self.trading_conditions.sell_conditions.profit_target}%")
                return True
            
            # 손절매 조건
            if (self.trading_conditions.sell_conditions.stop_loss and 
                item.profit_rate and 
                item.profit_rate <= -self.trading_conditions.sell_conditions.stop_loss):
                logger.info(f"손절매 조건: {item.profit_rate}% <= -{self.trading_conditions.sell_conditions.stop_loss}%")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"수익률 조건 체크 실패: {str(e)}")
            return False
    
    def _check_trailing_stop(self, item: WatchlistItem) -> bool:
        """트레일링스탑 조건 체크"""
        try:
            if not self.trading_conditions.trailing_stop.enabled:
                return False
            
            # 트레일링스탑 발동 조건 (수익률 기준)
            if (not item.trailing_stop_active and 
                item.profit_rate and 
                item.profit_rate >= self.trading_conditions.trailing_stop.activation_rate):
                
                # 트레일링스탑 발동
                logger.info(f"트레일링스탑 발동: 수익률 {item.profit_rate}%")
                return False  # 발동만 하고 매도하지는 않음
            
            # 트레일링스탑 매도 조건
            if (item.trailing_stop_active and 
                item.trailing_stop_high and 
                item.current_price):
                
                # 고점 대비 하락률 계산
                drop_rate = (item.trailing_stop_high - item.current_price) / item.trailing_stop_high * 100
                
                if drop_rate >= self.trading_conditions.trailing_stop.trailing_rate:
                    logger.info(f"트레일링스탑 매도 조건: 고점 대비 {drop_rate}% 하락")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"트레일링스탑 조건 체크 실패: {str(e)}")
            return False
    
    async def execute_buy_order(self, stock_code: str, analysis_result: Dict[str, Any]) -> TradeExecutionResult:
        """
        매수 주문 실행
        PyQt5의 매수 로직과 동일
        """
        try:
            # 매수 조건 재확인
            if not await self.check_buy_conditions(stock_code, analysis_result):
                return TradeExecutionResult(
                    success=False,
                    message="매수 조건이 충족되지 않음"
                )
            
            # 매수 금액 계산
            buy_amount = self.trading_conditions.buy_conditions.amount
            current_price = analysis_result.get('current_price', 0)
            
            if current_price <= 0:
                return TradeExecutionResult(
                    success=False,
                    message="유효하지 않은 현재가"
                )
            
            # 주문 수량 계산
            quantity = int(buy_amount / current_price)
            
            if quantity <= 0:
                return TradeExecutionResult(
                    success=False,
                    message="매수 수량이 0 이하"
                )
            
            # API를 통한 실제 매수 주문 실행
            order_result = await self.korea_invest_service.place_buy_order(
                stock_code=stock_code,
                quantity=quantity,
                price=current_price  # 시장가 주문
            )
            
            if order_result and order_result.get('success'):
                logger.info(f"매수 주문 성공 - 종목: {stock_code}, 수량: {quantity}, 가격: {current_price}")
                
                # 실행 기록 저장
                self._add_order_record("매수", {
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': current_price
                }, order_result)
                
                return TradeExecutionResult(
                    success=True,
                    order_id=order_result.get('order_id'),
                    message=f"매수 주문 성공: {quantity}주 @ {current_price}원"
                )
            else:
                return TradeExecutionResult(
                    success=False,
                    message=f"매수 주문 실패: {order_result.get('message', '알 수 없는 오류')}"
                )
            
        except Exception as e:
            logger.error(f"매수 주문 실행 실패 ({stock_code}): {str(e)}")
            return TradeExecutionResult(
                success=False,
                message=f"매수 주문 실행 실패: {str(e)}"
            )
    
    async def execute_sell_order(self, stock_code: str, item: WatchlistItem) -> TradeExecutionResult:
        """
        매도 주문 실행
        PyQt5의 매도 로직과 동일
        """
        try:
            if item.quantity <= 0:
                return TradeExecutionResult(
                    success=False,
                    message="보유 수량이 0 이하"
                )
            
            # API를 통한 실제 매도 주문 실행
            order_result = await self.korea_invest_service.place_sell_order(
                stock_code=stock_code,
                quantity=item.quantity,
                price=item.current_price  # 시장가 주문
            )
            
            if order_result and order_result.get('success'):
                logger.info(f"매도 주문 성공 - 종목: {stock_code}, 수량: {item.quantity}, 가격: {item.current_price}")
                
                # 실행 기록 저장
                self._add_order_record("매도", {
                    'stock_code': stock_code,
                    'quantity': item.quantity,
                    'price': item.current_price,
                    'profit_rate': item.profit_rate
                }, order_result)
                
                return TradeExecutionResult(
                    success=True,
                    order_id=order_result.get('order_id'),
                    message=f"매도 주문 성공: {item.quantity}주 @ {item.current_price}원 (수익률: {item.profit_rate}%)"
                )
            else:
                return TradeExecutionResult(
                    success=False,
                    message=f"매도 주문 실패: {order_result.get('message', '알 수 없는 오류')}"
                )
            
        except Exception as e:
            logger.error(f"매도 주문 실행 실패 ({stock_code}): {str(e)}")
            return TradeExecutionResult(
                success=False,
                message=f"매도 주문 실행 실패: {str(e)}"
            )
    
    def _add_order_record(self, order_type: str, order: Dict[str, Any], result: Dict[str, Any]):
        """주문 기록 추가"""
        try:
            record = {
                "order_type": order_type,
                "stock_code": order.get('stock_code'),
                "quantity": order.get('quantity'),
                "price": order.get('price'),
                "profit_rate": order.get('profit_rate'),
                "order_time": datetime.now().isoformat(),
                "result": result
            }
            
            self.order_history.append(record)
            self.trading_stats["total_trades"] += 1
            
            # 메모리 관리를 위해 최근 1000개만 유지
            if len(self.order_history) > 1000:
                self.order_history = self.order_history[-1000:]
                
        except Exception as e:
            logger.error(f"주문 기록 추가 실패: {str(e)}")
    
    async def get_order_history(self, limit: int = 50) -> List[OrderHistory]:
        """주문 내역 조회"""
        try:
            # 최근 주문 내역 반환
            recent_orders = self.order_history[-limit:] if limit > 0 else self.order_history
            
            history = []
            for record in reversed(recent_orders):  # 최신 순으로 정렬
                order_history = OrderHistory(
                    order_id=record.get("result", {}).get("data", {}).get("order_id", "N/A"),
                    stock_code=record["stock_code"],
                    stock_name="",  # 실제로는 종목명 조회 필요
                    order_type=record["order_type"],
                    quantity=record["quantity"],
                    price=record["price"],
                    executed_quantity=0,  # 실제 체결 정보 필요
                    executed_price=0,     # 실제 체결 정보 필요
                    status="접수",         # 실제 주문 상태 확인 필요
                    order_time=datetime.fromisoformat(record["order_time"])
                )
                history.append(order_history)
            
            return history
            
        except Exception as e:
            logger.error(f"주문 내역 조회 실패: {str(e)}")
            return []
    
    async def get_pending_orders(self) -> List[OrderHistory]:
        """미체결 주문 조회"""
        try:
            # 실제로는 한국투자증권 API에서 미체결 주문을 조회해야 함
            # 여기서는 기본 구조만 제공
            return []
            
        except Exception as e:
            logger.error(f"미체결 주문 조회 실패: {str(e)}")
            return []
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """주문 취소"""
        try:
            # 실제로는 한국투자증권 API에서 주문을 취소해야 함
            # 여기서는 기본 구조만 제공
            return {
                "success": False,
                "message": "주문 취소 기능이 구현되지 않았습니다."
            }
            
        except Exception as e:
            logger.error(f"주문 취소 실패: {str(e)}")
            return {
                "success": False,
                "message": f"주문 취소 실패: {str(e)}"
            }
    
    async def get_trading_performance(self, days: int = 30) -> Dict[str, Any]:
        """매매 성과 조회"""
        try:
            # 지정된 기간의 거래 내역 분석
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_trades = [
                record for record in self.order_history
                if datetime.fromisoformat(record["order_time"]) >= cutoff_date
            ]
            
            total_trades = len(recent_trades)
            buy_trades = len([t for t in recent_trades if t["order_type"] == "매수"])
            sell_trades = len([t for t in recent_trades if t["order_type"] == "매도"])
            
            return {
                "period_days": days,
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "profit_trades": self.trading_stats["profit_trades"],
                "loss_trades": self.trading_stats["loss_trades"],
                "total_profit_loss": self.trading_stats["total_profit_loss"],
                "win_rate": (self.trading_stats["profit_trades"] / max(1, total_trades)) * 100,
                "is_trading_active": self.is_trading_active,
                "trading_start_time": self.trading_start_time.isoformat() if self.trading_start_time else None
            }
            
        except Exception as e:
            logger.error(f"매매 성과 조회 실패: {str(e)}")
            return {
                "error": f"매매 성과 조회 실패: {str(e)}"
            }

    async def get_minute_chart_data_range(
        self,
        stock_code: str,
        end_date: Optional[datetime] = None,
        max_days: int = 10
    ) -> Dict[str, List[ChartCandle]]:
        """
        날짜 범위의 분봉 데이터 조회 (과거 여러 날짜)

        Args:
            stock_code: 종목 코드
            end_date: 종료 날짜 (None이면 오늘, 이 날짜 포함)
            max_days: 조회할 최대 일수 (end_date로부터 이전 N-1개 거래일 + end_date)

        Returns:
            날짜별 분봉 데이터 딕셔너리
            {
                "20251006": [ChartCandle 360개],
                "20251003": [ChartCandle 360개],
                ...
            }

        Example:
            >>> # 월요일(10/6)로부터 과거 3일치 (월/금/목/수)
            >>> data = await service.get_minute_chart_data_range("005930", datetime(2025, 10, 6), 4)
            >>> assert len(data) == 4
            >>> assert "20251006" in data  # 월요일
            >>> assert "20251003" in data  # 금요일
        """
        from app.utils.trading_calendar import TradingCalendar

        # 종료일 설정
        target_end_date = end_date if end_date else datetime.now()

        logger.info(f"📅 범위 분봉 조회: {stock_code}, 종료={target_end_date.strftime('%Y-%m-%d')}, 일수={max_days}")

        # 1. 종료일 포함 + 이전 N-1개 거래일 계산
        trading_days = []

        # 종료일이 거래일이면 포함
        calendar = get_default_calendar()
        if calendar.is_trading_day(target_end_date):
            trading_days.append(target_end_date)

        # 이전 거래일들 추가
        previous_days = calendar.get_previous_trading_days(target_end_date, max_days - 1)
        trading_days.extend(previous_days)

        logger.info(f"   거래일 {len(trading_days)}개: {[d.strftime('%Y-%m-%d') for d in trading_days]}")

        # 2. 각 날짜별로 분봉 데이터 조회
        result = {}

        for trade_date in trading_days:
            date_str = trade_date.strftime("%Y%m%d")

            try:
                # get_minute_chart_data는 캐시 우선 전략 사용
                candles = await self.get_minute_chart_data(
                    stock_code=stock_code,
                    target_date=trade_date,
                    regular_hours_only=True
                )

                if candles:
                    result[date_str] = candles
                    logger.info(f"   ✅ {date_str}: {len(candles)}개")
                else:
                    logger.warning(f"   ⚠️ {date_str}: 데이터 없음")

            except Exception as e:
                logger.error(f"   ❌ {date_str} 조회 실패: {e}")
                continue

        logger.info(f"✅ 범위 조회 완료: {len(result)}일치 데이터")
        return result
