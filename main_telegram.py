import urllib.request
import urllib.parse
from datetime import datetime
from core_engine.council import QuantCouncil

BOT_TOKEN = "توکن_ربات_شما"
CHAT_ID = "آیدی_شما"

def send_telegram(text):
    if BOT_TOKEN == "توکن_ربات_شما":
        print("\n" + text)
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}).encode('utf-8')
    try: urllib.request.urlopen(url, data=data, timeout=10)
    except: pass

def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 NEXUS-Q Enterprise Core Initializing...")
    council = QuantCouncil()
    result = council.execute_market_scan()
    
    if "error" in result:
        send_telegram(f"❌ *NEXUS CRITICAL ERROR*\n{result['error']}")
        return
        
    macro = result['macro']
    
    msg = f"🏛️ *NEXUS-Q INSTITUTIONAL DESK V2.0* 🏛️\n"
    msg += f"================================\n\n"
    msg += f"🌐 *1. MACRO & GEX DESK:*\n"
    msg += f"• Spot Price: `${macro['spot']:,.0f}`\n"
    msg += f"• Max Pain: `${macro['max_pain']:,.0f}`\n"
    msg += f"• GEX Resistance (Sell Wall): `${macro['pos_gex_wall']:,.0f}`\n"
    msg += f"• GEX Support (Buy Wall): `${macro['neg_gex_wall']:,.0f}`\n"
    msg += f"• Volatility Skew: `{macro['skew']:.2f}%` {'(Bearish)' if macro['skew'] > 0 else '(Bullish)'}\n\n"
    
    msg += f"🔬 *2. MICROSTRUCTURE DESK:*\n"
    msg += f"• Orderbook Imbalance: `{macro['ob_imbalance']:.2f}x`\n\n"
    
    if result['status'] == "STANDBY":
        msg += "🛑 *COUNCIL VERDICT: STANDBY*\nMarket is in absolute equilibrium. No edge detected."
    elif result['status'] == "NO_CONTRACT":
        msg += "⚠️ *COUNCIL VERDICT: NO CONTRACT*\nSetup found but Deribit lacks liquidity for this strike."
    else:
        opt = result['option']
        risk = result['risk']
        msg += f"🎲 *3. MONTE CARLO DESK (100,000 Paths):*\n"
        msg += f"• Contract: `{opt['name']}`\n"
        msg += f"• Premium: `${opt['price']:,.2f}`\n"
        msg += f"• Vanna (2nd Order Greek): `{opt['greeks']['vanna']:.4f}`\n"
        msg += f"• Probability of Profit: `{risk['pop']:.1f}%`\n"
        msg += f"• Expected Value (EV): `${risk['ev']:,.2f}`\n\n"
        
        if result['status'] == "APPROVED":
            msg += "🟢 *COUNCIL VERDICT: EXECUTE TRADE (10/10)*\n"
            msg += "Algorithm Confirmed: Positive Mathematical Expectancy."
        else:
            msg += "🔴 *COUNCIL VERDICT: REJECTED (OVERPRICED)*\n"
            msg += "Algorithm Confirmed: Negative Expected Value. Retail Trap."
            
    send_telegram(msg)

if __name__ == "__main__":
    run()
