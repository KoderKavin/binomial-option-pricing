import pytest
import config
from src.strategy.positions import PortfolioState
from src.strategy.arbitrage import ArbitrageStrategy

def test_portfolio_initial_capital_and_daily_interest():
    portfolio = PortfolioState(cash_balance=100000.0)
    assert portfolio.cash_balance == 100000.0
    
    # 1 day of risk-free interest
    daily_rate = config.RATE_LEND / config.DAYS_IN_YEAR
    portfolio.apply_daily_interest()
    assert portfolio.cash_balance == pytest.approx(100000.0 * (1 + daily_rate))

def test_arbitrage_uses_own_cash_in_scenario_a():
    strat = ArbitrageStrategy(initial_capital=100000.0)
    
    # Initiation where option is overpriced (Scenario A)
    # S0=180, C0=10 (overpriced compared to CRR theoretical value)
    trade = strat.check_and_initiate(
        S0=180.0,
        C0=10.0,
        strike=180.0,
        right='C',
        expiration='2025-01-10',
        sigma=0.25,
        num_contracts=2
    )
    
    assert trade == 'Scenario_A'
    assert strat.portfolio.option_contracts == -2
    assert strat.portfolio.stock_shares > 0
    # Crucial check: Cash balance should remain positive (funded from 100k, not borrowed)
    assert strat.portfolio.cash_balance > 0
    assert strat.portfolio.cash_balance < 100000.0
    
    # Verify daily interest accrues on the idle cash
    cash_before = strat.portfolio.cash_balance
    strat.portfolio.apply_daily_interest()
    assert strat.portfolio.cash_balance > cash_before
    
    # Liquidation
    final_cash = strat.liquidate(S_t=182.0, C_t=8.0)
    assert strat.portfolio.option_contracts == 0
    assert strat.portfolio.stock_shares == 0.0
    assert strat.portfolio.cash_balance == final_cash
    assert final_cash > 0
