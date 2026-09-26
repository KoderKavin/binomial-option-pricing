from dataclasses import dataclass
import config

@dataclass
class PortfolioState:
    option_contracts: int = 0  # + for Long, - for Short
    stock_shares: float = 0.0  # + for Long, - for Short
    cash_balance: float = 100000.0  # + for deposit / idle cash, - for margin borrow
    total_fees: float = 0.0
    
    def apply_daily_interest(self):
        """Compounds daily interest on cash balance.
        If positive (idle cash / deposits), earns the risk-free lending rate.
        If negative (margin borrowing), pays the institutional borrow rate.
        """
        if self.cash_balance > 0:
            daily_rate = config.RATE_LEND / config.DAYS_IN_YEAR
            self.cash_balance *= (1 + daily_rate)
        elif self.cash_balance < 0:
            daily_rate = config.RATE_BORROW / config.DAYS_IN_YEAR
            self.cash_balance *= (1 + daily_rate)
            
    def reset_positions(self):
        """Resets active position legs without wiping out cash balance."""
        self.option_contracts = 0
        self.stock_shares = 0.0

    def reset(self, initial_cash: float = 100000.0):
        self.option_contracts = 0
        self.stock_shares = 0.0
        self.cash_balance = initial_cash
        self.total_fees = 0.0

