import urllib.request
import urllib.parse
import time
from datetime import datetime
from core_engine.council import QuantCouncil

# ==========================================
# تنظیمات شکارچی 24 ساعته
# ==========================================
BOT_TOKEN = "توکن_شما"
CHAT_ID = "آیدی_شما"
SCAN_INTERVAL_MINUTES = 15  # هر 15 دقیقه یک‌بار بازار را اسکن می‌کند

def send_telegram(text):
    if BOT_TOKEN == "توکن_شما":
        print("\n[تلگرام غیرفعال است] - پیام:\n" + text)
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}).encode('utf-8')
    try: urllib.request.urlopen(url, data=data, timeout=10)
    except: pass

def run_hunter():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🦅 شکارچی خاموش NEXUS فعال شد. در حال مانیتورینگ...")
    council = QuantCouncil()
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] در حال اسکن پنهان بازار...")
            result = council.execute_market_scan()
            
            if "error" in result:
                print("خطای موقت در دریافت دیتا. تلاش مجدد در دور بعدی.")
            
            elif result['status'] == "APPROVED":
                # فقط وقتی سیگنال 10/10 پیدا کرد به تلگرام پیام می‌دهد!
                macro = result['macro']
                opt = result['option']
                risk = result['risk']
                
                msg = f"🚨 *NEXUS-Q GOLDEN SETUP FOUND* 🚨\n"
                msg += f"================================\n\n"
                msg += f"صرافی یک آپشن را ارزان قیمت‌گذاری کرده است!\n\n"
                msg += f"🌐 *MACRO & GEX:*\n"
                msg += f"• Spot: `${macro['spot']:,.0f}`\n"
                msg += f"• Skew: `{macro['skew']:.2f}%`\n\n"
                
                msg += f"🎯 *ACTION REQUIRED (Demo):*\n"
                msg += f"• Buy Contract: `{opt['name']}`\n"
                msg += f"• Current Premium: `${opt['price']:,.2f}`\n\n"
                
                msg += f"🎲 *MATH VERIFICATION:*\n"
                msg += f"• Win Probability: `{risk['pop']:.1f}%`\n"
                msg += f"• Net Expected Value: `+${risk['ev']:,.2f}`\n\n"
                msg += "🟢 *EXECUTING TRADE IS STATISTICALLY PROFITABLE.*"
                
                send_telegram(msg)
                print("✅ سیگنال طلایی یافت شد و به تلگرام ارسال گردید!")
                
                # توقف 2 ساعته بعد از یافتن سیگنال برای جلوگیری از اسپم
                time.sleep(7200)
                continue
                
            else:
                print(f"وضعیت: {result['status']}. ارزش ریسک ندارد. سکوت...")
                
        except Exception as e:
            print(f"خطای سیستمی: {e}")
            
        # صبر برای دور بعدی اسکن
        time.sleep(SCAN_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_hunter()
