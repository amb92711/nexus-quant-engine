import random
import math
import concurrent.futures

class RiskEngine:
    """High-Performance Monte Carlo VaR & Expected Value Simulator"""
    
    @staticmethod
    def simulate_path(S, K, T, r, sigma, opt_type, premium, iterations):
        wins = 0
        total_profit = 0
        
        for _ in range(iterations):
            # Geometric Brownian Motion (GBM)
            Z = random.gauss(0, 1)
            ST = S * math.exp((r - 0.5 * sigma**2)*T + sigma * math.sqrt(T) * Z)
            
            payoff = max(0, ST - K) if opt_type == 'C' else max(0, K - ST)
            profit = payoff - premium
            
            if profit > 0:
                wins += 1
                total_profit += profit
                
        return wins, total_profit

    @staticmethod
    def parallel_monte_carlo(option, spot, total_iterations=100000):
        """Simulates 100k paths using Multi-Threading for Speed"""
        S = spot
        K = option['strike']
        T = option['dte'] / 365.0
        sigma = option['iv']
        premium = option['price']
        opt_type = option['type']
        
        threads = 10
        iters_per_thread = total_iterations // threads
        
        total_wins = 0
        total_pnl = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(RiskEngine.simulate_path, S, K, T, 0.05, sigma, opt_type, premium, iters_per_thread) for _ in range(threads)]
            for f in concurrent.futures.as_completed(futures):
                w, p = f.result()
                total_wins += w
                total_pnl += p
                
        pop = (total_wins / total_iterations) * 100
        ev = (total_pnl / total_iterations) - (premium * (total_iterations - total_wins) / total_iterations)
        
        return pop, ev
