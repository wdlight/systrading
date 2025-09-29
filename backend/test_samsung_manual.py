#!/usr/bin/env python3
"""
삼성전자 차트 데이터 수동 테스트 스크립트
한국투자증권 API 연결 및 데이터 형식 검증
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from loguru import logger
from app.core.config import get_settings
from app.core.korea_invest import KoreaInvestAPIService
from app.services.stock_service import StockService

# Real API 직접 사용을 위한 import
try:
    from brokers.korea_investment.ki_api import KoreaInvestAPI
    from brokers.korea_investment.ki_env import KoreaInvestEnv
    import yaml
    REAL_API_AVAILABLE = True
except ImportError as e:
    print(f"Real API import failed: {e}")
    REAL_API_AVAILABLE = False

async def test_samsung_chart_data():
    """삼성전자(005930) 차트 데이터 테스트"""
    print("=" * 60)
    print("🔍 삼성전자 차트 데이터 테스트 시작")
    print("=" * 60)

    # Real API 직접 초기화 (simple_server.py 방식 사용)
    real_api = None
    if REAL_API_AVAILABLE:
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                env = KoreaInvestEnv(config)
                base_headers = env.get_base_headers()
                full_config = env.get_full_config()

                real_api = KoreaInvestAPI(full_config, base_headers=base_headers)
                print("✅ Real API 직접 초기화 성공!")
            else:
                print("❌ config.yaml 파일을 찾을 수 없습니다")
                return False
        except Exception as e:
            print(f"❌ Real API 초기화 실패: {e}")
            return False
    else:
        print("❌ Real API 모듈을 import할 수 없습니다")
        return False

    print()

    # 삼성전자 차트 데이터 조회 테스트
    stock_code = "005930"  # 삼성전자
    print(f"📊 삼성전자({stock_code}) 차트 데이터 조회 중...")

    try:
        # 직접 real_api 사용해서 차트 데이터 조회
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        formatted_start_date = start_date.strftime("%Y%m%d")
        formatted_end_date = end_date.strftime("%Y%m%d")

        # 차트 데이터 조회
        chart_df = real_api.get_daily_price_chart(stock_code, formatted_start_date, formatted_end_date, 'D')

        if chart_df is None or chart_df.empty:
            print("❌ 차트 데이터 조회 실패!")
            return False

        print("✅ 차트 데이터 조회 성공!")
        print()

        # DataFrame을 API 응답 형식으로 변환
        chart_data = chart_df.to_dict('records')

        # KIS API 응답 형식에 맞춤
        renamed_data = []
        for item in chart_data:
            renamed_data.append({
                "stck_bsop_date": item.get("일자", ""),
                "stck_oprc": str(item.get("시가", "0")),
                "stck_hgpr": str(item.get("고가", "0")),
                "stck_lwpr": str(item.get("저가", "0")),
                "stck_clpr": str(item.get("종가", "0")),
                "acml_vol": str(item.get("거래량", "0")),
            })

        chart_data = {"output1": {}, "output2": renamed_data}

        # 데이터 구조 확인
        print("📋 응답 데이터 구조:")
        print(f"   - Type: {type(chart_data)}")
        print(f"   - Keys: {list(chart_data.keys()) if isinstance(chart_data, dict) else 'Not a dict'}")
        print()

        # output2 데이터 확인 (실제 차트 데이터)
        if 'output2' in chart_data:
            output2 = chart_data['output2']
            print(f"📈 차트 데이터 (output2):")
            print(f"   - Type: {type(output2)}")
            print(f"   - Length: {len(output2) if output2 else 0}")

            if output2 and len(output2) > 0:
                print(f"   - 첫 번째 데이터:")
                first_item = output2[0]
                for key, value in first_item.items():
                    print(f"     {key}: {value}")
                print()

                print(f"   - 마지막 데이터:")
                last_item = output2[-1]
                for key, value in last_item.items():
                    print(f"     {key}: {value}")
                print()

                # 데이터 형식 검증
                print("🔍 데이터 형식 검증:")
                sample = output2[0]

                # 필수 필드 확인
                required_fields = ["stck_bsop_date", "stck_oprc", "stck_hgpr", "stck_lwpr", "stck_clpr", "acml_vol"]
                for field in required_fields:
                    if field in sample:
                        print(f"   ✅ {field}: {sample[field]} (Type: {type(sample[field])})")
                    else:
                        print(f"   ❌ {field}: Missing!")

                print()

                # 숫자 변환 테스트
                print("🔢 숫자 변환 테스트:")
                try:
                    open_price = int(sample.get("stck_oprc", "0"))
                    high_price = int(sample.get("stck_hgpr", "0"))
                    low_price = int(sample.get("stck_lwpr", "0"))
                    close_price = int(sample.get("stck_clpr", "0"))
                    volume = int(sample.get("acml_vol", "0"))

                    print(f"   ✅ 시가: {open_price:,}")
                    print(f"   ✅ 고가: {high_price:,}")
                    print(f"   ✅ 저가: {low_price:,}")
                    print(f"   ✅ 종가: {close_price:,}")
                    print(f"   ✅ 거래량: {volume:,}")

                    # 데이터 유효성 검증
                    if low_price <= close_price <= high_price and low_price <= open_price <= high_price:
                        print("   ✅ OHLC 데이터 유효성 확인!")
                    else:
                        print("   ⚠️ OHLC 데이터 유효성 문제 발견!")

                except ValueError as e:
                    print(f"   ❌ 숫자 변환 실패: {e}")

            else:
                print("   ❌ 차트 데이터가 비어있습니다!")
        else:
            print("   ❌ output2 키가 없습니다!")

        print()

        # API 엔드포인트 형식으로 변환 테스트
        print("🔄 API 응답 형식 변환 테스트:")
        if chart_data.get('output2'):
            # KoreanStockChart 형식으로 변환
            converted_data = []
            for item in chart_data['output2'][:5]:  # 처음 5개만 테스트
                try:
                    converted_item = {
                        "timestamp": item.get("stck_bsop_date", ""),
                        "open": int(item.get("stck_oprc", "0")),
                        "high": int(item.get("stck_hgpr", "0")),
                        "low": int(item.get("stck_lwpr", "0")),
                        "close": int(item.get("stck_clpr", "0")),
                        "volume": int(item.get("acml_vol", "0")),
                        "tradingValue": int(item.get("stck_clpr", "0")) * int(item.get("acml_vol", "0")),
                        "foreignBuy": 0,  # 임시값
                        "foreignSell": 0,  # 임시값
                        "institutionalBuy": 0,  # 임시값
                        "institutionalSell": 0,  # 임시값
                        "individualBuy": 0,  # 임시값
                        "individualSell": 0   # 임시값
                    }
                    converted_data.append(converted_item)
                    print(f"   ✅ {converted_item['timestamp']}: O={converted_item['open']:,} H={converted_item['high']:,} L={converted_item['low']:,} C={converted_item['close']:,} V={converted_item['volume']:,}")
                except Exception as e:
                    print(f"   ❌ 변환 실패: {e}")

            print(f"   📊 총 {len(converted_data)}개 데이터 변환 성공!")

        print()
        print("=" * 60)
        print("🎉 삼성전자 차트 데이터 테스트 완료!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        logger.error(f"Samsung chart test error: {e}")
        return False

async def test_api_endpoint():
    """API 엔드포인트 직접 테스트"""
    print("\n" + "=" * 60)
    print("🌐 API 엔드포인트 테스트")
    print("=" * 60)

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            url = "http://localhost:8000/api/stocks/005930/chart?period=D"
            print(f"📡 API 호출: {url}")

            response = await client.get(url, timeout=30.0)

            print(f"   - Status Code: {response.status_code}")
            print(f"   - Headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"   - Response Type: {type(data)}")
                print(f"   - Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

                if 'output2' in data and data['output2']:
                    print(f"   ✅ 차트 데이터 {len(data['output2'])}개 수신!")
                else:
                    print("   ⚠️ 차트 데이터가 비어있습니다.")
            else:
                print(f"   ❌ API 호출 실패: {response.text}")

    except httpx.ConnectError:
        print("   ❌ Backend 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"   ❌ API 테스트 실패: {e}")

if __name__ == "__main__":
    print("🚀 삼성전자 차트 데이터 통합 테스트")
    print(f"📅 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 비동기 테스트 실행
    success = asyncio.run(test_samsung_chart_data())

    if success:
        print("\n🔗 API 엔드포인트 테스트도 실행합니다...")
        asyncio.run(test_api_endpoint())
    else:
        print("\n❌ 기본 테스트 실패로 API 엔드포인트 테스트를 건너뜁니다.")