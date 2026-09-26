import sys

file_path = "Quantitative Strategy.md"
with open(file_path, "r") as f:
    content = f.read()

target = """Evaluate the trade at the close of each trading day $t_i$ ($i \in \{1, 2, 3\}$). Liquidate all open positions (option, stock hedge, and money market balance) if either condition is met:

1. **Sub-Intrinsic Value Decay Trigger ($i < 4$):**  
   If the theoretical continuation value of the option drops below its observable intrinsic value:
   $$V_i < \max(\phi \cdot (S_i - K), \, 0) \quad \text{where } \phi = 1 \text{ for Calls, } -1 \text{ for Puts}$$
   Liquidate the entire structure immediately on day $t_i$ to monetize the remaining edge and prevent adverse early assignment.
2. **Mandatory Terminal Settlement ($t_4$):**"""

replacement = """Evaluate the trade at the close of each trading day $t_i$ ($i \in \{1, 2, 3\}$). Liquidate all open positions (option, stock hedge, and money market balance) if any of the following conditions are met:

1. **Price Convergence Trigger ($i < 4$):**
   If the prevailing market price of the option ($C_i$) converges to or crosses the model's theoretical fair value ($V_i$) adjusted for remaining days to expiration:
   * **Scenario A (Short Option):** $C_i \le V_i$
   * **Scenario B (Long Option):** $C_i \ge V_i$
   Liquidate the entire structure immediately on day $t_i$ (by closing positions in the market) to lock in the captured arbitrage profit and eliminate unnecessary holding risk (e.g., gamma risk, financing fees).

2. **Sub-Intrinsic Value Decay Trigger ($i < 4$):**  
   If the theoretical option value drops below its observable intrinsic value:
   $$V_i < \max(\phi \cdot (S_i - K), \, 0) \quad \text{where } \phi = 1 \text{ for Calls, } -1 \text{ for Puts}$$
   *(Note: While mathematically impossible for American Calls on non-dividend paying stocks, this serves as a safeguard for deep ITM Puts).* Liquidate the entire structure immediately to prevent adverse early assignment.

3. **Mandatory Terminal Settlement ($t_4$):**"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)
