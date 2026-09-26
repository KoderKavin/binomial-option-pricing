import sqlite3
import pandas as pd
import os
import config

def get_connection():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create stock_prices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            symbol TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume INTEGER,
            dividend_yield REAL,
            PRIMARY KEY (symbol, date)
        )
    ''')
    
    # Create option_contracts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS option_contracts (
            symbol TEXT,
            date TEXT,
            expiration TEXT,
            strike REAL,
            right TEXT,
            bid REAL,
            ask REAL,
            close REAL,
            volume INTEGER,
            open_interest INTEGER,
            implied_vol REAL,
            PRIMARY KEY (symbol, date, expiration, strike, right)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_stock_data(df: pd.DataFrame):
    if df.empty:
        return
    conn = get_connection()
    df.to_sql('stock_prices', conn, if_exists='append', index=False, method='multi')
    conn.close()

def save_options_data(df: pd.DataFrame):
    if df.empty:
        return
    conn = get_connection()
    # Use ignore on conflict to avoid duplicate errors on same date/strike/exp
    columns = ', '.join(df.columns)
    placeholders = ', '.join(['?'] * len(df.columns))
    sql = f'INSERT OR IGNORE INTO option_contracts ({columns}) VALUES ({placeholders})'
    
    cursor = conn.cursor()
    cursor.executemany(sql, df.values.tolist())
    conn.commit()
    conn.close()

def get_stock_data(symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    conn = get_connection()
    query = f"SELECT * FROM stock_prices WHERE symbol = '{symbol}'"
    if start_date:
        query += f" AND date >= '{start_date}'"
    if end_date:
        query += f" AND date <= '{end_date}'"
    query += " ORDER BY date ASC"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_options_data(symbol: str, date: str) -> pd.DataFrame:
    conn = get_connection()
    query = f"SELECT * FROM option_contracts WHERE symbol = '{symbol}' AND date = '{date}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
def purge_options_data(symbol: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    if symbol:
        cursor.execute(f"DELETE FROM option_contracts WHERE symbol = '{symbol}'")
    else:
        cursor.execute("DELETE FROM option_contracts")
    conn.commit()
    conn.close()

def get_specific_option_contract(symbol: str, date: str, strike: float, right: str, expiration: str) -> pd.DataFrame:
    conn = get_connection()
    query = f"""
        SELECT * FROM option_contracts 
        WHERE symbol = '{symbol}' 
        AND date = '{date}' 
        AND strike = {strike} 
        AND right = '{right}' 
        AND expiration = '{expiration}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
