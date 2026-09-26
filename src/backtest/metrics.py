import numpy as np
import pandas as pd
from tabulate import tabulate

def compute_metrics(initial_capital: float, strat_history: list, bench_history: list):
    
    if not strat_history:
        return "No trades executed."
        
    strat_final = strat_history[-1]['capital']
    bench_final = bench_history[-1]['value'] if bench_history else initial_capital
    
    # Strat Returns
    strat_caps = [initial_capital] + [h['capital'] for h in strat_history]
    strat_returns = pd.Series(strat_caps).pct_change().dropna()
    
    # Bench Returns (Weekly sampling for comparison if needed, but we can just use daily)
    bench_vals = [initial_capital] + [h['value'] for h in bench_history]
    bench_returns = pd.Series(bench_vals).pct_change().dropna()
    
    # Metrics
    def safe_cagr(start, end, periods, periods_per_year):
        if start <= 0 or periods == 0: return 0.0
        return (end / start) ** (periods_per_year / periods) - 1
        
    strat_cum_ret = (strat_final - initial_capital) / initial_capital * 100
    bench_cum_ret = (bench_final - initial_capital) / initial_capital * 100
    
    strat_cagr = safe_cagr(initial_capital, strat_final, len(strat_history), 52) * 100
    bench_cagr = safe_cagr(initial_capital, bench_final, len(bench_history), 252) * 100
    
    # Sharpe
    rf_weekly = 0.045 / 52
    rf_daily = 0.045 / 252
    
    strat_sharpe = np.sqrt(52) * (strat_returns.mean() - rf_weekly) / strat_returns.std() if strat_returns.std() != 0 else 0
    bench_sharpe = np.sqrt(252) * (bench_returns.mean() - rf_daily) / bench_returns.std() if bench_returns.std() != 0 else 0
    
    # Sortino
    strat_downside = strat_returns[strat_returns < 0].std()
    strat_sortino = np.sqrt(52) * (strat_returns.mean() - rf_weekly) / strat_downside if strat_downside > 0 else 0
    
    bench_downside = bench_returns[bench_returns < 0].std()
    bench_sortino = np.sqrt(252) * (bench_returns.mean() - rf_daily) / bench_downside if bench_downside > 0 else 0
    
    # Max Drawdown
    def mdd(series):
        cummax = series.cummax()
        drawdown = (series - cummax) / cummax
        return drawdown.min() * 100
        
    strat_mdd = mdd(pd.Series(strat_caps))
    bench_mdd = mdd(pd.Series(bench_vals))
    
    # Trade Stats
    winning_weeks = sum(1 for r in strat_returns if r > 0)
    win_rate = (winning_weeks / len(strat_returns)) * 100 if len(strat_returns) > 0 else 0
    
    early_exits = sum(1 for h in strat_history if 'Early Exit' in h['reason'])
    early_exit_freq = (early_exits / len(strat_history)) * 100 if len(strat_history) > 0 else 0
    
    table = [
        ["Metric", "Arbitrage Strategy", "Buy-and-Hold Benchmark"],
        ["Initial Capital ($)", f"{initial_capital:,.2f}", f"{initial_capital:,.2f}"],
        ["Final Net Portfolio Value ($)", f"{strat_final:,.2f}", f"{bench_final:,.2f}"],
        ["Total Cumulative Return (%)", f"{strat_cum_ret:.2f}%", f"{bench_cum_ret:.2f}%"],
        ["Compound Annual Growth Rate (CAGR)", f"{strat_cagr:.2f}%", f"{bench_cagr:.2f}%"],
        ["Annualized Sharpe Ratio", f"{strat_sharpe:.2f}", f"{bench_sharpe:.2f}"],
        ["Annualized Sortino Ratio", f"{strat_sortino:.2f}", f"{bench_sortino:.2f}"],
        ["Maximum Drawdown (MDD)", f"{strat_mdd:.2f}%", f"{bench_mdd:.2f}%"],
        ["Win Rate (%)", f"{win_rate:.2f}%", "N/A"],
        ["Early Exit Frequency", f"{early_exit_freq:.2f}%", "0.00%"]
    ]
    
    return tabulate(table, headers="firstrow", tablefmt="pipe")
