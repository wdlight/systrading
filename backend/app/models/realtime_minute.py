from dataclasses import dataclass
from datetime import datetime
from app.models.schemas import ChartCandle


@dataclass
class MinuteCandleState:
    minute_key: str  # "YYYY-MM-DDTHH:MM:00"
    open: float
    high: float
    low: float
    close: float
    volume: int
    start_ts: datetime
    last_tick_ts: datetime

    def apply_tick(self, price: float, volume: int, tick_ts: datetime) -> None:
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += volume
        self.last_tick_ts = tick_ts

    def apply_price_only(self, price: float, tick_ts: datetime) -> None:
        """
        호가 데이터처럼 거래량 없이 가격만 업데이트
        (현재가 변동 추적용)

        Args:
            price: 현재가
            tick_ts: 업데이트 시각

        Note:
            - high/low 자동 갱신
            - close 업데이트
            - volume은 변경 안 함 (호가에는 거래량 없음)
        """
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        # volume은 업데이트 안 함 (호가에는 거래량 없음)
        self.last_tick_ts = tick_ts

    def to_chart_candle(self) -> ChartCandle:
        return ChartCandle(
            timestamp=self.minute_key,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )
