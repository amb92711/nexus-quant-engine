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

print("⏳ [ موتور اسکالپ زمان (0DTE Scalper): شکار پوسیدگی درون‌روزی ] ⏳\n")

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
    
    # STRICT 0-1 DTE (We want MAX Theta decay)
    if not (0.1 <= dte <= 1.2): continue
    
    strike = float(parts[2])
    opt_type = parts[3]
    bid = (s.get('bid_price') or 0) * btc_price
    ask = (s.get('ask_price') or 0) * btc_price
    mark = (s.get('mark_price') or 0) * btc_price
    
    if mark > 2:
        options.append({
            'name': inst, 'strike': strike, 'type': opt_type, 
            'dte': dte, 'mark': mark, 'bid': bid, 'ask': ask
        })

print(f"🪙 قیمت لایو: {btc_price:,.0f} دلار")
print("جستجو برای ستاپ‌های 0DTE (خروج در چند ساعت)...\n")

best_setup = None
max_net_credit = 0

for sell_opt in options:
    if sell_opt['bid'] <= 0: continue
    
    # Must be reasonably close to the money to have high Theta, but safely OTM
    dist_pct = abs(sell_opt['strike'] - btc_price) / btc_price
    if dist_pct > 0.04 or dist_pct < 0.01: continue
    
    for buy_opt in options:
        if sell_opt['dte'] != buy_opt['dte'] or sell_opt['type'] != buy_opt['type']: continue
        if buy_opt['ask'] <= 0: continue
        
        if sell_opt['type'] == 'C' and buy_opt['strike'] <= sell_opt['strike']: continue
        if sell_opt['type'] == 'P' and buy_opt['strike'] >= sell_opt['strike']: continue
        
        # VERY TIGHT SPREAD to keep risk low and equal sizing (0.01) effective
        spread_dist = abs(sell_opt['strike'] - buy_opt['strike'])
        if spread_dist > 3000: continue
        
        vol = 0.01
        credit = (sell_opt['bid'] - buy_opt['ask']) * vol
        margin = spread_dist * vol
        
        if credit > 0.5: # At least 50 cents net credit on 0.01 size
            if credit > max_net_credit:
                max_net_credit = credit
                best_setup = {
                    'type': sell_opt['type'],
                    'sell': sell_opt,
                    'buy': buy_opt,
                    'credit': credit,
                    'risk': margin - credit,
                    'vol': vol
                }

if best_setup:
    print(f"🔥 ستاپ 0DTE (سود از گذر زمان در چند ساعت) 🔥")
    print(f"   نوع: {'Bear Call (مقاومت)' if best_setup['type'] == 'C' else 'Bull Put (حمایت)'}")
    print(f"   زمان تا انقضا: {best_setup['sell']['dte']*24:.1f} ساعت")
    
    print(f"\n🛒 دستورات (حجم مساوی):")
    print(f"   🔴 SELL: {best_setup['sell']['name']} (دریافت ~${best_setup['sell']['bid']*best_setup['vol']:.2f})")
    print(f"   🟢 BUY:  {best_setup['buy']['name']} (پرداخت ~${best_setup['buy']['ask']*best_setup['vol']:.2f})")
    
    print(f"\n💰 ریاضیات خالص (حجم {best_setup['vol']}):")
    print(f"   پریمیوم خالصِ شما: +${best_setup['credit']:.2f}")
    print(f"   حداکثر ریسک قفل شده: -${best_setup['risk']:.2f}")
    print(f"\n💡 قانون خروج: این معامله را باز کنید، 2-4 ساعت رها کنید. به محض اینکه برآیند کلی به 30-50% سود رسید، دکمه Close All را بزنید.")
else:
    print("ستاپ مناسبی یافت نشد.")
