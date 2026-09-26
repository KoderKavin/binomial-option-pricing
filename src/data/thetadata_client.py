import io
import requests
import pandas as pd
from datetime import datetime
import config
from src.data.db import save_options_data, get_options_data

def fetch_and_store_options_data(symbol: str, date_str: str, expiration_str: str = None):
    """
    Fetches EOD option data for a specific date from ThetaTerminal REST API v3.
    Raises ConnectionError if the terminal is offline or data cannot be fetched.
    """
    # Check if already in DB
    existing_df = get_options_data(symbol, date_str)
    if not existing_df.empty:
        return
        
    url = f"{config.THETA_TERMINAL_URL}/option/history/eod"
    date_clean = date_str.replace("-", "")
    
    # Try with expiration filter if provided, or wildcard
    exp_param = expiration_str.replace("-", "") if expiration_str else "*"
    params = {
        "symbol": symbol,
        "start_date": date_clean,
        "end_date": date_clean,
        "expiration": exp_param,
        "strike": "*",
        "right": "both",
        "format": "csv"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10.0)
        
        # If specific expiration returned empty or 404, retry with wildcard
        if response.status_code != 200 and exp_param != "*":
            params["expiration"] = "*"
            response = requests.get(url, params=params, timeout=10.0)
            
        if response.status_code == 200:
            content = response.text.strip()
            if not content:
                raise ValueError(f"ThetaTerminal returned empty response for {symbol} on {date_str}.")
            
            try:
                raw_df = pd.read_csv(io.StringIO(content))
            except Exception as e:
                snippet = content[:300]
                raise ValueError(f"Failed to parse ThetaTerminal CSV: {e}. Raw snippet: {snippet}")
                
            raw_df.columns = [c.strip().lower() for c in raw_df.columns]
            
            if 'expiration' not in raw_df.columns or raw_df.empty:
                snippet = content[:300]
                raise ValueError(f"No option records in CSV for {symbol} on {date_str}. Raw snippet: {snippet}")
                
            df = _convert_raw_thetadata_to_schema(symbol, date_str, raw_df)
            if not df.empty:
                save_options_data(df)
                print(f"Stored {len(df)} live options records for {symbol} on {date_str}.")
                return
            else:
                snippet = content[:300]
                raise ValueError(f"Parsed 0 valid records for {symbol} on {date_str}. Raw snippet: {snippet}")
        else:
            snippet = response.text[:300]
            raise ConnectionError(f"ThetaTerminal returned HTTP {response.status_code}: {snippet}")
            
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"ThetaTerminal is offline or unreachable: {e}")

def _convert_raw_thetadata_to_schema(symbol: str, date_str: str, raw_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(index=raw_df.index)
    df['symbol'] = symbol
    df['date'] = date_str
    
    def fmt_exp(val):
        s = str(val).split('T')[0].replace('-', '')
        if len(s) >= 8:
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
        return str(val)
        
    df['expiration'] = raw_df['expiration'].apply(fmt_exp)
    
    # Strike formatting
    df['strike'] = raw_df['strike'].astype(float).apply(lambda x: x / 1000.0 if x > 10000 else x)
    
    # Right formatting ('C' or 'P')
    df['right'] = raw_df['right'].astype(str).str.upper().apply(lambda x: 'C' if x.startswith('C') else 'P')
    
    # Close price
    df['close'] = raw_df['close'].astype(float) if 'close' in raw_df.columns else 0.0
    
    # Bid / Ask
    if 'bid' in raw_df.columns:
        df['bid'] = raw_df['bid'].astype(float)
    elif 'bid_price' in raw_df.columns:
        df['bid'] = raw_df['bid_price'].astype(float)
    else:
        df['bid'] = df['close']
        
    if 'ask' in raw_df.columns:
        df['ask'] = raw_df['ask'].astype(float)
    elif 'ask_price' in raw_df.columns:
        df['ask'] = raw_df['ask_price'].astype(float)
    else:
        df['ask'] = df['close']
        
    df['volume'] = raw_df['volume'].fillna(0).astype(int) if 'volume' in raw_df.columns else 0
    df['open_interest'] = raw_df['count'].fillna(0).astype(int) if 'count' in raw_df.columns else 0
    df['implied_vol'] = 0.30
    
    return df

