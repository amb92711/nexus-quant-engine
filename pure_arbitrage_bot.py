import urllib.request
import urllib.parse
import json
import math
import time
from datetime import datetime

BOT_TOKEN = "توکن_شما"
CHAT_ID = "آیدی_شما"

def send_telegram(text):
    if BOT_TOKEN == "توکن_شما":
        print("\n[خروجی پایچارم]:\n" + text)
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}).encode('utf-8')
    try: urllib.request.urlopen(url, data=data, timeout=10)
    except: pass

def fetch_api(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except: return None

# توابع بلک-شولز
def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
def norm_pdf(x):
    return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)
def get_delta(S, K, T, r, sigma, opt_type):
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    return norm_cdf(d1) if opt_type == 'C' else norm_cdf(d1) - 1

def run_pure_arbitrage():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚙️ در حال اسکن برای آربیتراژ محض (بدون تحلیل جهت)...")
    
    deribit_data = fetch_api("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option")
    if not deribit_data: return "خطا در دریافت دیتا."
    summaries = deribit_data.get('result', [])
    
    btc_price = summaries[0].get('estimated_delivery_price', 86000)
    now_ts = time.time()
    
    # 1. پیدا کردن آپشن‌های 1 الی 3 روزه (برای اسکالپ سریعِ نوسان)
    short_term_options = []
    for s in summaries:
        inst = s['instrument_name']
        parts = inst.split('-')
        if len(parts) != 4: continue
        try: dte = (datetime.strptime(parts[1], "%d%b%y").timestamp() - now_ts) / 86400
        except: continue
        
        if not (1 <= dte <= 3): continue
        
        strike = float(parts[2])
        opt_type = parts[3]
        iv = s.get('mark_iv', 0) / 100.0
        price_usd = s.get('mark_price', 0) * btc_price
        
        # آپشن‌هایی که قیمتشان به بازار نزدیک است (ATM)
        if abs(strike - btc_price)/btc_price < 0.02 and iv > 0 and price_usd > 10:
            delta = get_delta(btc_price, strike, dte/365.0, 0.05, iv, opt_type)
            short_term_options.append({
                'name': inst, 'strike': strike, 'dte': dte, 'price': price_usd, 
                'type': opt_type, 'delta': delta, 'iv': iv*100
            })
            
    if not short_term_options:
        return "❌ هیچ آپشن کوتاه‌مدتِ مناسبی برای آربیتراژ یافت نشد."
        
    # انتخاب ارزان‌ترین آپشن برای شروع (بر اساس قیمت دلاری، نه جهت)
    short_term_options.sort(key=lambda x: x['price'])
    best_opt = short_term_options[0]
    
    demo_qty = 0.01
    position_delta = best_opt['delta'] * demo_qty
    hedge_action = "SHORT" if position_delta > 0 else "LONG"
    hedge_size = abs(position_delta)
    
    report = f"🤖 *NEXUS-Q PURE ARBITRAGE (NO-ANALYSIS MODE)* 🤖\n"
    report += f"=========================================\n\n"
    report += f"این سیستم هیچ پیش‌بینی‌ای از جهت بازار ندارد. فقط منتظر نوسان کورکورانه است.\n\n"
    
    report += f"🪙 *Spot Price:* `${btc_price:,.0f}`\n\n"
    
    report += f"⚙️ *MECHANICAL EXECUTION (اجرای ماشینی):*\n"
    report += f"1️⃣ *مرحله اول (خرید آپشن):*\n"
    report += f"   - Contract: `{best_opt['name']}`\n"
    report += f"   - Premium Cost (0.01 Size): `${(best_opt['price'] * demo_qty):,.2f}`\n\n"
    
    report += f"2️⃣ *مرحله دوم (هج کردن جهت در فیوچرز):*\n"
    report += f"   - Action: `{hedge_action} {hedge_size:.4f} BTC in Futures`\n"
    report += f"   - نتیجه: جهت بازار برای شما کاملاً بی‌اثر شد (Delta = 0).\n\n"
    
    report += f"🛑 *MECHANICAL RULES (قوانین خروج رباتیک):*\n"
    report += f"این دو معامله را در دمو باز کنید. هیچ تارگتی نگذارید.\n"
    report += f"• **تارگت سود (Take Profit):** هر زمان مجموع PnL آپشن + فیوچرز رسید به `+$3.00`، هردو را دستی ببندید.\n"
    report += f"• **استاپ ضرر (Time Decay Stop):** هر زمان مجموع PnL رسید به `-$2.00`، هردو را دستی ببندید.\n"
    report += f"*(نکته: شما دیگر منتظر تحلیل و رسیدن به مقاومت نیستید. شما فقط منتظرید که بازار هر جهتی دلش می‌خواهد برود تا ترازوی شما به هم بریزد و سود بدهد).* \n"
    
    return report

if __name__ == "__main__":
    final_report = run_pure_arbitrage()
    send_telegram(final_report)
