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

print("📅 [ ماشین Calendar Spread: سود از زمان، خنثی در برابر جهت ] 📅\n")

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
    
    strike = float(parts[2])
    opt_type = parts[3]
    bid = (s.get('bid_price') or 0) * btc_price
    ask = (s.get('ask_price') or 0) * btc_price
    mark = (s.get('mark_price') or 0) * btc_price
    
    options.append({
        'name': inst, 'strike': strike, 'type': opt_type, 
        'dte': dte, 'mark': mark, 'bid': bid, 'ask': ask
    })

print(f"🪙 قیمت لایو: {btc_price:,.0f} دلار")
print("در حال یافتن بهترین اختلاف زمانی (همان استرایک، تاریخ‌های متفاوت)...\n")

best_setup = None
max_theta_edge = 0

# پیدا کردن آپشن‌های کوتاه مدت (1 تا 3 روز) برای فروش
for short_opt in [o for o in options if 0.5 <= o['dte'] <= 3]:
    if short_opt['bid'] <= 5: continue
    
    # باید نزدیک به قیمت فعلی باشد (ATM) تا بیشترین افت زمانی را داشته باشد
    dist = abs(short_opt['strike'] - btc_price) / btc_price
    if dist > 0.05: continue 
    
    # پیدا کردن آپشن بلند مدت (7 تا 15 روز) برای خرید بیمه
    for long_opt in [o for o in options if 7 <= o['dte'] <= 15]:
        # استرایک و نوع آپشن باید دقیقاً و دقیقاً یکی باشد!
        if short_opt['strike'] != long_opt['strike'] or short_opt['type'] != long_opt['type']: continue
        if long_opt['ask'] <= 0: continue
        
        # در کلندر اسپرد، ما پول پرداخت می‌کنیم (Net Debit)، اما ضرر ما دقیقاً محدود به همین پول است
        vol = 0.01
        cost = (long_opt['ask'] - short_opt['bid']) * vol
        
        if cost > 0:
            # ما ستاپی می‌خواهیم که افتِ زمانیِ شورت خیلی سریع‌تر از افتِ لانگ باشد
            theta_edge = (short_opt['bid'] / short_opt['dte']) - (long_opt['ask'] / long_opt['dte'])
            if theta_edge > max_theta_edge:
                max_theta_edge = theta_edge
                best_setup = {
                    'short': short_opt,
                    'long': long_opt,
                    'cost': cost,
                    'vol': vol
                }

if best_setup:
    print(f"🔥 ستاپ Calendar Spread (خنثی‌سازِ جهت) 🔥")
    print(f"   استرایک قفل شده: {best_setup['short']['strike']:,.0f} ({'Call' if best_setup['short']['type'] == 'C' else 'Put'})")
    
    print(f"\n🛒 دستورات در صرافی (دقیقاً با حجم یکسان {best_setup['vol']}):")
    print(f"   🔴 1. SELL (فروشِ زودگذر): {best_setup['short']['name']} | انقضا: {best_setup['short']['dte']:.1f} روز | (دریافت ~${best_setup['short']['bid']*best_setup['vol']:.2f})")
    print(f"   🟢 2. BUY (خریدِ ماندگار): {best_setup['long']['name']}  | انقضا: {best_setup['long']['dte']:.1f} روز | (پرداخت ~${best_setup['long']['ask']*best_setup['vol']:.2f})")
    
    print(f"\n⚖️ ریاضیاتِ ضدگلوله:")
    print(f"   - هزینه راه‌اندازی (Max Risk): ${best_setup['cost']:.2f}")
    print(f"   - اگر بازار به شدت پامپ یا دامپ کند: استرایک‌ها برابرند، پس ضرر شما از این ${best_setup['cost']:.2f} بیشتر نخواهد شد!")
    print(f"   - اگر بازار رنج بزند یا حرکت کندی داشته باشد: آپشن اول (SELL) فردا بی‌ارزش می‌شود و پولش برای شماست، در حالی که آپشن دوم (BUY) هنوز 10 روز اعتبار دارد و می‌توانید آن را با قیمت خوبی بفروشید.")
else:
    print("ستاپ مناسبی یافت نشد.")
