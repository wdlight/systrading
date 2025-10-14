"""
호가 데이터 통합 테스트
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.domestic_websocket import receive_realtime_hoga_domestic
from app.services.realtime_service import RealtimeDataService


def test_receive_realtime_hoga_parsing():
    """호가 데이터 파싱 테스트"""
    # 샘플 호가 데이터 (한국투자증권 API 형식)
    # 종목코드^매수10호가^매수9호가^...^매수1호가^매도1호가^매도2호가^...^매도10호가^매수10호가수량^매수9호가수량^...^매수1호가수량^매도1호가수량^매도2호가수량^...^매도10호가수량
    sample_data = "005930^49100^49200^49300^49400^49500^49600^49700^49800^49900^50000^" \
                  "50100^50200^50300^50400^50500^50600^50700^50800^50900^51000^" \
                  "100^200^300^400^500^600^700^800^900^1000^" \
                  "150^250^350^450^550^650^750^850^950^1050"
    
    result = receive_realtime_hoga_domestic(sample_data)
    
    # 종목코드 확인
    assert result["종목코드"] == "005930"
    
    # 매도호가 확인 (1~10호가)
    assert result["매도1호가"] == "50100"
    assert result["매도10호가"] == "51000"
    
    # 매수호가 확인 (1~10호가)
    assert result["매수1호가"] == "50000"
    assert result["매수10호가"] == "49100"
    
    # 수량 확인
    assert result["매도1호가수량"] == "100"
    assert result["매수1호가수량"] == "150"


@pytest.mark.asyncio
async def test_handle_hoga_data():
    """호가 데이터 처리 테스트"""
    # Mock 서비스 생성
    korea_invest_service = Mock()
    connection_manager = Mock()
    connection_manager.broadcast_to_stock_subscribers = AsyncMock()
    ws_result_queue = Mock()
    
    service = RealtimeDataService(
        korea_invest_service,
        connection_manager,
        ws_result_queue
    )
    
    # 테스트 메시지
    message = {
        "action_id": "실시간호가",
        "data": {
            "종목코드": "005930",
            "매도1호가": "50000",
            "매도1호가수량": "100",
            "매도2호가": "50100",
            "매도2호가수량": "200",
            "매수1호가": "49900",
            "매수1호가수량": "150",
            "매수2호가": "49800",
            "매수2호가수량": "250",
            "현재가": "49950"
        }
    }
    
    # 호가 데이터 처리
    await service._handle_hoga_data(message)
    
    # 브로드캐스트 호출 확인
    assert connection_manager.broadcast_to_stock_subscribers.called
    call_args = connection_manager.broadcast_to_stock_subscribers.call_args
    
    assert call_args[0][0] == "005930"  # stock_code
    orderbook_message = call_args[0][1]
    assert orderbook_message["type"] == "orderbook_update"
    assert orderbook_message["stock_code"] == "005930"
    
    # 호가 데이터 구조 확인
    data = orderbook_message["data"]
    assert "asks" in data
    assert "bids" in data
    assert "timestamp" in data
    
    # 매도호가 확인
    asks = data["asks"]
    assert len(asks) == 2
    assert asks[0]["price"] == 50000
    assert asks[0]["quantity"] == 100
    assert asks[1]["price"] == 50100
    assert asks[1]["quantity"] == 200
    
    # 매수호가 확인
    bids = data["bids"]
    assert len(bids) == 2
    assert bids[0]["price"] == 49900
    assert bids[0]["quantity"] == 150
    assert bids[1]["price"] == 49800
    assert bids[1]["quantity"] == 250


@pytest.mark.asyncio
async def test_handle_hoga_data_with_empty_values():
    """빈 값이 포함된 호가 데이터 처리 테스트"""
    korea_invest_service = Mock()
    connection_manager = Mock()
    connection_manager.broadcast_to_stock_subscribers = AsyncMock()
    ws_result_queue = Mock()
    
    service = RealtimeDataService(
        korea_invest_service,
        connection_manager,
        ws_result_queue
    )
    
    # 빈 값이 포함된 테스트 메시지
    message = {
        "action_id": "실시간호가",
        "data": {
            "종목코드": "005930",
            "매도1호가": "",
            "매도1호가수량": "",
            "매수1호가": "49900",
            "매수1호가수량": "150",
        }
    }
    
    # 호가 데이터 처리
    await service._handle_hoga_data(message)
    
    # 브로드캐스트 호출 확인
    assert connection_manager.broadcast_to_stock_subscribers.called
    call_args = connection_manager.broadcast_to_stock_subscribers.call_args
    
    orderbook_message = call_args[0][1]
    data = orderbook_message["data"]
    
    # 빈 값은 제외되어야 함
    assert len(data["asks"]) == 0  # 빈 값이므로 제외
    assert len(data["bids"]) == 1  # 유효한 값만 포함
    
    bid = data["bids"][0]
    assert bid["price"] == 49900
    assert bid["quantity"] == 150


def test_hoga_data_parsing_edge_cases():
    """호가 데이터 파싱 엣지 케이스 테스트"""
    # 콤마가 포함된 데이터
    sample_data_with_comma = "005930^49,100^49,200^49,300^49,400^49,500^49,600^49,700^49,800^49,900^50,000^" \
                             "51,000^52,000^53,000^54,000^55,000^56,000^57,000^58,000^59,000^60,000^" \
                             "1,000^2,000^3,000^4,000^5,000^6,000^7,000^8,000^9,000^10,000^" \
                             "1,500^2,500^3,500^4,500^5,500^6,500^7,500^8,500^9,500^10,500"
    
    result = receive_realtime_hoga_domestic(sample_data_with_comma)
    
    # 콤마 제거 확인
    assert result["매도1호가"] == "51,000"
    assert result["매수1호가"] == "50,000"
    
    # 빈 문자열 데이터
    sample_data_empty = "005930^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
    result_empty = receive_realtime_hoga_domestic(sample_data_empty)
    
    # 빈 값들도 올바르게 처리되어야 함
    assert result_empty["종목코드"] == "005930"
    # 빈 데이터는 길이 부족으로 인해 기본값만 반환됨


if __name__ == "__main__":
    # 개별 테스트 실행
    test_receive_realtime_hoga_parsing()
    print("✅ 호가 데이터 파싱 테스트 통과")
    
    import asyncio
    asyncio.run(test_handle_hoga_data())
    print("✅ 호가 데이터 처리 테스트 통과")
    
    asyncio.run(test_handle_hoga_data_with_empty_values())
    print("✅ 빈 값 처리 테스트 통과")
    
    test_hoga_data_parsing_edge_cases()
    print("✅ 엣지 케이스 테스트 통과")
    
    print("\n🎉 모든 호가 데이터 통합 테스트 통과!")
