import urllib.request
import urllib.parse
import json
import math
import time
from datetime import datetime
from alpha_signals.max_pain_gex.nexus_core_brain import DataIngestion, MathEngine, MonteCarloRiskDesk

BOT_TOKEN = "توکن_شما"
CHAT_ID = "آیدی_شما"

def send_telegram(text):
    if BOT_TOKEN == "توکن_شما":
        print("\n[خروجی ترمینال پایچارم]:\n" + text)
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}).encode('utf-8')
    try: urllib.request.urlopen(url, data=data, timeout=10)
    except: pass

class AdvancedVolatilityDesk:
    """Detects Implied Volatility Surface Anomalies (Volatility Arbitrage)"""
    def __init__(self, summaries):
        self.summaries = summaries
        self.btc = summaries[0].get('estimated_delivery_price', 0) if summaries else 0
        self.now_ts = time.time()
        
    def find_volatility_anomalies(self):
        puts, calls = [], []
        
        # استخراج دیتای تمام قراردادهای 1 تا 7 روزه
        for s in self.summaries:
            parts = s['instrument_name'].split('-')
            if len(parts) != 4: continue
            try: dte = (datetime.strptime(parts[1], "%d%b%y").timestamp() - self.now_ts) / 86400
            except: continue
            
            if not (1 <= dte <= 7): continue
            
            strike = float(parts[2])
            iv = s.get('mark_iv', 0)
            if iv == 0: continue
            
            opt_data = {'name': s['instrument_name'], 'strike': strike, 'dte': dte, 'iv': iv, 
                        'price': s.get('mark_price', 0)*self.btc, 'type': parts[3]}
            if parts[3] == 'P' and self.btc * 0.8 < strike < self.btc: puts.append(opt_data)
            if parts[3] == 'C' and self.btc < strike < self.btc * 1.2: calls.append(opt_data)
                
        # پیدا کردن میانگین نوسانات (IV) برای پیدا کردن ناهنجاری آماری
        avg_put_iv = sum(p['iv'] for p in puts) / len(puts) if puts else 1
        avg_call_iv = sum(c['iv'] for c in calls) / len(calls) if calls else 1
        
        # ارزان‌ترین آپشن‌ها نسبت به میانگین بازار (آربیتراژ نوسان)
        underpriced_puts = [p for p in puts if p['iv'] < avg_put_iv * 0.9]
        underpriced_calls = [c for c in calls if c['iv'] < avg_call_iv * 0.9]
        
        underpriced_puts.sort(key=lambda x: x['iv'])
        underpriced_calls.sort(key=lambda x: x['iv'])
        
        return underpriced_puts, underpriced_calls

class DeltaNeutralHedger:
    """Calculates the exact Futures Short/Long hedge to isolate Gamma"""
    @staticmethod
    def calculate_hedge(option, btc_price, opt_quantity=0.01):
        # 1. محاسبه یونانی‌ها با بلک-شولز
        greeks = MathEngine.black_scholes_greeks(btc_price, option['strike'], option['dte']/365.0, 0.05, option['iv']/100.0, option['type'])
        delta = greeks['delta']
        
        # 2. محاسبه موقعیت خنثی
        # اگر آپشن خریده شده دلتای 0.45 دارد و سایز 0.01 است، دلتای کل پوزیشن 0.0045+ است.
        # برای خنثی کردن آن، باید 0.0045 بیت‌کوین شورت شود.
        position_delta = delta * opt_quantity
        hedge_action = "SHORT (فروش)" if position_delta > 0 else "LONG (خرید)"
        hedge_size = abs(position_delta)
        
        return greeks, hedge_action, hedge_size

def run_enterprise_engine():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧪 در حال اجرای موتور پیشرفته آربیتراژ نوسان و دلتا-خنثی...")
    summaries = DataIngestion.fetch_deribit_chain()
    if not summaries: return
    
    vol_desk = AdvancedVolatilityDesk(summaries)
    puts, calls = vol_desk.find_volatility_anomalies()
    btc = vol_desk.btc
    
    # انتخاب بهترین ناهنجاری
    if calls and puts:
        best_anomaly = calls[0] if calls[0]['iv'] < puts[0]['iv'] else puts[0]
    elif calls: best_anomaly = calls[0]
    elif puts: best_anomaly = puts[0]
    else:
        send_telegram("💤 بازار کاملاً کارا (Efficient) است. هیچ ناهنجاری قیمتی برای آربیتراژ یافت نشد.")
        return

    # محاسبه هجینگ دلتا-خنثی برای سایز دمو (0.01 BTC)
    demo_qty = 0.01
    greeks, h_action, h_size = DeltaNeutralHedger.calculate_hedge(best_anomaly, btc, demo_qty)
    
    # فیلتر مونت کارلو
    pop, ev = MonteCarloRiskDesk.simulate_trade(best_anomaly, btc)
    
    report = f"🏛️ *NEXUS-Q ENTERPRISE: VOLATILITY ARBITRAGE* 🏛️\n"
    report += f"====================================\n\n"
    report += f"🎯 *1. ناهنجاری آماری کشف شد (Anomaly Detected):*\n"
    report += f"صرافی این آپشن را ارزان‌تر از ارزش واقعی‌اش قیمت‌گذاری کرده است!\n"
    report += f"🔖 قرارداد: `{best_opt_name := best_anomaly['name']}`\n"
    report += f"📉 نوسان ضمنی (IV): `{best_anomaly['iv']:.1f}%` (بسیار پایین‌تر از میانگین مارکت)\n"
    report += f"💸 قیمت بلیط: `${best_anomaly['price']:,.2f}`\n\n"
    
    report += f"⚖️ *2. هجینگ دلتا-خنثی (Delta-Neutral Strategy):*\n"
    report += f"شما با این استراتژی، جهتِ بازار (بالا/پایین) را بی‌اثر می‌کنید و فقط از گاما سود می‌برید.\n"
    report += f"• **گام اول:** خرید آپشن بالا با حجم `{demo_qty}` (ریسک: `${(best_anomaly['price']*demo_qty):,.2f}`)\n"
    report += f"• **گام دوم:** همزمان در فیوچرز بایننس یا دریبیت، مقدار `{h_size:.4f}` بیت‌کوین را `{h_action}` کنید.\n"
    report += f"*(با این کار، سود/ضرر جهت‌دار شما صفر می‌شود. فقط کافیست بازار نوسان کند تا گامای شما منفجر شود!)*\n\n"
    
    report += f"🎲 *3. اعتبارسنجی مونت-کارلو (Risk Check):*\n"
    report += f"• شانس برد (POP): `{pop:.1f}%`\n"
    report += f"• امید ریاضی خالص (EV): `${ev:,.2f}`\n\n"
    
    if ev > 0:
        report += "🟢 *نتیجه‌گیری: استراتژی آربیتراژ و هجینگ با موفقیت تایید شد.*"
    else:
        report += "🔴 *نتیجه‌گیری: با وجود ارزان بودن، امید ریاضی مثبت نیست.*"

    send_telegram(report)

if __name__ == "__main__":
    run_enterprise_engine()
    print("✅ پردازش تمام شد.")
