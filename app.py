# ==========================================
# بوت رصد صفقات الحيتان - النسخة الكاملة
# يفحص كل اسهم S&P 500 ويرسل على تلجرام
# ==========================================

import yfinance as yf
import requests
import time
import pandas as pd
from datetime import datetime

# ===== 1. اعدادات تلجرام - غيرها ببياناتك =====
BOT_TOKEN = "ضع_توكن_البوت_هنا"  # مثلا: 123456:ABC-DEF1234ghIkl...
CHAT_ID = "ضع_ايدي_القناة_هنا"    # مثلا: -1001234567890 او @اسم_قناتك

# اذا ما تبي يرسل تلجرام، خليها False وبيطبع لك في الشاشة بس
SEND_TO_TELEGRAM = True

# ===== 2. شروط البوت - نفس شروط بوت القناة =====
MIN_PREMIUM = 50000       # اقل قيمة صفقة: 50 الف دولار
MIN_VOL_OI_RATIO = 1.5    # الفوليوم لازم يكون 1.5 ضعف الـ OI
MIN_VOLUME = 300          # اقل حجم تداول
MIN_PRICE = 0.5           # اقل سعر عقد
MAX_DAYS_TO_EXPIRY = 7    # بس العقود اللي تنتهي خلال 7 ايام
MAX_SIGNALS_PER_RUN = 10  # كم توصية يرسل في كل مرة
CHECK_EVERY_MINUTES = 60  # يفحص كل ساعة

# ===== 3. جلب كل اسهم S&P 500 =====
def get_sp500_tickers():
    try:
        # يجيب القائمة الحية من ويكيبيديا
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        tickers = table['Symbol'].tolist()
        # اصلاح رموز مثل BRK.B -> BRK-B عشان ياهو يفهمها
        tickers = [t.replace('.', '-') for t in tickers]
        print(f"تم جلب {len(tickers)} سهم من S&P 500")
        return tickers
    except Exception as e:
        print(f"ما قدرت اجيب قائمة S&P 500، بستخدم قائمة احتياطية: {e}")
        # قائمة احتياطية لاهم 100 سهم
        return [
            "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","BRK-B","AVGO","JPM",
            "LLY","V","MA","XOM","UNH","COST","HD","PG","JNJ","WMT","NFLX","CRM",
            "ORCL","BAC","CVX","ABBV","KO","TMO","CSCO","ACN","PEP","ADBE","MCD",
            "WFC","ABT","LIN","TXN","DHR","QCOM","AMGN","NKE","HON","IBM","GE",
            "CAT","UNP","VZ","PM","INTU","LOW","GS","MS","BLK","AMD","RTX","SPG",
            "NOW","ISRG","AMAT","BKNG","SYK","LRCX","ADI","MDT","GILD","ADP","MDLZ",
            "CHTR","REGN","VRTX","CSX","ATVI","MAR","PANW","KLAC","SNPS","CDNS",
            "BABA","TSLA","PLTR","COIN","GDX","SMCI","MU","MRVL","APP","HOOD"
        ]

# ===== 4. حساب الاهداف بنفس طريقة البوت =====
def get_targets(entry):
    return [
        round(entry * 1.25, 2),
        round(entry * 1.35, 2),
        round(entry * 1.50, 2),
        round(entry * 1.65, 2),
        round(entry * 1.75, 2),
        round(entry * 1.85, 2),
        round(entry * 1.90, 2),
        round(entry * 2.00, 2),
    ]

# ===== 5. ارسال رسالة تلجرام =====
def send_telegram(message):
    if not SEND_TO_TELEGRAM:
        print(message)
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"خطأ في ارسال تلجرام: {e}")

# ===== 6. فحص سهم واحد =====
def scan_ticker(symbol):
    results = []
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        stock_price = info.get('currentPrice') or info.get('regularMarketPrice')
        company = info.get('shortName', symbol)
        if not stock_price:
            return []

        expirations = ticker.options[:3]  # اقرب 3 تواريخ فقط للسرعة
        for exp in expirations:
            exp_date = datetime.strptime(exp, "%Y-%m-%d")
            days_left = (exp_date - datetime.now()).days
            if days_left < 0 or days_left > MAX_DAYS_TO_EXPIRY:
                continue

            try:
                chain = ticker.option_chain(exp)
            except:
                continue

            for opt_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                for _, row in df.iterrows():
                    vol = row['volume'] if pd.notna(row['volume']) else 0
                    oi = row['openInterest'] if pd.notna(row['openInterest']) else 0
                    price = row['lastPrice'] if pd.notna(row['lastPrice']) else 0

                    if vol < MIN_VOLUME or oi == 0 or price < MIN_PRICE:
                        continue

                    ratio = vol / oi
                    premium = vol * price * 100

                    # شرط الحوت
                    if ratio >= MIN_VOL_OI_RATIO and premium >= MIN_PREMIUM:
                        entry = round(float(price), 2)
                        stop = round(entry * 0.67, 2)
                        targets = get_targets(entry)
                        targets_str = " | ".join(map(str, targets))

                        # نوع الصفقة بالعربي
                        type_ar = "شراء CALL 🟢" if opt_type == "CALL" else "شراء PUT 🔴"

                        msg = (
                            f"🇺🇸 الأمريكي تحت المجهر\n"
                            f"{symbol} - {company}\n"
                            f"{type_ar}\n"
                            f"الانتهاء: {exp} ({days_left} يوم)\n"
                            f"السهم الآن: ${stock_price:.2f} | سترايك: {row['strike']}\n"
                            f"سعر التنفيذ: {entry} دولار للعقد (216 دولار تقريبا)\n"
                            f"الوقف: {stop} 🔴 | الكمية: {int(vol)} عقد\n"
                            f"قيمة الصفقة: ${int(premium):,}\n\n"
                            f"الأهداف بالترتيب 🎯\n"
                            f"{targets_str}\n\n"
                            f"إدارة الوقف ⚠️\n"
                            f"بعد الهدف الأول، ارفع الوقف إلى سعر الدخول. وبعد كل هدف جديد، ارفعه إلى سعر الهدف السابق.\n\n"
                            f"وقت التنفيذ: {datetime.now().strftime('%H:%M:%S')} SA\n"
                            f"رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."
                        )
                        results.append((premium, msg))
        return results
    except Exception as e:
        return []

# ===== 7. التشغيل الرئيسي - يفحص كل ساعة =====
def main_loop():
    tickers = get_sp500_tickers()
    print("البوت بدأ... بيفحص كل ساعة")
    send_telegram("✅ البوت اشتغل - ببدأ فحص كل اسهم S&P 500 كل ساعة")

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] جاري فحص {len(tickers)} سهم...")
        all_signals = []

        for i, sym in enumerate(tickers):
            if i % 50 == 0:
                print(f"فحصت {i}/{len(tickers)}...")
            signals = scan_ticker(sym)
            all_signals.extend(signals)

        # ترتيب من الاكبر قيمة للاصغر
        all_signals.sort(key=lambda x: x[0], reverse=True)

        if not all_signals:
            print("ما فيه صفقات حيتان تطابق الشروط هالساعة.")
        else:
            print(f"✅ لقيت {len(all_signals)} صفقة، برسل اقوى {MAX_SIGNALS_PER_RUN}")
            for _, msg in all_signals[:MAX_SIGNALS_PER_RUN]:
                send_telegram(msg)
                time.sleep(2)  # عشان تلجرام ما يحظرك

        print(f"انتظار {CHECK_EVERY_MINUTES} دقيقة للفحص القادم...")
        time.sleep(CHECK_EVERY_MINUTES * 60)

# ===== 8. تشغيل البوت =====
if __name__ == "__main__":
    # تثبيت المكتبات المطلوبة قبل اول تشغيل:
    # pip install yfinance pandas requests
    main_loop()
