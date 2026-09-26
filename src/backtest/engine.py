import pandas as pd
from datetime import datetime, timedelta
import config
from src.data.repository import ensure_stock_data, get_stock_data, get_atm_option, get_historical_volatility, get_option_quote
from src.strategy.arbitrage import ArbitrageStrategy
from src.models.binomial_tree import get_theoretical_price

class BacktestEngine:
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.strategy = ArbitrageStrategy()
        
        # Portfolio history
        self.history = []
        
    def run(self, initial_capital=None):
        if initial_capital is None:
            initial_capital = 100000.0
            
        self.strategy = ArbitrageStrategy(initial_capital=initial_capital)
        self.history = []
        
        # Fetch required stock data
        ensure_stock_data(self.symbol, self.start_date, self.end_date)
        df_stock = get_stock_data(self.symbol, self.start_date, self.end_date)
        
        week_count = 0
        current_week_start = None
        week_start_capital = initial_capital
        
        for index, row in df_stock.iterrows():
            date_str = row['date']
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = date_obj.weekday()
            S_t = row['close']
            
            # Monday Initiation (or first day of the week if Monday is holiday)
            if not self.strategy.current_trade and weekday <= 1: 
                call_opt, put_opt = get_atm_option(self.symbol, date_str, S_t)
                if not call_opt and not put_opt:
                    self.strategy.portfolio.apply_daily_interest()
                    continue # No option data available
                    
                # For simplicity, let's trade the Call option. Can be expanded to evaluate both.
                opt = call_opt if call_opt else put_opt
                if not opt:
                    self.strategy.portfolio.apply_daily_interest()
                    continue
                    
                sigma = get_historical_volatility(self.symbol, date_str)
                
                # Determine number of contracts to trade based on capital
                current_cash = self.strategy.portfolio.cash_balance
                num_contracts = 1
                if current_cash > 0:
                    notional = S_t * config.CONTRACT_MULTIPLIER
                    num_contracts = max(1, int((current_cash * 0.5) / notional))
                
                trade_type = self.strategy.check_and_initiate(
                    S_t, opt['close'], opt['strike'], opt['right'], opt['expiration'], sigma, num_contracts
                )
                
                if trade_type:
                    current_week_start = date_str
                    week_start_capital = current_cash
            
            # Monitoring and Exits
            if self.strategy.current_trade:
                liquidated = False
                exit_reason = None
                
                # Check early exit (Tuesday-Thursday, on days after initiation)
                if date_str != current_week_start and weekday < 4:
                    # Get actual market price for the option today
                    opt_data = get_option_quote(
                        self.symbol, date_str, self.strategy.strike, self.strategy.right, self.strategy.expiration, S_t
                    )
                    C_i = opt_data['close'] if opt_data else None
                    
                    if C_i is not None:
                        sigma = get_historical_volatility(self.symbol, date_str)
                        # Use remaining days to expiration instead of full N_STEPS
                        days_remaining = max(1, 4 - weekday)
                        
                        # Theoretical value today
                        V_i, _ = get_theoretical_price(S_t, self.strategy.strike, config.RISK_FREE_RATE, sigma, config.DELTA_T, days_remaining, self.strategy.right)
                        
                        if self.strategy.check_early_exit(S_t, V_i, C_i):
                            liquidated = True
                            exit_reason = 'Early Exit (Price Convergence)'
                
                # Mandatory Settlement (Friday)
                if weekday == 4 and not liquidated:
                    liquidated = True
                    exit_reason = 'Mandatory Expiration (Friday)'
                    
                if liquidated:
                    opt_data = get_option_quote(
                        self.symbol, date_str, self.strategy.strike, self.strategy.right, self.strategy.expiration, S_t
                    )
                    C_t = opt_data['close'] if opt_data else 0.0
                    
                    final_cash = self.strategy.liquidate(S_t, C_t)
                    net_value = final_cash - week_start_capital
                    
                    self.history.append({
                        'week_start': current_week_start,
                        'exit_date': date_str,
                        'reason': exit_reason,
                        'net_value': net_value,
                        'capital': final_cash
                    })
                    week_count += 1
                    
                    if week_count >= config.WEEKS:
                        break

            # Apply daily interest on whatever cash remains in portfolio at the end of each day
            self.strategy.portfolio.apply_daily_interest()
                        
        return initial_capital, self.history
