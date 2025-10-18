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

    def to_chart_candle(self) -> ChartCandle:
        return ChartCandle(
            timestamp=self.minute_key,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )
