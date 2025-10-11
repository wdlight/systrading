"""
차트 데이터 로컬 캐싱 서비스
분봉 데이터를 로컬 파일에 저장하여 빠른 조회 및 무한 스크롤 지원
"""

import json
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.models.schemas import ChartCandle

# KST = UTC+9
KST = timezone(timedelta(hours=9))
from app.utils.trading_calendar import get_default_calendar
from loguru import logger


class ChartCacheService:
    """차트 데이터 로컬 파일 캐시 서비스"""

    def __init__(self, cache_dir: str = "kordata"):
        """
        Args:
            cache_dir: 캐시 디렉토리 경로 (기본값: kordata)
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """캐시 디렉토리 생성"""
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"캐시 디렉토리 생성: {self.cache_dir}")

    def _get_cache_file_path(self, stock_code: str, date: datetime) -> Path:
        """
        캐시 파일 경로 생성

        Args:
            stock_code: 종목코드 (예: "005930")
            date: 날짜

        Returns:
            Path: kordata/{종목코드}/{YYYYMMDD}.json
        """
        stock_dir = self.cache_dir / stock_code
        stock_dir.mkdir(parents=True, exist_ok=True)

        date_str = date.strftime("%Y%m%d")
        return stock_dir / f"{date_str}.json"

    def _load_from_cache(self, stock_code: str, date: datetime) -> Optional[List[ChartCandle]]:
        """
        캐시에서 데이터 로드

        Args:
            stock_code: 종목코드
            date: 날짜

        Returns:
            Optional[List[ChartCandle]]: 캐시된 데이터 또는 None
        """
        cache_file = self._get_cache_file_path(stock_code, date)

        if not cache_file.exists():
            logger.debug(f"캐시 파일 없음: {cache_file}")
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # JSON을 ChartCandle 객체로 변환
            candles = [ChartCandle(**item) for item in data]
            logger.info(f"캐시에서 로드 성공: {cache_file}, {len(candles)}개 캔들")
            return candles

        except Exception as e:
            logger.error(f"캐시 로드 실패: {cache_file}, 오류: {e}")
            return None

    async def _sanitize_cached_candles_for_date(
        self,
        cached_candles: List[ChartCandle],
        stock_code: str,
        target_date: datetime,
        korea_invest_service,
        skip_cache_save: bool = False
    ) -> List[ChartCandle]:
        """Filter cache to the target date and refill when the date is missing."""
        if not cached_candles:
            return []

        target_date_str = target_date.strftime("%Y-%m-%d")
        same_day, others = self._partition_candles_by_date(cached_candles, target_date_str)

        if others:
            summary = ", ".join(
                f"{date}({len(items)}개)" for date, items in others.items()
            )
            logger.warning(
                f"캐시에 다른 날짜 데이터 포함: {stock_code}, target={target_date_str} → {summary}"
            )

        if same_day:
            if others and not skip_cache_save:
                self._save_to_cache(stock_code, target_date, same_day)
            return same_day

        if others:
            logger.warning(
                f"캐시에 대상 날짜({target_date_str}) 데이터가 없어 전체 재조회 시도: {stock_code}"
            )
            refetched = await self._fetch_full_day_candles(
                stock_code=stock_code,
                target_date=target_date,
                korea_invest_service=korea_invest_service
            )

            if refetched and not skip_cache_save:
                self._save_to_cache(stock_code, target_date, refetched)

            return refetched

        return []

    def _partition_candles_by_date(
        self,
        candles: List[ChartCandle],
        target_date_str: str
    ) -> Tuple[List[ChartCandle], Dict[str, List[ChartCandle]]]:
        """Split candles into target date entries and grouped extras."""
        same_day: List[ChartCandle] = []
        others: Dict[str, List[ChartCandle]] = {}

        for candle in candles:
            candle_date = candle.timestamp[:10]
            if candle_date == target_date_str:
                same_day.append(candle)
            else:
                others.setdefault(candle_date, []).append(candle)

        return same_day, others

    async def _fetch_full_day_candles(
        self,
        stock_code: str,
        target_date: datetime,
        korea_invest_service
    ) -> List[ChartCandle]:
        """Retrieve the entire minute series for the specified date."""
        target_date_str = target_date.strftime("%Y-%m-%d")
        is_today = target_date.date() == datetime.now().date()

        try:
            if is_today:
                logger.info(f"전체 재조회(당일): {stock_code}, {target_date_str}")
                candles = await korea_invest_service.get_minute_chart_data(stock_code) or []
            else:
                logger.info(f"전체 재조회(과거): {stock_code}, {target_date_str}")
                df = await korea_invest_service.get_daily_minute_chart_data(stock_code, target_date)
                if df is None or (hasattr(df, 'empty') and df.empty):
                    return []
                candles = self._convert_df_to_candles(df, target_date)
        except Exception as e:
            logger.error(f"전체 분봉 재조회 실패: {stock_code}, {target_date_str}, 오류: {e}")
            return []

        filtered, _ = self._partition_candles_by_date(candles, target_date_str)
        return filtered

    def _save_to_cache(self, stock_code: str, date: datetime, candles: List[ChartCandle]):
        """
        캐시에 데이터 저장

        Args:
            stock_code: 종목코드
            date: 날짜
            candles: 캔들 데이터 리스트
        """
        if not candles:
            logger.warning(f"저장할 캔들 데이터가 없음: {stock_code}, {date}")
            return

        cache_file = self._get_cache_file_path(stock_code, date)

        try:
            # ChartCandle 객체를 dict로 변환
            data = [candle.model_dump() for candle in candles]

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"캐시 저장 성공: {cache_file}, {len(candles)}개 캔들")

        except Exception as e:
            logger.error(f"캐시 저장 실패: {cache_file}, 오류: {e}")

    def _needs_gap_fill(
        self,
        cached_candles: List[ChartCandle],
        target_date: datetime
    ) -> bool:
        """
        Gap fill이 필요한지 판단

        Args:
            cached_candles: 캐시된 캔들 데이터
            target_date: 조회 대상 날짜

        Returns:
            Gap fill 필요 여부
        """
        # 오늘 날짜가 아니면 gap-fill 불필요
        if target_date.date() != datetime.now().date():
            return False

        # 거래시간 체크를 위한 현재 시간
        now = datetime.now()

        # 장 시작 전이면 gap-fill 불필요
        from app.utils.trading_hours import TradingHoursManager
        if not TradingHoursManager.is_trading_hours(now):
            # 장 종료 후에도 gap이 있을 수 있으므로 체크
            # 15:30 이후라면 gap-fill 시도
            if now.hour < 15 or (now.hour == 15 and now.minute < 30):
                return False

        # Cache의 마지막 캔들 시간 확인
        try:
            latest_cached = max(
                cached_candles,
                key=lambda c: datetime.fromisoformat(c.timestamp)
            )
            latest_time = datetime.fromisoformat(latest_cached.timestamp)
        except (ValueError, AttributeError) as e:
            logger.error(f"캔들 timestamp 파싱 실패: {e}")
            return False

        # 2분 이상 차이나면 gap 존재
        gap_seconds = (now - latest_time).total_seconds()
        gap_minutes = gap_seconds / 60

        if gap_minutes >= 2:
            logger.info(
                f"Gap detected: latest={latest_time.strftime('%H:%M')}, "
                f"now={now.strftime('%H:%M')}, gap={gap_minutes:.1f}분"
            )
            return True

        return False

    async def _fill_gap(
        self,
        cached_candles: List[ChartCandle],
        stock_code: str,
        korea_invest_service,
        target_date: datetime  # ✅ 추가: 대상 날짜
    ) -> List[ChartCandle]:
        """
        Cache gap을 API로 채움 (최적화: Gap 구간만 조회)

        Args:
            cached_candles: 기존 cache 데이터
            stock_code: 종목 코드
            korea_invest_service: KoreaInvestAPIService 인스턴스
            target_date: 대상 날짜 (datetime)

        Returns:
            Gap이 채워진 완전한 데이터
        """
        target_date_str = target_date.strftime("%Y-%m-%d")
        base_candles, extras = self._partition_candles_by_date(cached_candles, target_date_str)

        if extras:
            summary = ", ".join(
                f"{date}({len(items)}개)" for date, items in extras.items()
            )
            logger.warning(
                f"Gap fill 이전 캐시에 다른 날짜 데이터 발견: {stock_code} → {summary}. 대상 날짜만 사용합니다."
            )

        if not base_candles:
            logger.warning(
                f"Gap fill을 위한 대상 날짜 데이터가 없어 전체 재조회 시도: {stock_code}, {target_date_str}"
            )
            base_candles = await self._fetch_full_day_candles(
                stock_code=stock_code,
                target_date=target_date,
                korea_invest_service=korea_invest_service
            )
            if not base_candles:
                logger.error(
                    f"Gap fill 실패: {stock_code}, {target_date_str} 대상 데이터 확보 불가"
                )
                return []

        # 1. Cache의 마지막 시간
        try:
            latest_cached = max(
                base_candles,
                key=lambda c: datetime.fromisoformat(c.timestamp)
            )
            gap_start_time = datetime.fromisoformat(latest_cached.timestamp)
        except (ValueError, AttributeError) as e:
            logger.error(f"캔들 timestamp 파싱 실패: {e}")
            return base_candles

        # 2. Gap 시작 시간 계산 (마지막 캔들 + 1분)
        gap_start = gap_start_time + timedelta(minutes=1)
        gap_start_hhmmss = gap_start.strftime("%H%M%S")

        logger.info(
            f"Gap 구간만 조회: {stock_code}, {target_date.strftime('%Y-%m-%d')} "
            f"{gap_start.strftime('%H:%M')}~현재 (start_time={gap_start_hhmmss})"
        )

        # 3. ✨ Gap 구간만 API 호출 (최적화) - ✅ target_date 전달
        gap_candles = await korea_invest_service.get_minute_chart_data_from(
            stock_code=stock_code,
            start_time=gap_start_hhmmss,
            target_date=target_date  # ✅ 추가: 날짜 지정
        )

        if not gap_candles:
            logger.warning(f"Gap 데이터 없음: {stock_code}, {gap_start_hhmmss}~")
            return base_candles

        valid_gap_candles: List[ChartCandle] = []
        discarded_counts = {}

        for candle in gap_candles:
            candle_date = candle.timestamp[:10]
            if candle_date == target_date_str:
                valid_gap_candles.append(candle)
            else:
                discarded_counts[candle_date] = discarded_counts.get(candle_date, 0) + 1

        if discarded_counts:
            extra_summary = ", ".join(f"{date}({count}개)" for date, count in discarded_counts.items())
            logger.info(f"Gap 데이터에서 다른 날짜 발견: {stock_code} → {extra_summary}")

        if not valid_gap_candles:
            # 다른 날짜 데이터만 반환된 경우 기존 캐시 유지
            logger.warning(
                f"유효한 Gap 데이터 없음: {stock_code}, target={target_date_str}. 기존 캐시를 유지합니다."
            )
            return base_candles

        logger.info(
            f"Gap 채우기: {len(valid_gap_candles)}개 추가 "
            f"({gap_start_hhmmss}~현재)"
        )

        # 4. 병합 및 중복 제거 (timestamp를 key로 사용)
        all_candles = base_candles + valid_gap_candles
        unique_map = {candle.timestamp: candle for candle in all_candles}

        # 5. 시간순 정렬
        sorted_candles = [
            candle
            for candle in sorted(
                unique_map.values(),
                key=lambda c: datetime.fromisoformat(c.timestamp)
            )
            if candle.timestamp[:10] == target_date_str
        ]

        logger.info(
            f"Gap fill 완료: {len(base_candles)}개 → {len(sorted_candles)}개 "
            f"(+{len(sorted_candles) - len(base_candles)}개)"
        )

        return sorted_candles

    async def get_minute_candles(
        self,
        stock_code: str,
        target_date: datetime,
        korea_invest_service,  # ✅ 직접 service 전달
        skip_cache_save: bool = False
    ) -> Optional[List[ChartCandle]]:
        """
        분봉 데이터 조회 (캐시 우선, gap-fill 최적화)

        Args:
            stock_code: 종목코드
            target_date: 조회할 날짜
            korea_invest_service: KoreaInvestAPIService 인스턴스
            skip_cache_save: True면 API 호출 후 캐시 저장 생략 (기본값: False)

        Returns:
            Optional[List[ChartCandle]]: 캔들 데이터 리스트
        """
        # 1. 캐시에서 조회 시도
        cached_data = self._load_from_cache(stock_code, target_date)
        if cached_data:
            cached_data = await self._sanitize_cached_candles_for_date(
                cached_candles=cached_data,
                stock_code=stock_code,
                target_date=target_date,
                korea_invest_service=korea_invest_service,
                skip_cache_save=skip_cache_save
            )
        
        # 2. Gap 감지 및 채우기 (최적화)
        if cached_data and self._needs_gap_fill(cached_data, target_date):
            logger.info(f"Gap 감지, 구간만 조회: {stock_code}, {target_date.strftime('%Y-%m-%d')}")

            try:
                # ✅ Gap 구간만 조회 (전체 조회 X) - target_date 전달
                filled_data = await self._fill_gap(
                    cached_candles=cached_data,
                    stock_code=stock_code,
                    korea_invest_service=korea_invest_service,
                    target_date=target_date  # ✅ 추가
                )
                
                # 캐시 저장
                if not skip_cache_save:
                    self._save_to_cache(stock_code, target_date, filled_data)
                
                return filled_data
            except Exception as e:
                logger.error(f"Gap fill 실패: {stock_code}, 오류: {e}")
                # 오류 발생 시 기존 캐시 반환
                return cached_data
        
        # 3. Cache hit (gap 없음)
        if cached_data:
            return cached_data

        logger.info(f"캐시 미스: {stock_code}, {target_date.strftime('%Y%m%d')}")

        # 4. 거래일이 아닌 경우 이전 거래일 데이터 반환
        calendar = get_default_calendar()
        if not calendar.is_trading_day(target_date):
            logger.info(f"비거래일: {target_date.strftime('%Y%m%d')}, 이전 거래일 조회")
            previous_trading_day = calendar.get_previous_trading_day(target_date)
            return await self.get_minute_candles(stock_code, previous_trading_day, korea_invest_service, skip_cache_save)

        # 5. API 호출하여 데이터 가져오기 (전체 조회)
        try:
            logger.info(f"API 호출 시작 (전체): {stock_code}, {target_date.strftime('%Y%m%d')}")

            # ✅ 수정: 날짜에 따라 올바른 API 메서드 호출
            is_today = target_date.date() == datetime.now().date()
            candles: Optional[List[ChartCandle]] = None

            if is_today:
                # 오늘 데이터: get_minute_chart_data (실시간) -> returns List[ChartCandle]
                logger.info(f"오늘 데이터 조회: {stock_code}")
                candles = await korea_invest_service.get_minute_chart_data(stock_code)
            else:
                # 과거 데이터: get_daily_minute_chart_data (과거 날짜 전용) -> returns DataFrame
                logger.info(f"과거 데이터 조회: {stock_code}, {target_date.strftime('%Y-%m-%d')}")
                df = await korea_invest_service.get_daily_minute_chart_data(stock_code, target_date)
                
                # DataFrame -> List[ChartCandle] 변환
                if df is not None and not df.empty:
                    candles = self._convert_df_to_candles(df, target_date)
                else:
                    candles = []

            if not candles:
                logger.warning(f"API에서 데이터를 받지 못함: {stock_code}, {target_date.strftime('%Y%m%d')}")
                return None

            # 6. 캐시에 저장 (skip_cache_save=True면 생략)
            if not skip_cache_save:
                self._save_to_cache(stock_code, target_date, candles)
            else:
                logger.debug(f"캐시 저장 생략 (skip_cache_save=True): {stock_code}, {target_date.strftime('%Y%m%d')}")

            return candles

        except Exception as e:
            logger.error(f"API 호출 실패: {stock_code}, 오류: {e}", exc_info=True)
            return None

    async def get_historical_minute_candles(
        self,
        stock_code: str,
        target_date: datetime,
        korea_invest_service
    ) -> Optional[List[ChartCandle]]:
        """
        과거 날짜의 분봉 데이터 조회 (영구 캐싱)
        
        Args:
            stock_code: 종목코드
            target_date: 조회 날짜
            korea_invest_service: KoreaInvestAPIService 인스턴스
        
        Returns:
            Optional[List[ChartCandle]]: 과거 날짜의 전체 분봉 데이터
        """
        # 1. 캐시 조회 (과거 데이터는 변경되지 않으므로 영구 캐싱)
        cached_data = self._load_from_cache(stock_code, target_date)
        
        if cached_data:
            logger.info(f"✅ Historical cache hit: {stock_code}, {target_date.strftime('%Y%m%d')}")
            return cached_data
        
        # 2. 비거래일 체크
        calendar = get_default_calendar()
        if not calendar.is_trading_day(target_date):
            logger.info(f"⚠️ 비거래일: {target_date.strftime('%Y%m%d')}, 이전 거래일 조회")
            previous_day = calendar.get_previous_trading_day(target_date)
            return await self.get_historical_minute_candles(
                stock_code, previous_day, korea_invest_service
            )
        
        # 3. 신규 API 호출 (일자별 분봉 데이터)
        logger.info(f"📅 과거 데이터 API 호출: {stock_code}, {target_date.strftime('%Y%m%d')}")
        
        try:
            # 비동기 메서드 호출
            df = await korea_invest_service.get_daily_minute_chart_data(
                stock_code,
                target_date
            )

            if df is None or (hasattr(df, 'empty') and df.empty):
                logger.warning(f"❌ 과거 데이터 없음: {stock_code}, {target_date.strftime('%Y%m%d')}")
                return None
            
            # DataFrame → ChartCandle 변환
            candles = self._convert_df_to_candles(df, target_date)
            
            # 4. 영구 캐싱 (과거 데이터는 변경되지 않음)
            self._save_to_cache(stock_code, target_date, candles)
            logger.info(f"💾 과거 데이터 캐싱 완료: {stock_code}, {target_date.strftime('%Y%m%d')}, {len(candles)}개")
            
            return candles
            
        except Exception as e:
            logger.error(f"❌ 과거 데이터 조회 실패: {stock_code}, {target_date.strftime('%Y%m%d')}, 오류: {e}")
            return None
    
    def _convert_df_to_candles(self, df, target_date: datetime) -> List[ChartCandle]:
        """
        DataFrame을 ChartCandle 리스트로 변환
        
        Args:
            df: pandas DataFrame (['일자', '시간', '시가', '고가', '저가', '종가', '거래량'])
            target_date: 기준 날짜
        
        Returns:
            List[ChartCandle]: 캔들 데이터 리스트
        """
        candles = []
        
        for _, row in df.iterrows():
            try:
                # 시간 파싱 (HHMMSS 형식)
                time_str = str(row['시간']).zfill(6)  # 6자리 맞추기
                hour = int(time_str[0:2])
                minute = int(time_str[2:4])
                second = int(time_str[4:6])
                
                # datetime 생성 (KST timezone 명시)
                timestamp = target_date.replace(
                    hour=hour,
                    minute=minute,
                    second=second,
                    microsecond=0,
                    tzinfo=KST  # ✅ KST timezone 추가
                )

                # ChartCandle 생성
                candle = ChartCandle(
                    timestamp=timestamp.isoformat(),  # ISO 8601: "2025-10-03T09:00:00+09:00"
                    open=float(row['시가']),
                    high=float(row['고가']),
                    low=float(row['저가']),
                    close=float(row['종가']),
                    volume=int(row['거래량'])
                )
                
                candles.append(candle)
                
            except Exception as e:
                logger.warning(f"⚠️ Candle 변환 실패: {row}, 오류: {e}")
                continue
        
        return candles

    def _get_daily_cache_file_path(self, stock_code: str, year: int) -> Path:
        """
        일봉 캐시 파일 경로 생성

        Args:
            stock_code: 종목코드 (예: "005930")
            year: 연도 (YYYY)

        Returns:
            Path: kordata/{종목코드}/daily/{YYYY}.json
        """
        stock_dir = self.cache_dir / stock_code / "daily"
        stock_dir.mkdir(parents=True, exist_ok=True)
        return stock_dir / f"{year}.json"

    def _load_daily_from_cache(self, stock_code: str, year: int) -> Optional[List[ChartCandle]]:
        """일봉 캐시에서 데이터 로드"""
        cache_file = self._get_daily_cache_file_path(stock_code, year)
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            candles = [ChartCandle(**item) for item in data]
            logger.info(f"일봉 캐시에서 로드 성공: {cache_file}, {len(candles)}개 캔들")
            return candles
        except Exception as e:
            logger.error(f"일봉 캐시 로드 실패: {cache_file}, 오류: {e}")
            return None

    def _save_daily_to_cache(self, stock_code: str, year: int, candles: List[ChartCandle]):
        """일봉 캐시에 데이터 저장"""
        if not candles:
            return
        cache_file = self._get_daily_cache_file_path(stock_code, year)
        try:
            data = [candle.model_dump() for candle in candles]
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"일봉 캐시 저장 성공: {cache_file}, {len(candles)}개 캔들")
        except Exception as e:
            logger.error(f"일봉 캐시 저장 실패: {cache_file}, 오류: {e}")

    async def get_daily_candles(
        self,
        stock_code: str,
        start_date: datetime,
        end_date: datetime,
        korea_invest_service
    ) -> Optional[List[ChartCandle]]:
        """
        일봉 데이터 조회 (연도별 캐시 우선)
        """
        all_candles = []
        # 요청된 기간의 모든 연도를 순회
        for year in range(start_date.year, end_date.year + 1):
            cached_candles = self._load_daily_from_cache(stock_code, year)

            if cached_candles:
                all_candles.extend(cached_candles)
                logger.info(f"일봉 캐시 히트: {stock_code}, {year}년")
            else:
                # 캐시 미스: 해당 연도 전체 데이터를 API로 조회
                logger.info(f"일봉 캐시 미스: {stock_code}, {year}년. API 호출")
                api_start_date = f"{year}0101"
                api_end_date = f"{year}1231"
                
                try:
                    year_candles = await korea_invest_service.get_daily_chart_data(
                        stock_code, api_start_date, api_end_date
                    )
                    if year_candles:
                        self._save_daily_to_cache(stock_code, year, year_candles)
                        all_candles.extend(year_candles)
                except Exception as e:
                    logger.error(f"{year}년 일봉 데이터 API 호출 실패: {e}")
                    continue
        
        if not all_candles:
            return None

        # 전체 데이터에서 요청된 기간만큼 필터링
        filtered_candles = [
            candle for candle in all_candles
            if start_date.strftime('%Y-%m-%d') <= candle.timestamp[:10] <= end_date.strftime('%Y-%m-%d')
        ]
        
        # 시간순으로 정렬
        sorted_candles = sorted(filtered_candles, key=lambda c: c.timestamp)
        logger.info(f"최종 일봉 데이터 필터링 및 정렬: {len(sorted_candles)}개")
        
        return sorted_candles

    def invalidate_cache(self, stock_code: str, date: Optional[datetime] = None):
        """
        캐시 무효화 (삭제)

        Args:
            stock_code: 종목코드
            date: 특정 날짜 (None이면 전체 삭제)
        """
        if date:
            # 특정 날짜만 삭제
            cache_file = self._get_cache_file_path(stock_code, date)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"캐시 삭제: {cache_file}")
        else:
            # 종목 전체 캐시 삭제
            stock_dir = self.cache_dir / stock_code
            if stock_dir.exists():
                for cache_file in stock_dir.glob("*.json"):
                    cache_file.unlink()
                stock_dir.rmdir()
                logger.info(f"종목 전체 캐시 삭제: {stock_code}")

    def get_cache_stats(self, stock_code: str) -> dict:
        """
        캐시 통계 조회

        Args:
            stock_code: 종목코드

        Returns:
            dict: 캐시 통계 정보
        """
        stock_dir = self.cache_dir / stock_code

        if not stock_dir.exists():
            return {
                "stock_code": stock_code,
                "cached_days": 0,
                "total_size_kb": 0,
                "files": []
            }

        cache_files = list(stock_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "stock_code": stock_code,
            "cached_days": len(cache_files),
            "total_size_kb": round(total_size / 1024, 2),
            "files": [f.name for f in sorted(cache_files)]
        }
