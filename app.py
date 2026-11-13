# راصد الحيتان - V4
# توصيات فقط، بدون جدول - بريميوم حقيقي من الأوبشن تشين - إرسال واتساب
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
import requests

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("🔍 راصد الحيتان")

# ============ إعدادات الواتساب ============
# استخدم Twilio WhatsApp أو UltraMsg - حط بياناتك هنا
WHATSAPP_TOKEN = st.secrets.get("WHATSAPP_TOKEN", "حط_التوكن_هنا")
WHATSAPP_TO = st.secrets.get("WHATSAPP_TO", "9665xxxxxxxx")  # رقمك بالواتساب
WHATSAPP_API_URL = "https://api.ultramsg.com/instanceXXXX/messages/chat"  # مثال UltraMsg

def send_whatsapp(msg):
    try:
        # UltraMsg مثال - غيره حسب خدمتك
        payload = {"token": WHATSAPP_TOKEN, "to": WHATSAPP_TO, "body": msg}
        r = requests.post(WHATSAPP_API_URL, data=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"فشل الإرسال: {e}")
        return False

# ============ قائمة الأسهم - 150 سهم، بدون أسهم رخيصة ============
STOCKS_150 = ["SPY","QQQ","IWM","DIA","VOO","NVDA","AAPL","MSFT","GOOGL","AMZN","META","TSLA","AVGO","ORCL","AMD","NFLX","CRM","ADBE","MU","QCOM","TXN","AMAT","PLTR","SNOW","CRWD","PANW","SHOP","JPM","BAC","GS","MS","WFC","BLK","SCHW","AXP","V","MA","PYPL","COIN","HOOD","SOFI","XOM","CVX","COP","SLB","OXY","MSTR","LLY","UNH","JNJ","MRK","PFE","ABBV","TMO","AMGN","GILD","VRTX","ISRG","WMT","COST","HD","MCD","SBUX","NKE","TGT","LOW","TJX","CMG","LULU","ABNB","UBER","DASH","BA","CAT","GE","HON","LMT","RTX","NOC","DE","UPS","FDX","DAL","T","VZ","TMUS","DIS","CMCSA","SPOT","SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","RIVN","LCID","AFRM","UPST","AI","SOUN","IONQ","RGTI","BRK-B","PEP","KO","PG","CSCO","IBM"]
STOCKS_150 = list(dict.fromkeys(STOCKS_150))

def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False
    return time(9, 30) <= now.time() <= time(16, 0)

market_open = is_market_open()
st.warning("🔴 السوق مسكر - نستخدم بيانات آخر إغلاق" if not market_open else "🟢 السوق فاتح - بيانات حية")

# ============ التصحيح الأهم: جيب العقد الحقيقي من الأوبشن تشين ============
def get_real_whale_contract(symbol):
    """
    بدل ما نحسب البريميوم، نجيبه من الأوبشن تشين الحقيقي
    نختار العقد اللي بريميومه بين 2 و 3، وأعلى حجم تداول = هذا هو عقد الحوت
    """
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty:
            return None
        last_close = float(hist['Close'].iloc[-1])
        # استبعد الأسهم الرخيصة اللي تخرب النتائج مثل PARA 0.10 و NIO 3.05
        if last_close < 20:
            return None

        # أقرب تاريخ انتهاء - الجمعة القادمة
        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]  # أقرب انتهاء

        chain = tk.option_chain(expiry)
        # نجمع CALL و PUT مع بعض
        calls = chain.calls.copy()
        calls['type'] = 'CALL'
        puts = chain.puts.copy()
        puts['type'] = 'PUT'
        all_opts = pd.concat([calls, puts])

        # فلتر الحوت الحقيقي: بريميوم 2 إلى 3، وحجم تداول عالي
        # هذا يصلح مشكلة NVDA: قبل كنا نقدر البريميوم 7.21، الحين نجيبه حقيقي 2.66
        filtered = all_opts[
            (all_opts['lastPrice'] >= 2.0) &
            (all_opts['lastPrice'] <= 3.0) &
            (all_opts['volume'].fillna(0) > 500) &
            (abs(all_opts['strike'] - last_close) / last_close < 0.10)  # سترايك قريب من السعر 10%
        ]
        if filtered.empty:
            return None

        # أعلى حجم = عقد الحوت
        whale = filtered.sort_values('volume', ascending=False).iloc[0]
        entry = float(whale['lastPrice'])
        strike = float(whale['strike'])
        opt_type = whale['type']
        volume = int(whale['volume'])

        # الأهداف والوقف بنفس معادلة البوت القديم
        stop = round(entry * 0.67, 2)
        targets = [round(entry * m, 2) for m in [1.25, 1.35, 1.50, 1.65, 1.75, 1.85, 1.90, 2.00]]

        return {
            "symbol": symbol,
            "type": opt_type,  # CALL أو PUT حقيقي من السوق، مو من تغير السعر
            "strike": strike,
            "expiry": expiry,
            "entry": entry,
            "stop": stop,
            "targets": targets,
            "volume": volume,
            "last_close": last_close,
            "score": volume  # الترتيب حسب الحجم، مو حسب نقاط وهمية
        }
    except Exception:
        return None

# ============ الفحص والعرض كتوصيات، مو جدول ============
if st.button("🔍 افحص الآن - 150 سهم", use_container_width=True):
    with st.spinner("جار فحص الأوبشن تشين الحقيقي لـ 150 سهم..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_real_whale_contract(sym)
            if r:
                results.append(r)
            progress.progress((i+1)/len(STOCKS_150))

        # أفضل 10 حسب حجم العقد - هذا هو الحوت
        results = sorted(results, key=lambda x: x['volume'], reverse=True)[:10]
        st.session_state['results'] = results
        st.success(f"✅ فحصت {len(STOCKS_150)} سهم - لقيت {len(results)} توصية")

# عرض التوصيات - بدون جدول نهائيا
if 'results' in st.session_state:
    for r in st.session_state['results']:
        emoji = "🟢" if r['type'] == 'CALL' else "🔴"
        # نفس صيغة الواتساب القديمة بالضبط
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

        # كارد توصية، مو جدول
        with st.container():
            st.markdown(f"### {emoji} {r['symbol']} - {r['type']} {r['strike']:.1f}")
            st.code(msg, language="text")
            st.write(f"السعر الحالي: {r['last_close']:.2f} | حجم العقد: {r['volume']} | الانتهاء: {r['expiry']}")
            if st.button(f"📤 أرسل {r['symbol']} للواتساب", key=f"send_{r['symbol']}"):
                if send_whatsapp(msg):
                    st.success(f"تم إرسال {r['symbol']} للواتساب ✅")
                else:
                    st.error("فشل الإرسال - تأكد من التوكن والرقم")

    # زر إرسال الكل دفعة واحدة
    if st.button("📤 أرسل أفضل 10 كلها للواتساب", use_container_width=True):
        for r in st.session_state['results']:
            emoji = "🟢" if r['type'] == 'CALL' else "🔴"
            msg = f"🔍 راصد الحيتان\n{r['symbol']}\n{emoji} {r['type']} {r['strike']:.1f}\nدخول: {r['entry']} | وقف: {r['stop']} | أهداف: {' | '.join(map(str, r['targets']))}"
            send_whatsapp(msg)
        st.success("تم إرسال الكل للواتساب ✅")
