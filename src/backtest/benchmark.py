import pandas as pd
from src.data.repository import get_stock_data

def run_benchmark(symbol: str, initial_capital: float, start_date: str, end_date: str):
    df_stock = get_stock_data(symbol, start_date, end_date)
    if df_stock.empty:
        return initial_capital, []
        
    start_price = df_stock.iloc[0]['close']
    shares = initial_capital / start_price
    
    history = []
    current_cash = 0.0
    
    for index, row in df_stock.iterrows():
        # Dividend reinvestment
        if row['dividend_yield'] > 0:
            dividend_amount = row['dividend_yield'] * row['close'] * shares
            current_cash += dividend_amount
            new_shares = current_cash / row['close']
            shares += new_shares
            current_cash = 0.0
            
        history.append({
            'date': row['date'],
            'value': shares * row['close']
        })
        
    final_value = shares * df_stock.iloc[-1]['close']
    return final_value, history
