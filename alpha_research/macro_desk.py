import time
from datetime import datetime
from quant_math.stochastics import DerivativesMath

class AlphaResearcher:
    """Analyzes GEX, Volatility Skew, and Microstructure"""
    def __init__(self, deribit_data, gateio_ob):
        self.deribit = deribit_data
        self.ob = gateio_ob
        self.btc_price = self.deribit[0].get('estimated_delivery_price', 0) if self.deribit else 0
        self.now_ts = time.time()
        
    def extract_institutional_flow(self):
        strikes_oi = {}
        gex_profile = {}
        puts_iv, calls_iv = [], []
        valid_options = []
        
        for s in self.deribit:
            inst = s['instrument_name']
            parts = inst.split('-')
            if len(parts) != 4: continue
            
            try:
                dte = (datetime.strptime(parts[1], "%d%b%y").timestamp() - self.now_ts) / 86400
            except: continue
            
            if dte <= 0.1: continue
            
            strike = float(parts[2])
            opt_type = parts[3]
            oi = s.get('open_interest', 0)
            iv = s.get('mark_iv', 0) / 100.0
            price_usd = s.get('mark_price', 0) * self.btc_price
            
            if oi > 0:
                strikes_oi[strike] = strikes_oi.get(strike, 0) + oi
                greeks = DerivativesMath.black_scholes_merton(self.btc_price, strike, dte/365.0, 0.05, iv, opt_type)
                
                # Market Maker Gamma Exposure
                contract_gex = greeks['gamma'] * oi * self.btc_price * (1 if opt_type=='C' else -1)
                gex_profile[strike] = gex_profile.get(strike, 0) + contract_gex
                
            if 1 < dte < 30:
                if opt_type == 'P' and strike < self.btc_price: puts_iv.append(iv)
                if opt_type == 'C' and strike > self.btc_price: calls_iv.append(iv)
                
            valid_options.append({'name': inst, 'type': opt_type, 'strike': strike, 'dte': dte, 'iv': iv, 'price': price_usd, 'greeks': greeks})

        # Calculations
        max_pain = max(strikes_oi, key=strikes_oi.get) if strikes_oi else self.btc_price
        skew = ((sum(puts_iv)/len(puts_iv) if puts_iv else 0) - (sum(calls_iv)/len(calls_iv) if calls_iv else 0)) * 100
        
        nearby = {k: v for k, v in gex_profile.items() if self.btc_price * 0.8 < k < self.btc_price * 1.2}
        pos_wall = max(nearby, key=nearby.get) if nearby else 0
        neg_wall = min(nearby, key=nearby.get) if nearby else 0
        
        # Orderbook Imbalance (Spoofing detection)
        bids = sum(float(b['s']) for b in self.ob.get('bids', []))
        asks = sum(float(a['s']) for a in self.ob.get('asks', []))
        imbalance = bids / asks if asks > 0 else 1
        
        return {
            'spot': self.btc_price, 'max_pain': max_pain, 'pos_gex_wall': pos_wall, 'neg_gex_wall': neg_wall,
            'skew': skew, 'ob_imbalance': imbalance, 'options': valid_options
        }
