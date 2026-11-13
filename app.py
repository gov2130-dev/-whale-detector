# ============================================================
# راصد الحيتان - V6 النسخة الكاملة النهائية
# - 150 سهم
# - يشتغل السوق فاتح أو مسكر
# - توصيات فقط، بدون جدول
# - بريميوم حقيقي من الأوبشن تشين، ونطاق نسبي حسب سعر السهم
# - إرسال واتساب CallMeBot مع تنظيف الرقم تلقائيا
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, time
import pytz

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("🔍 راصد الحيتان")

# ============================================================
# 1. إعدادات الواتساب - حطها في Secrets
# ============================================================
# في Streamlit -> Settings -> Secrets حط:
# CALLMEBOT_PHONE = "966551234567"  بدون + وبدون مسافات وبدون 0
# CALLMEBOT_APIKEY = "123456"  الكود اللي يرسله لك CallMeBot
# عشان تفعل CallMeBot: ارسل واتساب "I allow callmebot to send me messages" لرقم +34 644 10 47 73
try:
    CALLMEBOT_PHONE = st.secrets["CALLMEBOT_PHONE"]
    CALLMEBOT_APIKEY = st.secrets["CALLMEBOT_APIKEY"]
except Exception:
    CALLMEBOT_PHONE = "966551234567"
    CALLMEBOT_APIKEY = "حط_ال apikey هنا"
    st.warning("⚠️ لم يتم ضبط Secrets - حط رقمك والـ apikey في Secrets")

def clean_phone(raw):
    # ينظف الرقم تلقائيا مهما كتبته
    p = str(raw).strip()
    p = p.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if p.startswith("00"):
        p = p[2:]
    if p.startswith("0"):
        p = "966" + p[1:]
    if len(p) == 9 and p.startswith("5"):
        p = "966" + p
    return p

def send_whatsapp(msg):
    phone_clean = clean_phone(CALLMEBOT_PHONE)
    st.write(f"الرقم اللي قاعد أرسل له: {phone_clean} | الطول: {len(phone_clean)} رقم")
    if len(phone_clean) != 12 or not phone_clean.startswith("966"):
        st.error(f"الرقم غلط! لازم يكون 12 رقم يبدأ بـ 966، الحين هو: {phone_clean}")
        return False
    if not CALLMEBOT_APIKEY or CALLMEBOT_APIKEY == "حط_ال apikey هنا":
        st.error("الـ apikey مو محطوط في Secrets")
        return False
    try:
        url = "https://api.callmebot.com/whatsapp.php"
        params = {"phone": phone_clean, "text": msg, "apikey": CALLMEBOT_APIKEY}
        r = requests.get(url, params=params, timeout=15)
        st.write(f"رد الواتساب: {r.status_code} - {r.text[:300]}")
        if "ERROR" in r.text:
            st.error("CallMeBot رفض - اقرأ رسالة الخطأ فوق")
            if "Phone number" in r.text:
                st.error("المشكلة في الرقم - تأكد أنه 966 + 9 أرقام بدون + وبدون مسافات")
            if "apikey" in r.text.lower():
                st.error("المشكلة في الـ apikey - تأكد أنك أرسلت رسالة التفعيل لـ +34 644 10 47 73")
            return False
        return True
    except Exception as e:
        st.error(f"خطأ إرسال: {e}")
        return False

# زر تجربة الإرسال
if st.button("📱 جرب الإرسال الآن", use_container_width=True):
    if send_whatsapp("تجربة راصد الحيتان - إذا وصلتك معناها الإرسال شغال ✅"):
        st.success("تم الإرسال - شيك واتسابك ✅")

st.divider()

# ============================================================
# 2. هل السوق فاتح؟ - للعرض فقط، البحث يشتغل في الحالتين
# ============================================================
def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False, now
    return time(9, 30) <= now.time() <= time(16, 0), now

market_open, ny_now = is_market_open()
if market_open:
    st.success(f"🟢 السوق فاتح - نستخدم بيانات حية | {ny_now.strftime('%H:%M')} نيويورك")
else:
    st.warning(f"🔴 السوق مسكر - نستخدم بيانات آخر إغلاق | {ny_now.strftime('%H:%M')} نيويورك")

# ============================================================
# 3. قائمة الأسهم - 150 سهم
# ============================================================
STOCKS_150 = [
    # ETF - 10
    "SPY","QQQ","IWM","DIA","VOO","IVV","ARKK","XLF","XLK","XLE",
    # تكنولوجيا كبيرة - 25
    "NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL",
    "AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX",
    "PLTR","SNOW","CRWD","PANW","SHOP",
    # بنوك ومالية - 15
    "JPM","BAC","GS","MS","WFC","C","BLK","SCHW","AXP","V",
    "MA","PYPL","COIN","HOOD","SOFI",
    # طاقة - 12
    "XOM","CVX","COP","SLB","EOG","OXY","MPC","PSX","VLO","HAL",
    "MSTR","CLSK",
    # صحة - 15
    "LLY","UNH","JNJ","MRK","PFE","ABBV","TMO","AMGN","GILD","REGN",
    "VRTX","ISRG","HIMS","CVS","ZTS",
    # تجزئة واستهلاك - 15
    "WMT","COST","HD","MCD","SBUX","NKE","TGT","LOW","TJX","CMG",
    "LULU","ABNB","UBER","LYFT","DASH",
    # صناعة ودفاع - 12
    "BA","CAT","GE","HON","LMT","RTX","NOC","GD","DE","UPS",
    "FDX","DAL",
    # اتصالات وإعلام - 10
    "T","VZ","TMUS","DIS","CMCSA","WBD","PARA","SPOT","ROKU","NFLX",
    # أشباه موصلات إضافية - 10
    "SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON","SWKS",
    # نمو ومضاربة - 16
    "RIVN","LCID","NIO","PLUG","OPEN","GME","AMC","AFRM",
    "UPST","AI","SOUN","IONQ","RGTI","QBTS","DNA","BBAI",
    # قيادية أخرى - 10
    "BRK-B","PEP","KO","PG","CSCO","IBM","ORCL","XOM","VZ","INTC",
]
STOCKS_150 = list(dict.fromkeys(STOCKS_150))
st.write(f"عدد الأسهم في الفحص: **{len(STOCKS_150)} سهم**")

# ============================================================
# 4. جلب عقد الحوت الحقيقي من الأوبشن تشين
# ============================================================
def get_whale(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        last = float(hist['Close'].iloc[-1])
        # استبعد الأسهم الرخيصة اللي تخرب النتائج مثل PARA 0.10
        if last < 20:
            return None

        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]  # أقرب انتهاء
        chain = tk.option_chain(expiry)

        # نطاق البريميوم كنسبة من سعر السهم، مو رقم ثابت
        # SPY/QQQ غالية: 0.3% إلى 1.0% = 2.2 إلى 7.5 لـ SPY
        # NVDA متوسطة: 0.5% إلى 1.5%
        # الرخيصة: 2.0 إلى 3.0
        if last > 500:
            min_prem, max_prem = last * 0.003, last * 0.01
        elif last > 200:
            min_prem, max_prem = last * 0.005, last * 0.015
        else:
            min_prem, max_prem = 2.0, 3.0

        def best_in(df, opt_type):
            df = df.copy()
            df['type'] = opt_type
            # سترايك قريب 5% فقط، عشان ما نجيب عقود بعيدة ميتة
            f = df[
                (df['lastPrice'] >= min_prem) &
                (df['lastPrice'] <= max_prem) &
                (df['volume'].fillna(0) > 500) &
                (abs(df['strike'] - last) / last < 0.05)
            ]
            if f.empty:
                return None
            return f.sort_values('volume', ascending=False).iloc[0]

        best_call = best_in(chain.calls, 'CALL')
        best_put = best_in(chain.puts, 'PUT')

        # اختيار الاتجاه حسب حركة السهم، عشان ما نختار PUT تحوط والسوق طالع
        change = (last - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2]) * 100
        if change >= 0:
            whale = best_call if best_call is not None else best_put
            reason = "السهم صاعد، تجاهلنا PUT التحوط"
        else:
            whale = best_put if best_put is not None else best_call
            reason = "السهم هابط، تجاهلنا CALL التحوط"

        if whale is None:
            return None

        entry = float(whale['lastPrice'])
        strike = float(whale['strike'])
        volume = int(whale['volume'])
        stop = round(entry * 0.67, 2)
        targets = [round(entry * m, 2) for m in [1.25, 1.35, 1.50, 1.65, 1.75, 1.85, 1.90, 2.00]]

        return {
            "symbol": symbol,
            "type": whale['type'],
            "strike": strike,
            "expiry": expiry,
            "entry": entry,
            "stop": stop,
            "targets": targets,
            "volume": volume,
            "last": last,
            "change": change,
            "reason": reason,
            "prem_range": f"{min_prem:.2f} - {max_prem:.2f}"
        }
    except Exception:
        return None

# ============================================================
# 5. الفحص
# ============================================================
if st.button("🔍 افحص الآن - 150 سهم", use_container_width=True):
    with st.spinner(f"جار فحص الأوبشن تشين الحقيقي لـ {len(STOCKS_150)} سهم... قد يأخذ 40-60 ثانية"):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_whale(sym)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        # أفضل 10 حسب حجم العقد - هذا هو الحوت
        results = sorted(results, key=lambda x: x['volume'], reverse=True)[:10]
        st.session_state['results'] = results
        st.success(f"✅ فحصت {len(STOCKS_150)} سهم - لقيت {len(results)} توصية")

# ============================================================
# 6. عرض التوصيات - كروت، بدون جدول نهائيا
# ============================================================
if 'results' in st.session_state and st.session_state['results']:
    st.subheader(f"🏆 أفضل 10 توصيات - {len(st.session_state['results'])} توصية")

    for r in st.session_state['results']:
        emoji = "🟢" if r['type'] == 'CALL' else "🔴"
        msg = f"""🔍 راصد الحيتان
{r['symbol']}
{emoji} شراء مرجح {r['type']} {r['strike']:.1f}
الانتهاء: {r['expiry']} 📅
سعر التنفيذ: {r['entry']} ({int(r['entry']*100)} دولار للعقد) 💰
الوقف: {r['stop']} 🔴 | الكمية: {r['volume']} عقد 📦
الأهداف بالترتيب 🎯
{' | '.join(map(str, r['targets']))}
⚠️ إدارة الوقف
بعد الهدف الأول، ارفع الوقف إلى سعر الدخول. وبعد كل هدف جديد، ارفعه إلى سعر الهدف السابق.
📌 رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."""

        with st.container():
            st.markdown(f"### {emoji} {r['symbol']} - {r['type']} {r['strike']:.1f} - دخول {r['entry']}")
            st.write(f"السعر الحالي: {r['last']:.2f} ({r['change']:+.2f}%) | حجم العقد: {r['volume']} | الانتهاء: {r['expiry']}")
            st.write(f"نطاق البريميوم الصح لهالسهم: {r['prem_range']} | {r['reason']}")
            st.code(msg, language="text")
            if st.button(f"📤 أرسل {r['symbol']} للواتساب", key=f"send_{r['symbol']}", use_container_width=True):
                if send_whatsapp(msg):
                    st.success(f"تم إرسال {r['symbol']} للواتساب ✅ شيك واتسابك")
            st.divider()

    # زر إرسال الكل
    if st.button("📤 أرسل أفضل 10 كلها للواتساب", use_container_width=True):
        for r in st.session_state['results']:
            emoji = "🟢" if r['type'] == 'CALL' else "🔴"
            msg = f"🔍 راصد الحيتان\n{r['symbol']}\n{emoji} {r['type']} {r['strike']:.1f}\nدخول: {r['entry']} | وقف: {r['stop']} | أهداف: {' | '.join(map(str, r['targets']))}"
            send_whatsapp(msg)
        st.success("تم إرسال الكل للواتساب ✅")
