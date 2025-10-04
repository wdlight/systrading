# pip install pykrx
from pykrx import stock
import pandas as pd

tickers_kospi = stock.get_market_ticker_list(market="KOSPI")
tickers_kosdaq = stock.get_market_ticker_list(market="KOSDAQ")

rows = []
for t in tickers_kospi + tickers_kosdaq:
    rows.append({"code": t, "name": stock.get_market_ticker_name(t)})

df = pd.DataFrame(rows)
print(df.head())
