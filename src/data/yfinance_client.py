import yfinance as yf
import pandas as pd
from datetime import datetime
from src.data.db import save_stock_data, get_stock_data

def fetch_and_store_stock_data(symbol: str, start_date: str, end_date: str):
    print(f"Fetching {symbol} stock data from yfinance...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
    
    if df.empty:
        print("No data fetched.")
        return

    # Prepare DataFrame for DB
    records = []
    for date, row in df.iterrows():
        # Get dividends if available
        div = row['Dividends'] if 'Dividends' in row else 0.0
        div_yield = div / row['Close'] if row['Close'] > 0 else 0.0

        records.append({
            'symbol': symbol,
            'date': date.strftime('%Y-%m-%d'),
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'adj_close': float(row['Adj Close']),
            'volume': int(row['Volume']),
            'dividend_yield': float(div_yield)
        })

    df_records = pd.DataFrame(records)
    
    # Remove existing dates to avoid constraint failures
    existing_df = get_stock_data(symbol, start_date, end_date)
    if not existing_df.empty:
        existing_dates = set(existing_df['date'].tolist())
        df_records = df_records[~df_records['date'].isin(existing_dates)]
    
    if not df_records.empty:
        save_stock_data(df_records)
        print(f"Stored {len(df_records)} new stock records for {symbol}.")
    else:
        print(f"All stock records for {symbol} are already up to date.")
