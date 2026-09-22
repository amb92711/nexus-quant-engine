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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔭 در حال اسکن بازار برای روندهای چند روزه...")
    
    # دیتای کندل 4 ساعته برای روند کلان
    candles_4h = fetch_api("https://api.gateio.ws/api/v4/futures/usdt/candlesticks?contract=BTC_USDT&interval=4h&limit=100")
    if not candles_4h: return "خطا در دریافت دیتای 4 ساعته."
    
    closes = [float(c['c']) for c in candles_4h]
    highs = [float(c['h']) for c in candles_4h]
    lows = [float(c['l']) for c in candles_4h]
    
    curr_p = closes[-1]
    macro_top = max(highs[-100:-1])
    macro_bot = min(lows[-100:-1])
    ema_50 = sum(closes[-50:]) / 50
    
    # دیتای آپشن دریبیت برای رهگیری نهنگ‌ها (7 تا 30 روز آینده)
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
        
        # فقط قراردادهای 7 تا 30 روزه برای Swing Trading
        if not (7 <= dte <= 30): continue
        
        strike = float(parts[2])
        opt_type = parts[3]
        oi = s.get('open_interest', 0)
        price_usd = s.get('mark_price', 0) * curr_p
        
        # محاسبه حجم شرط‌بندی‌های نزدیک به قیمت
        if opt_type == 'C' and curr_p < strike < curr_p * 1.2: calls_vol += oi
        elif opt_type == 'P' and curr_p * 0.8 < strike < curr_p: puts_vol += oi
            
        valid_options.append({
            'name': inst, 'type': opt_type, 'strike': strike, 
            'dte': dte, 'price': price_usd, 'oi': oi
        })
        
    sentiment = calls_vol / puts_vol if puts_vol > 0 else 1
    
    report = f"🔭 *NEXUS-Q MACRO SWING DESK* 🔭\n"
    report += f"================================\n\n"
    report += f"📊 *Price Action (4H):*\n"
    report += f"• Spot: `${curr_p:,.0f}`\n"
    report += f"• Macro Top: `${macro_top:,.0f}`\n"
    report += f"• EMA50 (Trend): `${ema_50:,.0f}`\n\n"
    
    report += f"🐋 *Whale Sentiment (7-30 Days out):*\n"
    report += f"• Call/Put Ratio: `{sentiment:.2f}x`\n"
    report += f"• Status: {'Bullish Accumulation' if sentiment > 1.2 else 'Bearish Distribution' if sentiment < 0.8 else 'Neutral Indecision'}\n\n"
    
    direction = "WAIT"
    target_strike = curr_p
    
    # الگوریتم تایید دوگانه (پرایس اکشن + پول نهنگ‌ها)
    if curr_p > ema_50 and sentiment > 1.2:
        direction = "LONG"
        target_strike = macro_top if macro_top > curr_p * 1.02 else curr_p * 1.05
    elif curr_p < ema_50 and sentiment < 0.8:
        direction = "SHORT"
        target_strike = macro_bot if macro_bot < curr_p * 0.98 else curr_p * 0.95
    
    if direction == "WAIT":
        report += "🛑 *FINAL VERDICT: WAIT (CHOP ZONE)*\n"
        report += "Reason: Market trend and Whale options flow do NOT align. High risk of premium decay. Cash is a position."
        return report
        
    opt_type = 'C' if direction == "LONG" else 'P'
    
    # پیدا کردن بهترین آپشن: ارزان‌ترین آپشنی که حجم باز خوبی دارد و استرایک آن به تارگت نزدیک است
    opts = [o for o in valid_options if o['type'] == opt_type and o['oi'] > 10 and abs(o['strike'] - target_strike)/target_strike < 0.05]
    opts.sort(key=lambda x: x['price'])
    
    if not opts:
        return report + "❌ قرارداد نقدشونده‌ای در این محدوده یافت نشد."
        
    best_opt = opts[0]
    
    report += f"🟢 *FINAL VERDICT: CLEAR DIRECTION DETECTED*\n"
    report += f"• Trend: `{direction} (Multi-Day)`\n"
    report += f"• Target: `${target_strike:,.0f}`\n\n"
    
    report += f"🎯 *NAKED OPTION SETUP (No Hedging needed):*\n"
    report += f"• Contract: `{best_opt['name']}`\n"
    report += f"• Premium Cost: `${best_opt['price']:,.2f}`\n"
    report += f"• Time to Expire: `{best_opt['dte']:.1f} Days`\n\n"
    report += f"💡 *Exit Strategy:* Close manually when profit hits +100% or trend breaks EMA50. DO NOT hold to expiration."
    
    return report

if __name__ == "__main__":
    final_report = run_swing_analysis()
    send_telegram(final_report)
