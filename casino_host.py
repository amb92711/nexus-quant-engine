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

print("🎰 [ موتور میزبان کازینو: فروشِ رویاها به تریدرهای خرد ] 🎰\n")

deribit_data = fetch_api("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option")
if not deribit_data:
    print("خطا در دریافت دیتا.")
    exit()

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
    
    # ما فقط بلیط‌هایی را می‌فروشیم که خیلی زود باطل شوند (1 تا 3 روز آینده)
    if not (1 <= dte <= 3): continue
    
    strike = float(parts[2])
    opt_type = parts[3]
    price_usd = s.get('mark_price', 0) * btc_price
    
    if price_usd > 1:
        options.append({
            'name': inst, 'strike': strike, 'type': opt_type, 
            'dte': dte, 'price': price_usd
        })

print(f"🪙 قیمت لایو بیت‌کوین: {btc_price:,.0f} دلار")
print("در حال پیدا کردنِ توهم‌آمیزترین شرط‌بندی‌های تریدرهای خرد برای فروش...\n")

best_setup = None
max_credit = 0

for sell_opt in options:
    # ماشین دنبال آپشن‌هایی می‌گردد که فاصله‌شان با قیمت خیلی زیاد است (غیرممکن به نظر می‌رسند) اما هنوز گران هستند!
    # مثلاً بازار 86 هزار است، اما پوت 78 هزار هنوز قیمتش بالاست.
    dist_pct = abs(sell_opt['strike'] - btc_price) / btc_price
    if dist_pct < 0.05: continue # خیلی نزدیک است، خطرناک است! باید حداقل 5 درصد فاصله داشته باشد.
    
    for buy_opt in options:
        if sell_opt['dte'] != buy_opt['dte'] or sell_opt['type'] != buy_opt['type']: continue
        
        # خرید بیمه باید دورتر از تارگتِ فروش باشد
        if sell_opt['type'] == 'P' and buy_opt['strike'] >= sell_opt['strike']: continue
        if sell_opt['type'] == 'C' and buy_opt['strike'] <= sell_opt['strike']: continue
        
        # بیمه باید ارزان باشد
        if buy_opt['price'] >= sell_opt['price'] * 0.4: continue
        
        # ما در این استراتژی حجم‌ها را برابر می‌گیریم (0.01 هر دو) تا ترازوی ریسک ثابت باشد (Credit Spread ساده)
        credit_received = sell_opt['price'] - buy_opt['price']
        max_loss = abs(sell_opt['strike'] - buy_opt['strike']) - credit_received
        
        # ما ستاپی می‌خواهیم که حداقل 5 دلار خالص به ما بدهد
        if credit_received > 5 and max_loss > 0:
            if credit_received > max_credit:
                max_credit = credit_received
                best_setup = {
                    'type': sell_opt['type'],
                    'sell': sell_opt,
                    'buy': buy_opt,
                    'credit': credit_received,
                    'max_loss': max_loss
                }

if best_setup:
    leg1 = best_setup['sell']
    leg2 = best_setup['buy']
    
    print(f"🥂 [ ستاپ کازینو: Credit Spread آماده‌ی سرو است ]")
    print(f"   شما شرط می‌بندید که یک اتفاقِ غیرممکن تا {leg1['dte']:.1f} روز آینده رخ نمی‌دهد.\n")
    
    print(f"⚙️ *اجرا در صرافی (دقیقاً با حجم مساوی):*")
    print(f"   🔴 1. SELL (فروش) -> `{leg1['name']}` | حجم: 0.01")
    print(f"      *(صرافی ${leg1['price']*0.01:,.2f} به حساب شما واریز می‌کند)*")
    
    print(f"   🟢 2. BUY  (خرید)  -> `{leg2['name']}` | حجم: 0.01")
    print(f"      *(شما برای بیمه شدن، ${leg2['price']*0.01:,.2f} پرداخت می‌کنید)*\n")
    
    print(f"⚖️ *ریاضیات کازینو:*")
    print(f"   • پول نقد قفل شده در جیب شما (Max Profit): +${best_setup['credit']*0.01:,.2f}")
    print(f"   • حداکثر ضرر مطلق در بدترین روز دنیا (Max Risk): -${best_setup['max_loss']*0.01:,.2f}")
    
    if best_setup['type'] == 'P':
        print(f"\n💡 *شرط پیروزیِ شما (آرامش مطلق):*")
        print(f"   کافیست بیت‌کوین تا {leg1['dte']:.1f} روز آینده، سقوطِ تاریخی نکند و بالای {leg1['strike']:,.0f} بماند.")
        print(f"   (مهم نیست پامپ کند یا رنج بزند، شما پولتان را می‌برید!)")
else:
    print("تریدرهای خرد الان توهمی ندارند. بلیطِ گرانی برای فروش به آن‌ها پیدا نشد.")
