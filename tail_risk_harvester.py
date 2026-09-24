import urllib.request
import json
import time
import math
from datetime import datetime

def fetch_api(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except: return None

def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def bs_delta(S, K, T, r, sigma, opt_type):
    if T <= 0 or sigma <= 0: return 0
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    return norm_cdf(d1) if opt_type == 'C' else norm_cdf(d1) - 1

print("🧛‍♂️ [ ماشین اخاذیِ روانی (Tail Risk Harvester): فروشِ توهمِ خالص ] 🧛‍♂️\n")

deribit_data = fetch_api("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option")
if not deribit_data: exit()

summaries = deribit_data.get('result', [])
btc_price = summaries[0].get('estimated_delivery_price', 86000)
now_ts = time.time()

options = []
for s in summaries:
    inst = s['instrument_name']
    parts = inst.split('-')
    if len(parts) != 4: continue
    try: dte = (datetime.strptime(parts[1], "%d%b%y").timestamp() - now_ts) / 86400
    except: continue
    
    if not (0.5 <= dte <= 4): continue # بلیط‌های کوتاه مدت که زود باطل بشن
    
    strike = float(parts[2])
    opt_type = parts[3]
    bid = (s.get('bid_price') or 0) * btc_price
    ask = (s.get('ask_price') or 0) * btc_price
    iv = s.get('mark_iv', 0) / 100.0
    
    if bid > 0 and ask > 0:
        delta = bs_delta(btc_price, strike, dte/365.0, 0.0, iv, opt_type)
        options.append({
            'name': inst, 'strike': strike, 'type': opt_type, 
            'dte': dte, 'bid': bid, 'ask': ask, 'delta': delta, 'iv': iv
        })

print(f"🪙 قیمت لایو: {btc_price:,.0f} دلار")
print("در حال جستجوی بلیط‌های لاتاری که احمق‌ها در حال خریدن آن هستند...\n")

best_setup = None
best_safety = 0

for sell_opt in options:
    # قانون اول: باید Deep OTM باشه. احتمال رسیدن قیمت بهش باید زیر 15% باشه (Delta < 0.15)
    # یعنی 85 درصد مواقع، این شرط‌بندی می‌بازه!
    if abs(sell_opt['delta']) > 0.15: continue
    
    # باید حداقل 1500 تا 2000 دلار با قیمت فعلی فاصله داشته باشه تا خوابمون راحت باشه
    dist = abs(sell_opt['strike'] - btc_price)
    if dist < 2000: continue
    
    for buy_opt in options:
        if sell_opt['dte'] != buy_opt['dte'] or sell_opt['type'] != buy_opt['type']: continue
        if sell_opt['type'] == 'C' and buy_opt['strike'] <= sell_opt['strike']: continue
        if sell_opt['type'] == 'P' and buy_opt['strike'] >= sell_opt['strike']: continue
        
        spread_dist = abs(sell_opt['strike'] - buy_opt['strike'])
        if spread_dist not in [1000, 1500, 2000, 3000]: continue # استرایک‌های رند و موجود
        
        premium_ratio = sell_opt['bid'] / buy_opt['ask']
        if premium_ratio < 1.5: continue
        
        net_credit_1_btc = sell_opt['bid'] - buy_opt['ask']
        if net_credit_1_btc <= 0: continue
        risk_1_btc = spread_dist - net_credit_1_btc
        
        # محاسبه حجم برای درگیر کردن حداکثر 100 دلار
        calculated_vol = 100.0 / risk_1_btc
        safe_vol = round(calculated_vol - 0.005, 2)
        if safe_vol < 0.01: continue
        
        credit = net_credit_1_btc * safe_vol
        risk = risk_1_btc * safe_vol
        
        if credit > 5:
            # امتیازدهی بر اساس: امنیت بالا (دلتا پایین) + سود معقول
            safety_score = (1 - abs(sell_opt['delta'])) * (credit / risk)
            if safety_score > best_safety:
                best_safety = safety_score
                best_setup = {
                    'type': sell_opt['type'],
                    'sell': sell_opt,
                    'buy': buy_opt,
                    'credit': credit,
                    'risk': risk,
                    'vol': safe_vol,
                    'prob_win': (1 - abs(sell_opt['delta'])) * 100
                }

if best_setup:
    dist_to_strike = abs(best_setup['sell']['strike'] - btc_price)
    print(f"✅ [ باگِ توهمِ بازار (Volatility Skew) کشف شد! ]")
    print(f"احتمال پیروزیِ ریاضیِ شما در این معامله: {best_setup['prob_win']:.1f} درصد! 🎯")
    print(f"نوع توهم: {'رویای پامپِ نجومی (Call)' if best_setup['type'] == 'C' else 'ترسِ سقوطِ آزاد (Put)'}")
    print(f"فاصله‌ی امنیتی: {dist_to_strike:,.0f} دلار از قیمتِ الان!\n")
    
    print(f"🛒 **نحوه‌ی اخاذی از خریداران (حجم {best_setup['vol']}):**")
    print(f"🔴 1. SELL -> {best_setup['sell']['name']} (شما رویایِ رسیدن به {best_setup['sell']['strike']:,.0f} را می‌فروشید!)")
    print(f"🟢 2. BUY  -> {best_setup['buy']['name']} (بیمه برای آخرالزمان)")
    
    print(f"\n⚖️ **ترازوی نهایی (ریسک زیر 100 دلار):**")
    print(f"💰 پولِ یا مفتِ دریافتی (Max Profit): +${best_setup['credit']:.2f}")
    print(f"🛡️ حداکثر ریسک قفل شده: -${best_setup['risk']:.2f}")
else:
    print("❌ در حال حاضر احمق‌ها پولی در بازار خرج نمی‌کنند. باید صبر کنیم.")
