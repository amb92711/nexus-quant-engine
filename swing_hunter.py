import urllib.request
import urllib.parse
import json
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

def run_swing_analysis():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔭 در حال محاسبه زمان دقیقِ رسیدن به تارگت (Kinematic Time Prediction)...")
    
    # دیتای کندل روزانه برای محاسبه قدرت حرکت روزانه (Daily ATR)
    candles_1d = fetch_api("https://api.gateio.ws/api/v4/futures/usdt/candlesticks?contract=BTC_USDT&interval=1d&limit=30")
    if not candles_1d: return "خطا در دریافت دیتای روزانه."
    
    closes_1d = [float(c['c']) for c in candles_1d]
    highs_1d = [float(c['h']) for c in candles_1d]
    lows_1d = [float(c['l']) for c in candles_1d]
    
    # محاسبه میانگین حرکت واقعی روزانه (Daily ATR) برای 14 روز گذشته
    trs_1d = [max(highs_1d[k]-lows_1d[k], abs(highs_1d[k]-closes_1d[k-1]), abs(lows_1d[k]-closes_1d[k-1])) for k in range(len(closes_1d)-14, len(closes_1d))]
    daily_atr = sum(trs_1d) / 14
    curr_p = closes_1d[-1]
    
    # دیتای کندل 4 ساعته برای سطوح
    candles_4h = fetch_api("https://api.gateio.ws/api/v4/futures/usdt/candlesticks?contract=BTC_USDT&interval=4h&limit=100")
    closes_4h = [float(c['c']) for c in candles_4h]
    highs_4h = [float(c['h']) for c in candles_4h]
    lows_4h = [float(c['l']) for c in candles_4h]
    
    macro_top = max(highs_4h[-100:-1])
    macro_bot = min(lows_4h[-100:-1])
    ema_50 = sum(closes_4h[-50:]) / 50
    
    deribit_data = fetch_api("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option")
    summaries = deribit_data.get('result', []) if deribit_data else []
    now_ts = time.time()
    
    calls_vol = 0
    puts_vol = 0
    valid_options = []
    
    for s in summaries:
        inst = s['instrument_name']
        parts = inst.split('-')
        if len(parts) != 4: continue
        
        try: dte = (datetime.strptime(parts[1], "%d%b%y").timestamp() - now_ts) / 86400
        except: continue
        
        if dte <= 0: continue
        
        strike = float(parts[2])
        opt_type = parts[3]
        oi = s.get('open_interest', 0)
        price_usd = s.get('mark_price', 0) * curr_p
        
        if opt_type == 'C' and curr_p < strike < curr_p * 1.2: calls_vol += oi
        elif opt_type == 'P' and curr_p * 0.8 < strike < curr_p: puts_vol += oi
            
        valid_options.append({
            'name': inst, 'type': opt_type, 'strike': strike, 
            'dte': dte, 'price': price_usd, 'oi': oi
        })
        
    sentiment = calls_vol / puts_vol if puts_vol > 0 else 1
    
    direction = "WAIT"
    target_strike = curr_p
    
    if curr_p > ema_50 and sentiment > 1.2:
        direction = "LONG"
        target_strike = macro_top if macro_top > curr_p * 1.02 else curr_p * 1.05
    elif curr_p < ema_50 and sentiment < 0.8:
        direction = "SHORT"
        target_strike = macro_bot if macro_bot < curr_p * 0.98 else curr_p * 0.95
    else:
        # برای تست قابلیت جدید در چت، یک سیگنال آزمایشی ایجاد میکنیم اگر بازار رنج بود
        direction = "LONG_TEST"
        target_strike = curr_p + (daily_atr * 3)

    # ---------------------------------------------------------
    # جادوی جدید کوانت: محاسبه سینماتیک زمان تا تارگت
    # ---------------------------------------------------------
    distance_to_target = abs(target_strike - curr_p)
    expected_days_to_target = distance_to_target / daily_atr if daily_atr > 0 else 1
    
    # فرمول هج‌فاند: زمان انقضای آپشن = زمان مورد انتظار + 50٪ فضای تنفس (بافر)
    optimal_dte = expected_days_to_target * 1.5
    optimal_dte = max(2, optimal_dte) # حداقل 2 روز
    
    report = f"🔭 *NEXUS-Q DYNAMIC DTE PREDICTOR* 🔭\n"
    report += f"====================================\n\n"
    report += f"📊 *Price Action & Momentum:*\n"
    report += f"• Spot Price: `${curr_p:,.0f}`\n"
    report += f"• Target Price: `${target_strike:,.0f}`\n"
    report += f"• Daily Avg Move (ATR): `${daily_atr:,.0f}` per day\n\n"
    
    report += f"⏱️ *Kinematic Time Calculation:*\n"
    report += f"• Distance to Target: `${distance_to_target:,.0f}`\n"
    report += f"• Expected Time to Reach Target: `{expected_days_to_target:.1f} Days`\n"
    report += f"• Optimal Option Expiry (with 50% safety buffer): `{optimal_dte:.1f} Days`\n\n"
    
    if direction == "WAIT":
        report += "🛑 *VERDICT:* Chop Zone. No trades today."
        return report

    opt_type = 'C' if "LONG" in direction else 'P'
    
    # فیلتر آپشن‌ها: پیدا کردن قراردادی که تاریخ انقضایش دقیقاً با Optimal DTE ماشین همخوانی دارد
    opts = [o for o in valid_options if o['type'] == opt_type and o['dte'] >= optimal_dte and abs(o['strike'] - target_strike)/target_strike < 0.05]
    opts.sort(key=lambda x: (x['dte'] - optimal_dte)**2) # نزدیک‌ترین زمان به زمان ایده‌آل
    
    if not opts:
        return report + "❌ قراردادی با این تاریخ انقضای دقیق در صرافی یافت نشد."
        
    best_opt = opts[0]
    
    report += f"🎯 *ENGINEERED OPTION SETUP:*\n"
    report += f"ماشین دقیقاً قراردادی را پیدا کرد که با سرعت حرکت بازار همخوانی دارد.\n"
    report += f"• Contract: `{best_opt['name']}`\n"
    report += f"• Actual Time to Expire: `{best_opt['dte']:.1f} Days`\n"
    report += f"• Premium Cost: `${best_opt['price']:,.2f}`\n\n"
    report += f"💡 *Exit Rule:* The math expects the target to be hit in {expected_days_to_target:.1f} days. If not hit by then, close manually."
    
    return report

if __name__ == "__main__":
    final_report = run_swing_analysis()
    send_telegram(final_report)
