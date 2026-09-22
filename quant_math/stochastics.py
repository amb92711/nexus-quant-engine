import math

class DerivativesMath:
    """Advanced Stochastic Calculus & Greeks Engine"""
    @staticmethod
    def norm_cdf(x):
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    @staticmethod
    def norm_pdf(x):
        return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

    @staticmethod
    def black_scholes_merton(S, K, T, r, sigma, opt_type='C'):
        """Calculates Option Premium & First/Second Order Greeks"""
        if T <= 0 or sigma <= 0:
            return {'price': 0, 'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'vanna': 0}
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        gamma = DerivativesMath.norm_pdf(d1) / (S * sigma * math.sqrt(T))
        vega = S * DerivativesMath.norm_pdf(d1) * math.sqrt(T) / 100.0
        vanna = vega * (1 - d1 / (sigma * math.sqrt(T))) # 2nd Order Greek
        
        if opt_type == 'C':
            price = S * DerivativesMath.norm_cdf(d1) - K * math.exp(-r * T) * DerivativesMath.norm_cdf(d2)
            delta = DerivativesMath.norm_cdf(d1)
            theta = (- (S * DerivativesMath.norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * DerivativesMath.norm_cdf(d2)) / 365.0
        else:
            price = K * math.exp(-r * T) * DerivativesMath.norm_cdf(-d2) - S * DerivativesMath.norm_cdf(-d1)
            delta = DerivativesMath.norm_cdf(d1) - 1
            theta = (- (S * DerivativesMath.norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * DerivativesMath.norm_cdf(-d2)) / 365.0
            
        return {'price': price, 'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'vanna': vanna}
