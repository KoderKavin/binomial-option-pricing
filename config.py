import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'market_data.db')

# API Settings
THETA_TERMINAL_URL = 'http://127.0.0.1:25503/v3'

# Backtest Settings
SYMBOL = 'GOOGL'
YEAR = 2025
WEEKS = 50

# Binomial Model Settings
N_STEPS = 4
DAYS_IN_YEAR = 252
DELTA_T = 1.0 / DAYS_IN_YEAR
RISK_FREE_RATE = 0.045  # 4.5% annualized

# Transaction Costs & Frictions
COMMISSION_PER_SHARE = 0.005
FEE_PER_OPTION = 0.65
SLIPPAGE_SHARE = 0.01
SLIPPAGE_OPTION = 0.02
CONTRACT_MULTIPLIER = 100

# Financing / Borrowing rates
BORROW_SPREAD = 0.015
RATE_BORROW = RISK_FREE_RATE + BORROW_SPREAD  # 6.0%
RATE_LEND = RISK_FREE_RATE                    # 4.5%
SHORT_LOCATE_FEE = 0.005                      # 0.5% annualized
