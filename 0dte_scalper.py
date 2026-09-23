import urllib.request
import json
import time
from datetime import datetime

def fetch_api(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except: return None

print("⚡ [ موتور اسکالپ 0DTE (نوسان‌گیری چندساعته از آپشن‌های در حال مرگ) ] ⚡\n")

# 1. دریافت دیتای پرایس اکشن برای تعیین جهت و نوسان
candles_15m = fetch_api("https://api.gateio.ws/api/v4/futures/usdt/candlesticks?contract=BTC_USDT&interval=15m&limit=100")
if not candles_15m: exit()

closes = [float(c['c']) for c in candles_15m]
highs = [float(c['h']) for c in candles_15m]
lows = [float(c['l']) for c in candles_15m]

curr_p = closes[-1]
# پیدا کردن سقف و کف 12 ساعت گذشته برای تشخیص روند کوتاه‌مدت
local_top = max(highs[-48:-1])
local_bot = min(lows[-48:-1])

# 2. دریافت آپشن‌های دریبیت
deribit_data = fetch_api("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option")
summaries = deribit_data.get('result', []) if deribit_data else []
now_ts = time.time()

valid_options = []
for s in summaries:
    inst = s['instrument_name']
    parts = inst.split('-')
    if len(parts) != 4: continue
    
    try: dte = (datetime.strptime(parts[1], "%d%b%y").timestamp() - now_ts) / 86400
    except: continue
    
    # فیلتر حیاتی: فقط قراردادهایی که امروز یا فردا منقضی می‌شوند (0DTE تا 1DTE)
    if not (0 < dte <= 1.5): continue
    
    strike = float(parts[2])
    opt_type = parts[3]
    price_usd = s.get('mark_price', 0) * curr_p
    
    if price_usd > 5:
        valid_options.append({
            'name': inst, 'strike': strike, 'type': opt_type, 
            'dte': dte, 'price': price_usd
        })

print(f"🪙 قیمت لایو بیت‌کوین: {curr_p:,.0f} دلار")
print(f"   - مقاومت محلی: {local_top:,.0f} | حمایت محلی: {local_bot:,.0f}\n")

# 3. پیدا کردن بهترین ستاپ Diagonal Spread برای چند ساعت آینده
# استراتژی: فروش یک آپشن بسیار نزدیک به مارکت (گران) + خرید یک بیمه ارزان در همان تاریخ
best_setup = None
max_credit = 0

for sell_opt in valid_options:
    # می‌خواهیم آپشنی را بفروشیم که به قیمت مارکت نزدیک است (ATM) تا بیشترین پول را بگیریم
    if abs(sell_opt['strike'] - curr_p) / curr_p > 0.015: continue
    
    for buy_opt in valid_options:
        # بیمه‌نامه باید همان نوع و در همان تاریخ باشد، اما دورتر (OTM) و ارزان‌تر
        if sell_opt['dte'] != buy_opt['dte'] or sell_opt['type'] != buy_opt['type']: continue
        
        # اگر می‌فروشیم (Short)، باید بیمه را ارزان‌تر بخریم
        if buy_opt['price'] >= sell_opt['price'] * 0.5: continue
        
        if sell_opt['type'] == 'P' and buy_opt['strike'] < sell_opt['strike']:
            # Credit Put Spread (خوش‌بینانه)
            credit = sell_opt['price'] - buy_opt['price']
            risk = abs(sell_opt['strike'] - buy_opt['strike']) - credit
            
            if credit > max_credit and risk > 0:
                max_credit = credit
                best_setup = {'type': 'BULLISH', 'sell': sell_opt, 'buy': buy_opt, 'credit': credit, 'risk': risk}
                
        elif sell_opt['type'] == 'C' and buy_opt['strike'] > sell_opt['strike']:
            # Credit Call Spread (بدبینانه)
            credit = sell_opt['price'] - buy_opt['price']
            risk = abs(sell_opt['strike'] - buy_opt['strike']) - credit
            
            if credit > max_credit and risk > 0:
                max_credit = credit
                best_setup = {'type': 'BEARISH', 'sell': sell_opt, 'buy': buy_opt, 'credit': credit, 'risk': risk}

if best_setup:
    leg1 = best_setup['sell']
    leg2 = best_setup['buy']
    demo_qty = 0.01
    net_credit = best_setup['credit'] * demo_qty
    max_loss = best_setup['risk'] * demo_qty
    
    print(f"🔥 [ ستاپ اسکالپ 0DTE (درآمدزایی از افت زمان در چند ساعت) ] 🔥")
    print(f"   جهت استراتژی: {best_setup['type']} Credit Spread")
    print(f"   زمان تا انقضا: فقط {leg1['dte'] * 24:.1f} ساعت!\n")
    
    print(f"⚙️ *دستورالعمل اجرا در دمو (فقط آپشن، بدون فیوچرز):*")
    print(f"   🔴 1. SELL (فروش) -> {leg1['name']} | قیمت: ~${leg1['price']:,.0f}")
    print(f"   🟢 2. BUY  (خرید) -> {leg2['name']} | قیمت: ~${leg2['price']:,.0f}")
    
    print(f"\n⚖️ *ریاضیات پورتفو (حجم 0.01):*")
    print(f"   • پول دریافتی (Max Profit): +${net_credit:,.2f}")
    print(f"   • حداکثر ضرر قفل‌شده (Max Risk): -${max_loss:,.2f}")
    
    print(f"\n💡 *قانون خروج (چند ساعته):*")
    if best_setup['type'] == 'BULLISH':
        print(f"   - اگر بیت‌کوین بالای {leg1['strike']:,.0f} بماند، این بلیط‌ها تا امشب نابود می‌شوند و این سود مال شماست.")
    else:
        print(f"   - اگر بیت‌کوین زیر {leg1['strike']:,.0f} بماند، این بلیط‌ها تا امشب نابود می‌شوند و این سود مال شماست.")
    print("   - هر زمان در چند ساعت آینده مجموع حساب سبز شد (+1 تا +2 دلار)، دستی ببندید و خارج شوید.")
else:
    print("هیچ ستاپ مناسبی با انقضای امروز یا فردا یافت نشد.")
