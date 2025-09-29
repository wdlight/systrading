from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
from app.core.korea_invest import KoreaInvestAPIService
from loguru import logger

class StockService:
    """주식 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, ki_client: KoreaInvestAPIService):
        self.ki_client = ki_client

    async def get_chart_data(self, stock_code: str, period: str) -> Optional[Dict[str, Any]]:
        """
        기간별 시세 차트 데이터를 조회합니다.
        :param stock_code: 종목 코드
        :param period: 기간 구분 (D: 일, W: 주, M: 월)
        :return: 차트 데이터 (JSON 직렬화 가능 형태)
        """
        if not self.ki_client or not self.ki_client.is_connected:
            logger.error("한국투자증권 API가 연결되지 않았습니다.")
            return None

        # 조회 기간 설정 (최근 1년)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        formatted_start_date = start_date.strftime("%Y%m%d")
        formatted_end_date = end_date.strftime("%Y%m%d")

        try:
            # ki_api.py의 get_daily_price_chart 함수를 호출해야 합니다.
            # KoreaInvestAPIService에 해당 메소드를 추가해야 합니다.
            # 임시로 api_instance를 직접 사용합니다.
            if not hasattr(self.ki_client.api_instance, 'get_daily_price_chart'):
                logger.error("ki_api.py에 get_daily_price_chart 함수가 없습니다.")
                return None

            df = await self.ki_client._run_in_executor(
                self.ki_client.api_instance.get_daily_price_chart,
                stock_code,
                formatted_start_date,
                formatted_end_date,
                period
            )

            if df is None or df.empty:
                logger.warning(f"{stock_code}에 대한 차트 데이터를 가져오지 못했습니다.")
                return {"output1": {}, "output2": []}

            # DataFrame을 JSON으로 변환
            # output2 형식에 맞춤
            chart_data = df.to_dict('records')
            
            # KIS API 응답 형식과 유사하게 맞춤
            # stck_bsop_date, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr, acml_vol
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

            # output1은 현재가 정보 등을 담지만, 여기서는 빈 객체로 둡니다.
            return {"output1": {}, "output2": renamed_data}

        except Exception as e:
            logger.error(f"차트 데이터 조회 중 오류 발생: {e}")
            return None
