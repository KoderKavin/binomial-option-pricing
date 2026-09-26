import config
from src.strategy.positions import PortfolioState
from src.models.binomial_tree import get_theoretical_price

class ArbitrageStrategy:
    def __init__(self, initial_capital: float = 100000.0):
        self.portfolio = PortfolioState(cash_balance=initial_capital)
        self.current_trade = None
        self.strike = None
        self.right = None
        self.expiration = None
        
    def check_and_initiate(self, S0: float, C0: float, strike: float, right: str, expiration: str, sigma: float, num_contracts: int = 1):
        """Monday initiation: Check for mispricing and enter positions."""
        self.strike = strike
        self.right = right
        self.expiration = expiration
        
        # Calculate theoretical value and delta
        V0, delta = get_theoretical_price(S0, strike, config.RISK_FREE_RATE, sigma, config.DELTA_T, config.N_STEPS, right)
        shares_to_hedge = delta * config.CONTRACT_MULTIPLIER * num_contracts
        
        # Scenario A: Overpriced
        if C0 > V0:
            self.current_trade = 'Scenario_A'
            # Short Option
            self.portfolio.option_contracts = -num_contracts
            option_proceeds = (C0 - config.SLIPPAGE_OPTION) * config.CONTRACT_MULTIPLIER * num_contracts
            option_fee = config.FEE_PER_OPTION * num_contracts
            
            # Long Stock
            self.portfolio.stock_shares = shares_to_hedge
            stock_cost = (S0 + config.SLIPPAGE_SHARE) * shares_to_hedge
            stock_fee = config.COMMISSION_PER_SHARE * shares_to_hedge
            
            # Funded from existing cash; excess remains in cash earning risk-free rate
            net_outlay = stock_cost + stock_fee + option_fee - option_proceeds
            self.portfolio.cash_balance -= net_outlay
            self.portfolio.total_fees += (option_fee + stock_fee)
            
        # Scenario B: Underpriced
        elif C0 < V0:
            self.current_trade = 'Scenario_B'
            # Long Option
            self.portfolio.option_contracts = num_contracts
            option_cost = (C0 + config.SLIPPAGE_OPTION) * config.CONTRACT_MULTIPLIER * num_contracts
            option_fee = config.FEE_PER_OPTION * num_contracts
            
            # Short Stock
            self.portfolio.stock_shares = -shares_to_hedge # short position
            stock_proceeds = (S0 - config.SLIPPAGE_SHARE) * shares_to_hedge
            stock_fee = config.COMMISSION_PER_SHARE * shares_to_hedge
            
            # Net proceeds added to cash balance; all cash earns risk-free rate
            net_inflow = stock_proceeds - option_cost - option_fee - stock_fee
            self.portfolio.cash_balance += net_inflow
            self.portfolio.total_fees += (option_fee + stock_fee)
            
        return self.current_trade
        
    def check_early_exit(self, S_i: float, V_i: float, C_i: float = None) -> bool:
        """Check Sub-Intrinsic Value Decay and Price Convergence Triggers"""
        if not self.current_trade:
            return False
            
        phi = 1 if self.right == 'C' else -1
        IV = max(phi * (S_i - self.strike), 0.0)
        
        # 1. Price Convergence Trigger
        if C_i is not None:
            if self.current_trade == 'Scenario_A' and C_i <= V_i:
                return True
            elif self.current_trade == 'Scenario_B' and C_i >= V_i:
                return True
                
        # 2. Sub-Intrinsic Value Trigger (Theoretical)
        if V_i < IV:
            return True
            
        return False
        
    def liquidate(self, S_t: float, C_t: float):
        """Liquidate positions and return net portfolio cash balance."""
        if not self.current_trade:
            return self.portfolio.cash_balance
            
        contracts = abs(self.portfolio.option_contracts)
        shares = abs(self.portfolio.stock_shares)
        
        # Unwind Option
        if self.portfolio.option_contracts > 0:
            # Sell to close
            option_proceeds = (C_t - config.SLIPPAGE_OPTION) * config.CONTRACT_MULTIPLIER * contracts
            self.portfolio.cash_balance += option_proceeds
        else:
            # Buy to close
            option_cost = (C_t + config.SLIPPAGE_OPTION) * config.CONTRACT_MULTIPLIER * contracts
            self.portfolio.cash_balance -= option_cost
            
        option_fee = config.FEE_PER_OPTION * contracts
        self.portfolio.cash_balance -= option_fee
        self.portfolio.total_fees += option_fee
        
        # Unwind Stock
        if self.portfolio.stock_shares > 0:
            # Sell to close
            stock_proceeds = (S_t - config.SLIPPAGE_SHARE) * shares
            self.portfolio.cash_balance += stock_proceeds
        else:
            # Buy to cover
            stock_cost = (S_t + config.SLIPPAGE_SHARE) * shares
            self.portfolio.cash_balance -= stock_cost
            
            # Locate fee
            notional = shares * S_t
            locate_fee = notional * (config.SHORT_LOCATE_FEE / config.DAYS_IN_YEAR) * 5 # Approx for the week
            self.portfolio.cash_balance -= locate_fee
            self.portfolio.total_fees += locate_fee
            
        stock_fee = config.COMMISSION_PER_SHARE * shares
        self.portfolio.cash_balance -= stock_fee
        self.portfolio.total_fees += stock_fee
        
        net_value = self.portfolio.cash_balance
        self.portfolio.reset_positions()
        self.current_trade = None
        self.strike = None
        self.right = None
        self.expiration = None
        
        return net_value
