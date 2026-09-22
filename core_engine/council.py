from data_feed.exchange_api import DataIngestion
from alpha_research.macro_desk import AlphaResearcher
from risk_management.monte_carlo import RiskEngine

class QuantCouncil:
    """The central brain where all desks vote on the execution."""
    def __init__(self):
        pass
        
    def execute_market_scan(self):
        # 1. Ingest Data
        deribit = DataIngestion.get_deribit_chain()
        gateio = DataIngestion.get_gateio_orderbook()
        
        if not deribit: return {"error": "L3 Data Feed Offline"}
        
        # 2. Process Alpha
        research_desk = AlphaResearcher(deribit, gateio)
        macro = research_desk.extract_institutional_flow()
        
        # 3. Council Voting Logic
        btc = macro['spot']
        pos_wall = macro['pos_gex_wall']
        neg_wall = macro['neg_gex_wall']
        skew = macro['skew']
        imbalance = macro['ob_imbalance']
        
        signal = None
        target_strike = 0
        
        if btc > pos_wall * 0.985:
            signal = 'P'
            target_strike = pos_wall
        elif btc < neg_wall * 1.015:
            signal = 'C'
            target_strike = neg_wall
            
        if not signal:
            return {"status": "STANDBY", "macro": macro, "reason": "Market in No-Trade Zone (Chop)."}
            
        # 4. Option Selection
        candidates = [o for o in macro['options'] if o['type'] == signal and 1 <= o['dte'] <= 7]
        candidates.sort(key=lambda x: abs(x['strike'] - target_strike))
        
        if not candidates:
            return {"status": "NO_CONTRACT", "macro": macro}
            
        best_opt = candidates[0]
        
        # 5. Risk Management (100k Monte Carlo Paths)
        pop, ev = RiskEngine.parallel_monte_carlo(best_opt, btc, total_iterations=100000)
        
        approval = "APPROVED" if (ev > 0 and pop > 35) else "REJECTED"
        
        return {
            "status": approval,
            "macro": macro,
            "option": best_opt,
            "risk": {"pop": pop, "ev": ev}
        }
