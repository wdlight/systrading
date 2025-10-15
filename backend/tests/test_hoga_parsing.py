"""
호가 데이터 파싱 테스트
"""

import pytest
from datetime import datetime
from app.domestic_websocket import parse_hoga_json


def test_parse_hoga_json():
    """JSON 호가 데이터 파싱 테스트"""
    json_data = {
        "header": {"tr_id": "H0STASP0", "tr_key": "005930"},
        "body": {
            "askp1": "71800", "askp_rsqn1": "100",
            "askp2": "71900", "askp_rsqn2": "200",
            "askp3": "72000", "askp_rsqn3": "300",
            "askp4": "72100", "askp_rsqn4": "400",
            "askp5": "72200", "askp_rsqn5": "500",
            "askp6": "72300", "askp_rsqn6": "600",
            "askp7": "72400", "askp_rsqn7": "700",
            "askp8": "72500", "askp_rsqn8": "800",
            "askp9": "72600", "askp_rsqn9": "900",
            "askp10": "72700", "askp_rsqn10": "1000",
            "bidp1": "71700", "bidp_rsqn1": "150",
            "bidp2": "71600", "bidp_rsqn2": "250",
            "bidp3": "71500", "bidp_rsqn3": "350",
            "bidp4": "71400", "bidp_rsqn4": "450",
            "bidp5": "71300", "bidp_rsqn5": "550",
            "bidp6": "71200", "bidp_rsqn6": "650",
            "bidp7": "71100", "bidp_rsqn7": "750",
            "bidp8": "71000", "bidp_rsqn8": "850",
            "bidp9": "70900", "bidp_rsqn9": "950",
            "bidp10": "70800", "bidp_rsqn10": "1050",
            "last": "71700", "time": "180015", "date": "20251014",
            "open": "71000", "high": "72500", "low": "70500",
            "vol": "1234567", "value": "78900000000",
            "sign": "2", "change": "500", "drate": "0.70"
        }
    }
    
    result = parse_hoga_json(json_data)
    
    # 기본 정보 확인
    assert result["stock_code"] == "005930"
    assert result["current_price"] == 71700
    assert result["timestamp"] == "2025-10-14T18:00:15"
    
    # 매도호가 확인 (1~10호가)
    assert len(result["asks"]) == 10
    assert result["asks"][0]["price"] == 71800
    assert result["asks"][0]["quantity"] == 100
    assert result["asks"][9]["price"] == 72700
    assert result["asks"][9]["quantity"] == 1000
    
    # 매수호가 확인 (1~10호가)
    assert len(result["bids"]) == 10
    assert result["bids"][0]["price"] == 71700
    assert result["bids"][0]["quantity"] == 150
    assert result["bids"][9]["price"] == 70800
    assert result["bids"][9]["quantity"] == 1050
    
    # 시장 데이터 확인
    market_data = result["market_data"]
    assert market_data["open"] == 71000
    assert market_data["high"] == 72500
    assert market_data["low"] == 70500
    assert market_data["volume"] == 1234567
    assert market_data["value"] == 78900000000
    assert market_data["sign"] == "2"
    assert market_data["change"] == 500
    assert market_data["drate"] == 0.70


def test_parse_hoga_json_missing_fields():
    """필수 필드가 누락된 경우 테스트"""
    json_data = {
        "header": {"tr_id": "H0STASP0", "tr_key": "005930"},
        "body": {
            "askp1": "71800",
            "bidp1": "71700",
            "last": "71700"
        }
    }
    
    result = parse_hoga_json(json_data)
    
    # 기본 정보는 있어야 함
    assert result["stock_code"] == "005930"
    assert result["current_price"] == 71700
    
    # 누락된 필드는 기본값으로 처리
    assert len(result["asks"]) == 10
    assert result["asks"][0]["price"] == 71800
    assert result["asks"][1]["price"] == 0  # 누락된 필드
    assert result["asks"][1]["quantity"] == 0
    
    assert len(result["bids"]) == 10
    assert result["bids"][0]["price"] == 71700
    assert result["bids"][1]["price"] == 0  # 누락된 필드
    assert result["bids"][1]["quantity"] == 0


def test_parse_hoga_json_empty_body():
    """빈 body인 경우 테스트"""
    json_data = {
        "header": {"tr_id": "H0STASP0", "tr_key": "005930"},
        "body": {}
    }
    
    result = parse_hoga_json(json_data)
    
    assert result["stock_code"] == "005930"
    assert result["current_price"] == 0
    assert len(result["asks"]) == 10
    assert len(result["bids"]) == 10
    
    # 모든 값이 기본값(0)이어야 함
    for ask in result["asks"]:
        assert ask["price"] == 0
        assert ask["quantity"] == 0
    
    for bid in result["bids"]:
        assert bid["price"] == 0
        assert bid["quantity"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
