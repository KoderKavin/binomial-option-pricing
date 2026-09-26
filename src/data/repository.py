import pandas as pd
import numpy as np
from datetime import datetime
from src.data.db import get_stock_data, get_options_data, get_specific_option_contract
from src.data.yfinance_client import fetch_and_store_stock_data
from src.data.thetadata_client import fetch_and_store_options_data

def get_historical_volatility(symbol: str, target_date: str, window: int = 30) -> float:
    """Calculates historical volatility based on trailing stock returns."""
    df = get_stock_data(symbol, end_date=target_date)
    if len(df) < window:
        return 0.30 # Default fallback IV
    
    df_window = df.tail(window + 1)
    returns = np.log(df_window['close'] / df_window['close'].shift(1)).dropna()
    daily_vol = np.std(returns, ddof=1)
    annualized_vol = daily_vol * np.sqrt(252)
    return float(annualized_vol)

def ensure_stock_data(symbol: str, start_date: str, end_date: str):
    df = get_stock_data(symbol, start_date, end_date)
    if df.empty or len(df) < 5:
        fetch_and_store_stock_data(symbol, start_date, end_date)

def get_eod_stock_price(symbol: str, date: str) -> float:
    df = get_stock_data(symbol, start_date=date, end_date=date)
    if not df.empty:
        return df.iloc[0]['close']
    return None

def get_atm_option(symbol: str, date: str, stock_price: float):
    """
    Returns the closest ATM Call and Put options expiring on Friday 
    of the current week.
    """
    # Find Friday of current week
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    days_to_friday = 4 - date_obj.weekday()
    if days_to_friday < 0:
        days_to_friday += 7
    friday_str = (date_obj + pd.Timedelta(days=days_to_friday)).strftime("%Y-%m-%d")

    try:
        fetch_and_store_options_data(symbol, date, expiration_str=friday_str)
    except (ConnectionError, ValueError) as e:
        print(f"Notice: {e}")

    df = get_options_data(symbol, date)
    if df.empty:
        return None, None
        
    df_exp = df[df['expiration'] == friday_str].copy()
    if df_exp.empty:
        df_exp = df
    
    df_exp['distance'] = abs(df_exp['strike'] - stock_price)
    closest_strike = df_exp.loc[df_exp['distance'].idxmin()]['strike']
    
    atm_calls = df_exp[(df_exp['strike'] == closest_strike) & (df_exp['right'] == 'C')]
    atm_puts = df_exp[(df_exp['strike'] == closest_strike) & (df_exp['right'] == 'P')]
    
    call_opt = atm_calls.iloc[0].to_dict() if not atm_calls.empty else None
    put_opt = atm_puts.iloc[0].to_dict() if not atm_puts.empty else None
    
    return call_opt, put_opt

def get_option_quote(symbol: str, date: str, strike: float, right: str, expiration: str, stock_price: float):
    """
    Retrieves the specific contract's market price. If missing (e.g. at expiration),
    calculates intrinsic settlement value.
    """
    try:
        fetch_and_store_options_data(symbol, date, expiration_str=expiration)
    except (ConnectionError, ValueError):
        pass
        
    df = get_specific_option_contract(symbol, date, strike, right, expiration)
    
    if not df.empty:
        return df.iloc[0].to_dict()
        
    # If no quote available (e.g., expiration settlement), return intrinsic value
    phi = 1 if right == 'C' else -1
    intrinsic = max(phi * (stock_price - strike), 0.0)
    
    return {
        'symbol': symbol,
        'date': date,
        'expiration': expiration,
        'strike': strike,
        'right': right,
        'close': intrinsic,
        'bid': intrinsic,
        'ask': intrinsic,
        'is_synthetic_settlement': True
    }
