import argparse
import sys
from src.data.db import init_db
from src.data.yfinance_client import fetch_and_store_stock_data
from src.backtest.engine import BacktestEngine
from src.backtest.benchmark import run_benchmark
from src.backtest.metrics import compute_metrics
import config

def main():
    parser = argparse.ArgumentParser(description="Google American Option Arbitrage Strategy")
    parser.add_argument('--init-db', action='store_true', help="Initialize the SQLite database")
    parser.add_argument('--purge-options', action='store_true', help="Purge all options data from the database")
    parser.add_argument('--fetch-data', action='store_true', help="Fetch stock data")
    parser.add_argument('--run-backtest', action='store_true', help="Run the 50-week backtest")
    parser.add_argument('--symbol', type=str, default=config.SYMBOL, help="Ticker symbol")
    parser.add_argument('--start', type=str, default="2025-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default="2025-12-19", help="End date (YYYY-MM-DD) - Approx 50 weeks")
    parser.add_argument('--capital', type=float, default=100000.0, help="Initial capital for backtest")
    
    args = parser.parse_args()
    
    if args.purge_options:
        print("Purging mock options data...")
        from src.data.db import purge_options_data
        purge_options_data()
        print("Options data purged.")

    if args.init_db:
        print("Initializing database...")
        init_db()
        print("Database initialized.")
        
    if args.fetch_data:
        print(f"Fetching stock data for {args.symbol} from {args.start} to {args.end}...")
        fetch_and_store_stock_data(args.symbol, args.start, args.end)
        
    if args.run_backtest:
        print(f"Running backtest for {args.symbol} from {args.start} to {args.end}...")
        engine = BacktestEngine(args.symbol, args.start, args.end)
        initial_capital, strat_history = engine.run(initial_capital=args.capital)
        
        bench_final, bench_history = run_benchmark(args.symbol, initial_capital, args.start, args.end)
        
        print("\n=== Performance Report ===")
        report = compute_metrics(initial_capital, strat_history, bench_history)
        print(report)

if __name__ == '__main__':
    main()
