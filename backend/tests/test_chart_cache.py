"""
차트 캐시 서비스 테스트
Phase 1 백엔드 구현 검증
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.chart_cache_service import ChartCacheService
from app.utils.trading_calendar import get_default_calendar
from app.models.schemas import ChartCandle


async def test_cache_service():
    """ChartCacheService 기본 기능 테스트"""
    print("\n" + "="*60)
    print("Phase 1 테스트: ChartCacheService 검증")
    print("="*60)

    # 1. 서비스 초기화
    print("\n[1] ChartCacheService 초기화...")
    cache_service = ChartCacheService(cache_dir="test_kordata")
    print(f"✓ 캐시 디렉토리 생성 확인: {cache_service.cache_dir}")

    # 2. 테스트 데이터 생성
    print("\n[2] 테스트 캔들 데이터 생성...")
    test_stock_code = "005930"  # 삼성전자
    test_date = datetime(2025, 9, 30, 9, 0, 0)

    test_candles = [
        ChartCandle(
            timestamp=(test_date + timedelta(minutes=i)).isoformat(),
            open=83000 + i * 10,
            high=83100 + i * 10,
            low=82900 + i * 10,
            close=83050 + i * 10,
            volume=1000 + i * 100
        )
        for i in range(10)
    ]
    print(f"✓ {len(test_candles)}개 테스트 캔들 생성")

    # 3. 캐시에 저장
    print("\n[3] 캐시에 데이터 저장...")
    cache_service._save_to_cache(test_stock_code, test_date, test_candles)
    cache_file = cache_service._get_cache_file_path(test_stock_code, test_date)
    print(f"✓ 캐시 파일 생성: {cache_file}")
    print(f"✓ 파일 존재 확인: {cache_file.exists()}")

    # 4. 캐시에서 로드
    print("\n[4] 캐시에서 데이터 로드...")
    loaded_candles = cache_service._load_from_cache(test_stock_code, test_date)
    if loaded_candles:
        print(f"✓ {len(loaded_candles)}개 캔들 로드 성공")
        print(f"  - 첫 번째 캔들: {loaded_candles[0].timestamp}, 종가: {loaded_candles[0].close}")
        print(f"  - 마지막 캔들: {loaded_candles[-1].timestamp}, 종가: {loaded_candles[-1].close}")
    else:
        print("✗ 캐시 로드 실패")

    # 5. 캐시 통계
    print("\n[5] 캐시 통계 조회...")
    stats = cache_service.get_cache_stats(test_stock_code)
    print(f"✓ 캐시 통계:")
    print(f"  - 종목코드: {stats['stock_code']}")
    print(f"  - 캐시된 날짜 수: {stats['cached_days']}일")
    print(f"  - 총 크기: {stats['total_size_kb']} KB")
    print(f"  - 파일 목록: {stats['files']}")

    # 6. Mock API fallback 테스트
    print("\n[6] API fallback 함수 테스트...")

    # Mock KoreaInvestAPIService
    class MockKoreaInvestService:
        async def get_minute_chart_data(self, stock_code: str, **kwargs):
            """Mock API - 새로운 데이터 반환"""
            print(f"  - Mock API 호출: {stock_code}")
            return [
                ChartCandle(
                    timestamp=(datetime.now() + timedelta(minutes=i)).isoformat(),
                    open=84000,
                    high=84100,
                    low=83900,
                    close=84050,
                    volume=2000
                )
                for i in range(5)
            ]

    mock_korea_invest_service = MockKoreaInvestService()

    # 캐시 미스 테스트 (존재하지 않는 날짜)
    future_date = datetime(2025, 10, 15)
    print(f"  - 캐시 미스 시나리오: {future_date.strftime('%Y-%m-%d')}")
    result = await cache_service.get_minute_candles(
        stock_code=test_stock_code,
        target_date=future_date,
        korea_invest_service=mock_korea_invest_service
    )

    if result:
        print(f"✓ API fallback 성공: {len(result)}개 캔들")
    else:
        print("✗ API fallback 실패")

    # 7. 캐시 삭제
    print("\n[7] 캐시 무효화 테스트...")
    cache_service.invalidate_cache(test_stock_code, test_date)
    print(f"✓ 특정 날짜 캐시 삭제")
    print(f"✓ 파일 존재 확인: {cache_file.exists()}")

    # 정리
    print("\n[8] 테스트 데이터 정리...")
    cache_service.invalidate_cache(test_stock_code)
    if cache_service.cache_dir.exists():
        try:
            cache_service.cache_dir.rmdir()
            print("✓ 테스트 캐시 디렉토리 삭제")
        except:
            print("⚠ 테스트 캐시 디렉토리 삭제 실패 (파일이 남아있을 수 있음)")

    print("\n" + "="*60)
    print("Phase 1 테스트 완료")
    print("="*60)


def test_trading_calendar():
    """TradingCalendar 유틸리티 테스트"""
    print("\n" + "="*60)
    print("Phase 1 테스트: TradingCalendar 검증")
    print("="*60)

    calendar = get_default_calendar()

    # 1. 거래일 확인
    print("\n[1] 거래일 판별 테스트...")
    test_cases = [
        datetime(2025, 9, 30),  # 화요일 (거래일)
        datetime(2025, 10, 1),  # 수요일 (거래일)
        datetime(2025, 10, 4),  # 토요일 (주말)
        datetime(2025, 10, 5),  # 일요일 (주말)
        datetime(2025, 10, 3),  # 금요일 개천절 (공휴일)
        datetime(2025, 1, 1),   # 신정 (공휴일)
    ]

    for date in test_cases:
        is_trading = calendar.is_trading_day(date)
        is_holiday = date.weekday() < 5 and not is_trading
        weekday = ["월", "화", "수", "목", "금", "토", "일"][date.weekday()]
        status = "거래일" if is_trading else ("공휴일" if is_holiday else "주말")
        print(f"  {date.strftime('%Y-%m-%d')} ({weekday}): {status}")

    # 2. 이전 거래일 조회
    print("\n[2] 이전 거래일 조회 테스트...")
    current_date = datetime(2025, 10, 6)  # 월요일 (개천절 다음날)
    prev_trading = calendar.get_previous_trading_day(current_date)
    print(f"  기준일: {current_date.strftime('%Y-%m-%d')}")
    print(f"  이전 거래일: {prev_trading.strftime('%Y-%m-%d')}")

    # 연휴 테스트 (추석)
    chuseok = datetime(2025, 10, 6)  # 추석
    prev_trading = calendar.get_previous_trading_day(chuseok)
    print(f"\n  추석 연휴 테스트:")
    print(f"  기준일: {chuseok.strftime('%Y-%m-%d')}")
    print(f"  이전 거래일: {prev_trading.strftime('%Y-%m-%d')}")

    # 3. 다음 거래일 조회
    print("\n[3] 다음 거래일 조회 테스트...")
    friday = datetime(2025, 10, 10)  # 금요일
    next_trading = calendar.get_next_trading_day(friday)
    print(f"  금요일: {friday.strftime('%Y-%m-%d')}")
    print(f"  다음 거래일: {next_trading.strftime('%Y-%m-%d')}")

    # 4. 거래일 수 계산
    print("\n[4] 거래일 수 계산 테스트...")
    start = datetime(2025, 10, 1)
    end = datetime(2025, 10, 31)
    trading_days_list = calendar.get_trading_days(start, end)
    trading_days_count = len(trading_days_list)
    print(f"  기간: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}")
    print(f"  거래일 수: {trading_days_count}일")

    print("\n" + "="*60)
    print("Phase 1 테스트 완료")
    print("="*60)


if __name__ == "__main__":
    # TradingCalendar 테스트 (동기)
    test_trading_calendar()

    # ChartCacheService 테스트 (비동기)
    asyncio.run(test_cache_service())

    print("\n✓ 모든 Phase 1 테스트 완료!")