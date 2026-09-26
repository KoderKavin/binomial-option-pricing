import numpy as np

class BinomialPricer:
    def __init__(self, S0, K, r, sigma, dt, N, q=0.0):
        self.S0 = S0
        self.K = K
        self.r = r
        self.sigma = sigma
        self.dt = dt
        self.N = N
        self.q = q
        
        self.u = np.exp(self.sigma * np.sqrt(self.dt))
        self.d = 1.0 / self.u
        self.p = (np.exp((self.r - self.q) * self.dt) - self.d) / (self.u - self.d)
        
    def price(self, right='C'):
        phi = 1 if right == 'C' else -1
        
        # Initialize terminal asset prices and option values
        S = np.zeros(self.N + 1)
        V = np.zeros(self.N + 1)
        
        for j in range(self.N + 1):
            S[j] = self.S0 * (self.u ** j) * (self.d ** (self.N - j))
            V[j] = max(phi * (S[j] - self.K), 0.0)
            
        # Delta at t=0
        delta = 0.0
            
        # Backward induction
        for i in range(self.N - 1, -1, -1):
            V_prev = np.zeros(i + 1)
            for j in range(i + 1):
                S_node = self.S0 * (self.u ** j) * (self.d ** (i - j))
                CV = np.exp(-self.r * self.dt) * (self.p * V[j + 1] + (1 - self.p) * V[j])
                IV = max(phi * (S_node - self.K), 0.0)
                V_prev[j] = max(CV, IV)
                
                # Calculate delta at t=0 using nodes at t=1
                if i == 0:
                    delta = (V[1] - V[0]) / (self.S0 * self.u - self.S0 * self.d)
                    
            V = V_prev
            
        return V[0], delta

def get_theoretical_price(S0, K, r, sigma, dt, N, right='C', q=0.0):
    pricer = BinomialPricer(S0, K, r, sigma, dt, N, q)
    return pricer.price(right)
