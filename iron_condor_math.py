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

print("🦅 [ موتور کاندور آهنین (Iron Condor): حذفِ کاملِ جهتِ بازار ] 🦅\n")

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
    
    if not (1 <= dte <= 5): continue
    
    strike = float(parts[2])
    opt_type = parts[3]
    bid = (s.get('bid_price') or 0) * btc_price
    ask = (s.get('ask_price') or 0) * btc_price
    
    if bid > 0 and ask > 0:
        options.append({
            'name': inst, 'strike': strike, 'type': opt_type, 
            'dte': dte, 'bid': bid, 'ask': ask
        })

print(f"🪙 قیمت لایو: {btc_price:,.0f} دلار")
print("در حال ساختِ قفسِ دوطرفه (سود از رنج، محافظت در برابر پامپ و دامپ)...\n")

# پیدا کردن بهترین ستاپ سقف (Bear Call)
best_call_spread = None
for sell_c in [o for o in options if o['type'] == 'C' and o['strike'] >= btc_price * 1.02]:
    for buy_c in [o for o in options if o['type'] == 'C' and o['strike'] > sell_c['strike'] and o['dte'] == sell_c['dte']]:
        spread = buy_c['strike'] - sell_c['strike']
        if spread == 1500 or spread == 2000: # استاندارد
            credit = sell_c['bid'] - buy_c['ask']
            if credit > 5:
                best_call_spread = {'sell': sell_c, 'buy': buy_c, 'credit': credit, 'spread': spread, 'dte': sell_c['dte']}
                break
    if best_call_spread: break

# پیدا کردن بهترین ستاپ کف (Bull Put) برای همان تاریخ
best_put_spread = None
if best_call_spread:
    target_dte = best_call_spread['dte']
    for sell_p in [o for o in options if o['type'] == 'P' and o['strike'] <= btc_price * 0.98 and o['dte'] == target_dte]:
        for buy_p in [o for o in options if o['type'] == 'P' and o['strike'] < sell_p['strike'] and o['dte'] == target_dte]:
            spread = sell_p['strike'] - buy_p['strike']
            if spread == best_call_spread['spread']: # عرضِ اسپردها باید برابر باشد
                credit = sell_p['bid'] - buy_p['ask']
                if credit > 5:
                    best_put_spread = {'sell': sell_p, 'buy': buy_p, 'credit': credit, 'spread': spread}
                    break
        if best_put_spread: break

if best_call_spread and best_put_spread:
    vol = 0.05
    total_credit = (best_call_spread['credit'] + best_put_spread['credit']) * vol
    
    # باگِ جادوییِ مارجین: چون بیت‌کوین نمی‌تونه همزمان هم سقف رو بزنه هم کف رو، صرافی فقط مارجینِ یک طرف رو از ما می‌گیره!
    max_risk = (best_call_spread['spread'] * vol) - total_credit
    
    print(f"✅ [ تله‌ی ریاضی آماده شد: Iron Condor ]")
    print(f"انقضا: {best_call_spread['dte']:.1f} روز\n")
    
    print("قفسی که برای قیمت می‌سازیم:")
    print(f"   ⬆️ سقف قفس (مقاومت): {best_call_spread['sell']['strike']:,.0f}")
    print(f"   ⬇️ کف قفس (حمایت): {best_put_spread['sell']['strike']:,.0f}")
    print(f"   (فاصله‌ی آزادِ بیت‌کوین برای نوسان: {best_call_spread['sell']['strike'] - best_put_spread['sell']['strike']:,.0f} دلار!)\n")
    
    print("🛒 دستور اجرا (هر 4 اوردر را با حجم 0.05 بزنید):")
    print("   بخش اول (ساخت سقف):")
    print(f"      🔴 SELL -> {best_call_spread['sell']['name']}")
    print(f"      🟢 BUY  -> {best_call_spread['buy']['name']}")
    print("   بخش دوم (ساخت کف):")
    print(f"      🔴 SELL -> {best_put_spread['sell']['name']}")
    print(f"      🟢 BUY  -> {best_put_spread['buy']['name']}\n")
    
    print("⚖️ ترازوی قطعیِ ریاضی:")
    print(f"   💰 پول نقدِ دریافتی (Max Profit): +${total_credit:.2f} (این پول از هر دو طرف جمع شده!)")
    print(f"   🛡️ حداکثر ریسک (Max Risk): -${max_risk:.2f}")
    print("\n💡 چرا این یک باگِ ریاضی است؟")
    print("شما پولِ دو معامله را گرفته‌اید، اما چون قیمت نمی‌تواند هم سقف را بشکند هم کف را، شما فقط ریسکِ یک معامله را می‌پذیرید!")
    print("اگر بازار پامپ کند، سقف در ضرر می‌رود اما کف 100% سود می‌دهد و بالانس را حفظ می‌کند.")
else:
    print("در حال حاضر نقدینگی متقارن برای ساخت کاندور وجود ندارد.")
