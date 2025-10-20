import yfinance as yf
import asyncio
import json

async def test_ticker(ticker_symbol):
    """Fetches and prints yfinance ticker info."""
    try:
        print(f"--- Testing {ticker_symbol} ---")
        ticker = yf.Ticker(ticker_symbol)
        info = await asyncio.to_thread(lambda: ticker.info)
        print(json.dumps(info, indent=2))
    except Exception as e:
        print(f"!!! FAILED to fetch {ticker_symbol}: {e}")
        # Print the full exception traceback
        import traceback
        traceback.print_exc()

async def main():
    """Tests multiple tickers."""
    # Test all tickers from the service
    index_mapping = {
        "kospi": "^KS11",
        "kosdaq": "^KQ11",
        "nasdaq": "^IXIC",
        "dow": "^DJI",
        "sp500": "^GSPC",
        "usd_krw": "USDKRW=X",
        "nyse": "^NYA",
        "russell2000": "^RUT",
        "ftse": "^FTSE",
        "dax": "^GDAXI",
        "cac40": "^FCHI",
        "nikkei225": "^N225",
        "hangseng": "^HSI",
        "shanghai": "000001.SS"
    }
    await asyncio.gather(*(test_ticker(ticker) for ticker in index_mapping.values()))

if __name__ == "__main__":
    asyncio.run(main())