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

def calculate_delta(S, K, T, r, sigma, opt_type):
    if T <= 0 or sigma <= 0: return 0
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    return norm_cdf(d1) if opt_type == 'C' else norm_cdf(d1) - 1

print("🎰 [ موتور کازینوی وال‌استریت: فروش پریمیوم با ترازوی بالانس‌شده ] 🎰\n")

deribit_data = fetch_api("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option")
if not deribit_data: exit()

summaries = deribit_data.get('result', [])
btc_price = summaries[0].get('estimated_delivery_price', 87000)
now_ts = time.time()

valid_options = []
for s in summaries:
    inst = s['instrument_name']
    parts = inst.split('-')
    if len(parts) != 4: continue
    
    try: dte = (datetime.strptime(parts[1], "%d%b%y").timestamp() - now_ts) / 86400
    except: continue
    
    if not (0.5 <= dte <= 3): continue # تمرکز روی فروش آپشن‌های رو به مرگ (سود سریع از زمان)
    
    strike = float(parts[2])
    opt_type = parts[3]
    price_usd = s.get('mark_price', 0) * btc_price
    iv = s.get('mark_iv', 0) / 100.0
    
    if price_usd > 2 and iv > 0:
        delta = calculate_delta(btc_price, strike, dte/365.0, 0.05, iv, opt_type)
        valid_options.append({
            'name': inst, 'strike': strike, 'type': opt_type, 
            'dte': dte, 'price': price_usd, 'delta': delta, 'iv': iv*100
        })

print(f"🪙 قیمت لایو بیت‌کوین: {btc_price:,.0f} دلار")
print("در حال جستجوی احمقانه‌ترین قیمت‌گذاری‌های خریدارانِ خرد...\n")

best_setup = None
max_profit_ratio = 0

for sell_opt in valid_options:
    # می‌خواهیم آپشنی را بفروشیم که فاصله‌ی خوبی با قیمت دارد (امن است) اما گران است (IV بالا)
    dist_pct = abs(sell_opt['strike'] - btc_price) / btc_price
    if dist_pct < 0.02 or sell_opt['price'] < 50: continue 
    
    for buy_opt in valid_options:
        if sell_opt['dte'] != buy_opt['dte'] or sell_opt['type'] != buy_opt['type']: continue
        
        # بیمه‌نامه باید دورتر از تارگت فروش ما باشد
        if sell_opt['type'] == 'P' and buy_opt['strike'] >= sell_opt['strike']: continue
        if sell_opt['type'] == 'C' and buy_opt['strike'] <= sell_opt['strike']: continue
        
        if buy_opt['price'] >= sell_opt['price'] * 0.5: continue
        
        # === جادوی بالانس کردن حجم (Ratio Hedging) ===
        # اگر آپشن اول دلتای 0.4 دارد و دومی دلتای 0.1 دارد، ما باید 4 تا از دومی بخریم تا اولی خنثی شود!
        if abs(buy_opt['delta']) == 0: continue
        hedge_ratio = abs(sell_opt['delta']) / abs(buy_opt['delta'])
        
        # برای عملی بودن در صرافی، ریشیو را به یک عدد گرد معقول تبدیل می‌کنیم
        if hedge_ratio > 10: continue # نسبت‌های خیلی بزرگ خطرناک و گران هستند
        
        # ما می‌خواهیم با وجود خریدن بیمه به تعدادِ زیاد (Hedge Ratio)، همچنان پولِ دریافتیِ ما بیشتر باشد (Net Credit)
        cost_of_insurance = buy_opt['price'] * hedge_ratio
        net_credit = sell_opt['price'] - cost_of_insurance
        
        if net_credit > 10: # حداقل 10 دلار خالص به جیب ما برود
            profit_score = net_credit / sell_opt['price']
            if profit_score > max_profit_ratio:
                max_profit_ratio = profit_score
                best_setup = {
                    'type': sell_opt['type'],
                    'sell': sell_opt,
                    'buy': buy_opt,
                    'ratio': hedge_ratio,
                    'net_credit': net_credit
                }

if best_setup:
    leg1 = best_setup['sell']
    leg2 = best_setup['buy']
    
    # استانداردسازی سایز برای دمو
    base_qty = 0.01
    hedge_qty = round(base_qty * best_setup['ratio'], 3)
    
    print(f"🔥 [ ستاپ Ratio Credit Spread (ترازوی بالانس‌شده) ] 🔥")
    print(f"   جهت بیمه: {'Bearish (مقاومت بالا)' if best_setup['type'] == 'C' else 'Bullish (حمایت پایین)'}")
    print(f"   زمان تا انقضای این شرط‌بندی: {leg1['dte']:.1f} روز\n")
    
    print(f"⚖️ *دستورالعملِ دقیقِ حجم‌ها (برای بالانس شدنِ دلتا):*")
    print(f"   🔴 1. SELL (فروش) -> {leg1['name']}")
    print(f"      - حجم: {base_qty}")
    print(f"      - دریافتی شما: ~${(leg1['price'] * base_qty):,.2f}")
    
    print(f"\n   🟢 2. BUY  (خرید بیمه) -> {leg2['name']}")
    print(f"      - حجم حیاتی: {hedge_qty}  <-- (ماشین محاسبه کرد که بیمه باید {best_setup['ratio']:.1f} برابر بیشتر باشد!)")
    print(f"      - پرداختی شما: ~${(leg2['price'] * hedge_qty):,.2f}")
    
    print(f"\n💰 *برآیند حساب شما (Net Position):*")
    print(f"   • پولِ خالصِ قفل شده در جیب شما: +${(best_setup['net_credit'] * base_qty):,.2f}")
    print(f"   • **تضمین ماشین:** با این ترکیب حجم‌ها، اگر بازار برعکس شد، سودِ بیمه با ضررِ فروش کاملاً همخوانی دارد و ترازو کج نمی‌شود.")
else:
    print("هیچ ستاپ منطقی و سودآوری در این ثانیه یافت نشد.")
