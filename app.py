# ============================================================
# راصد الحيتان - V7 - الإرسال مفتوح
# بدون Secrets - تكتب رقمك والـ apikey في الصفحة نفسها
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
# 1. الإرسال مفتوح - بدون Secrets
# ============================================================
st.subheader("📱 إعدادات الواتساب - مفتوح")

# خانات مفتوحة، تقدر تغيرها في أي وقت من الصفحة
col1, col2 = st.columns(2)
with col1:
    phone_input = st.text_input(
        "رقم الواتساب - 966 + رقمك بدون + وبدون مسافات",
        value=st.session_state.get("phone", "966551234567"),
        key="phone_input"
    )
with col2:
    apikey_input = st.text_input(
        "apikey من CallMeBot",
        value=st.session_state.get("apikey", ""),
        type="password",
        key="apikey_input"
    )

# حفظها في session عشان ما تنمسح مع كل تحديث
st.session_state["phone"] = phone_input
st.session_state["apikey"] = apikey_input

# زر الإرسال التلقائي مفتوح
auto_send = st.checkbox("✅ إرسال تلقائي للواتساب بعد كل فحص", value=False)
st.caption("إذا فعلته، بعد ما يخلص الفحص بيرسل أفضل 10 لحاله للواتساب، بدون ما تضغط زر لكل واحد")

def clean_phone(raw):
    p = str(raw).strip()
    p = p.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if p.startswith("00"):
        p = p[2:]
    if p.startswith("0"):
        p = "966" + p[1:]
    if len(p) == 9 and p.startswith("5"):
        p = "966" + p
    return p

def send_whatsapp(msg, phone, apikey):
    # الإرسال مفتوح - ما يوقفك لو Secrets مو موجود
    phone_clean = clean_phone(phone)
    st.write(f"الرقم اللي قاعد أرسل له: {phone_clean} | الطول: {len(phone_clean)} رقم")
    if len(phone_clean) != 12 or not phone_clean.startswith("966"):
        st.error(f"الرقم غلط! لازم 12 رقم يبدأ بـ 966، الحين: {phone_clean}")
        return False
    if not apikey:
        st.error("حط الـ apikey في الخانة اللي فوق - عشان تفعل CallMeBot ارسل واتساب 'I allow callmebot to send me messages' لرقم +34 644 10 47 73")
        return False
    try:
        url = "https://api.callmebot.com/whatsapp.php"
        params = {"phone": phone_clean, "text": msg, "apikey": apikey}
        r = requests.get(url, params=params, timeout=15)
        st.write(f"رد الواتساب: {r.status_code} - {r.text[:300]}")
        if "ERROR" in r.text:
            if "Phone number" in r.text:
                st.error("المشكلة في الرقم - تأكد أنه 966 + 9 أرقام")
            elif "apikey" in r.text.lower():
                st.error("المشكلة في الـ apikey - تأكد أنك فعلت CallMeBot")
            else:
                st.error(f"CallMeBot رفض: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        st.error(f"خطأ إرسال: {e}")
        return False

if st.button("📱 جرب الإرسال الآن - مفتوح", use_container_width=True):
    if send_whatsapp("تجربة راصد الحيتان - إذا وصلتك معناها الإرسال شغال ✅", st.session_state["phone"], st.session_state["apikey"]):
        st.success("تم الإرسال - شيك واتسابك ✅")

st.divider()

# ============================================================
# 2. هل السوق فاتح؟ - للعرض فقط
# ============================================================
def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False, now
    return time(9, 30) <= now.time() <= time(16, 0), now

market_open, ny_now = is_market_open()
if market_open:
    st.success(f"🟢 السوق فاتح - بيانات حية | {ny_now.strftime('%H:%M')} نيويورك")
else:
    st.warning(f"🔴 السوق مسكر - بيانات آخر إغلاق | {ny_now.strftime('%H:%M')} نيويورك")

# ============================================================
# 3. الأسهم - 150 سهم
# ============================================================
STOCKS_150 = [
    "SPY","QQQ","IWM","DIA","VOO","IVV","ARKK","XLF","XLK","XLE",
    "NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL",
    "AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX",
    "PLTR","SNOW","CRWD","PANW","SHOP",
    "JPM","BAC","GS","MS","WFC","C","BLK","SCHW","AXP","V",
    "MA","PYPL","COIN","HOOD","SOFI",
    "XOM","CVX","COP","SLB","EOG","OXY","MPC","PSX","VLO","HAL","MSTR","CLSK",
    "LLY","UNH","JNJ","MRK","PFE","ABBV","TMO","AMGN","GILD","REGN",
    "VRTX","ISRG","HIMS","CVS","ZTS",
    "WMT","COST","HD","MCD","SBUX","NKE","TGT","LOW","TJX","CMG",
    "LULU","ABNB","UBER","LYFT","DASH",
    "BA","CAT","GE","HON","LMT","RTX","NOC","GD","DE","UPS","FDX","DAL",
    "T","VZ","TMUS","DIS","CMCSA","WBD","PARA","SPOT","ROKU",
    "SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON","SWKS",
    "RIVN","LCID","NIO","PLUG","OPEN","GME","AMC","AFRM",
    "UPST","AI","SOUN","IONQ","RGTI","QBTS","DNA","BBAI",
    "BRK-B","PEP","KO","PG","CSCO","IBM",
]
STOCKS_150 = list(dict.fromkeys(STOCKS_150))
st.write(f"عدد الأسهم: **{len(STOCKS_150)} سهم**")

# ============================================================
# 4. جلب عقد الحوت الحقيقي
# ============================================================
def get_whale(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        last = float(hist['Close'].iloc[-1])
        if last < 20:
            return None
        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = tk.option_chain(expiry)
        if last > 500:
            min_prem, max_prem = last * 0.003, last * 0.01
        elif last > 200:
            min_prem, max_prem = last * 0.005, last * 0.015
        else:
            min_prem, max_prem = 2.0, 3.0

        def best_in(df, opt_type):
            df = df.copy()
            df['type'] = opt_type
            f = df[(df['lastPrice'] >= min_prem) & (df['lastPrice'] <= max_prem) &
                   (df['volume'].fillna(0) > 500) &
                   (abs(df['strike'] - last) / last < 0.05)]
            if f.empty:
                return None
            return f.sort_values('volume', ascending=False).iloc[0]

        best_call = best_in(chain.calls, 'CALL')
        best_put = best_in(chain.puts, 'PUT')
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
        return {"symbol": symbol, "type": whale['type'], "strike": strike, "expiry": expiry,
                "entry": entry, "stop": stop, "targets": targets, "volume": volume,
                "last": last, "change": change, "reason": reason,
                "prem_range": f"{min_prem:.2f} - {max_prem:.2f}"}
    except Exception:
        return None

def make_msg(r):
    emoji = "🟢" if r['type'] == 'CALL' else "🔴"
    return f"""🔍 راصد الحيتان
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

# ============================================================
# 5. الفحص + إرسال تلقائي مفتوح
# ============================================================
if st.button("🔍 افحص الآن - 150 سهم", use_container_width=True):
    with st.spinner(f"جار فحص {len(STOCKS_150)} سهم..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_whale(sym)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        results = sorted(results, key=lambda x: x['volume'], reverse=True)[:10]
        st.session_state['results'] = results
        st.success(f"✅ فحصت {len(STOCKS_150)} سهم - لقيت {len(results)} توصية")

        # إرسال تلقائي مفتوح - إذا فعلت الشيك بوكس فوق
        if auto_send and results:
            st.info("📤 الإرسال التلقائي مفعل - قاعد أرسل أفضل 10 للواتساب...")
            for r in results:
                send_whatsapp(make_msg(r), st.session_state["phone"], st.session_state["apikey"])
            st.success("تم إرسال الكل تلقائيا ✅")

# ============================================================
# 6. عرض التوصيات - بدون جدول
# ============================================================
if 'results' in st.session_state and st.session_state['results']:
    st.subheader(f"🏆 أفضل 10 توصيات")
    for r in st.session_state['results']:
        emoji = "🟢" if r['type'] == 'CALL' else "🔴"
        msg = make_msg(r)
        with st.container():
            st.markdown(f"### {emoji} {r['symbol']} - {r['type']} {r['strike']:.1f} - دخول {r['entry']}")
            st.write(f"السعر: {r['last']:.2f} ({r['change']:+.2f}%) | حجم: {r['volume']} | الانتهاء: {r['expiry']}")
            st.write(f"نطاق البريميوم: {r['prem_range']} | {r['reason']}")
            st.code(msg, language="text")
            if st.button(f"📤 أرسل {r['symbol']} للواتساب", key=f"send_{r['symbol']}", use_container_width=True):
                if send_whatsapp(msg, st.session_state["phone"], st.session_state["apikey"]):
                    st.success(f"تم إرسال {r['symbol']} ✅")
            st.divider()

    if st.button("📤 أرسل أفضل 10 كلها للواتساب", use_container_width=True):
        for r in st.session_state['results']:
            send_whatsapp(make_msg(r), st.session_state["phone"], st.session_state["apikey"])
        st.success("تم إرسال الكل ✅")
