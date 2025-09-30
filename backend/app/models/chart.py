from pydantic import BaseModel
from typing import List

from app.models.schemas import ChartCandle # Import ChartCandle from schemas

class ChartCandleResponse(BaseModel):
    data: List[ChartCandle] # Now refers to app.models.schemas.ChartCandle
    stock_code: str
    stock_name: str