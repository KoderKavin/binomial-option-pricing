import pytest
import numpy as np
from src.models.binomial_tree import get_theoretical_price

def test_binomial_call_pricing():
    # Example parameters
    S0 = 100
    K = 100
    r = 0.05
    sigma = 0.2
    dt = 1/252
    N = 4
    
    # Calculate price
    V_call, delta_call = get_theoretical_price(S0, K, r, sigma, dt, N, right='C')
    
    # Value should be positive
    assert V_call > 0
    # Delta should be between 0 and 1 for a call
    assert 0 <= delta_call <= 1

def test_binomial_put_pricing():
    # Example parameters
    S0 = 100
    K = 100
    r = 0.05
    sigma = 0.2
    dt = 1/252
    N = 4
    
    # Calculate price
    V_put, delta_put = get_theoretical_price(S0, K, r, sigma, dt, N, right='P')
    
    # Value should be positive
    assert V_put > 0
    # Delta should be between -1 and 0 for a put
    assert -1 <= delta_put <= 0

def test_early_exercise_premium():
    # Deep ITM Put option
    S0 = 50
    K = 100
    r = 0.05
    sigma = 0.2
    dt = 1/252
    N = 4
    
    V_put, _ = get_theoretical_price(S0, K, r, sigma, dt, N, right='P')
    
    # American put should be at least intrinsic value
    intrinsic = K - S0
    assert V_put >= intrinsic
