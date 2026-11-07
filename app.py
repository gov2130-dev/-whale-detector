import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import requests

st.set_page_config(page_title="راصد الحيتان", layout="centered")
st.title("📊 راصد الحيتان")

# ===== 1. اعدادات الواتس - لازم تغيرها، اذا خليتها مثل ما هي ما بيرسل =====
ULTRAMSG_INSTANCE = "instance12345"  # غيرها: انسخها من موقع ultramsg.com
ULTRAMSG_TOKEN = "abc123"  # غيرها: انسخها من موقع ultramsg.com
MY_WHATSAPP = "966500000000"  # غيرها: رقمك يبدأ بـ 966 بدون + وبدون 0

MIN_PREMIUM = 30000
MIN_RATIO = 1.2

def get_targets(entry):
    return [round(entry*1.25,2), round(entry*1.35,2), round(entry*1.50,2), round(entry*1.65,2),
            round(entry*1.75,2), round(entry*1.85,2), round(entry*1.90,2), round(entry*2.00,2)]

# ===== اصلاح الواتس - الحين يطلع لك وش الخطأ بالضبط =====
def send_whatsapp(message):
    if "instance12345" in ULTRAMSG_INSTANCE or "abc123" in ULTRAMSG_TOKEN:
        return False, "⚠️ ما غيرت بيانات UltraMsg! لسى حاط البيانات الوهمية. روح ultramsg.com وانسخ Instance و Token الحقيقي."
    try:
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
        data = {"token": ULTRAMSG_TOKEN, "to": MY_WHATSAPP, "body": message}
        res = requests.post(url, data=data, timeout=20)
        # نعرض الرد كامل عشان نعرف وش المشكلة
        if res.status_code == 200:
            return True, "تم الارسال ✅"
        else:
            return False, f"خطأ من UltraMsg: {res.text[:500]}"
    except Exception as e:
        return False, f"خطأ اتصال: {e}"

# زر تجربة الواتس - اضغطه قبل الفحص
if st.button("📲 جرب الواتس الحين - ارسل رسالة تجريبية"):
    ok, msg = send_whatsapp("تجربة - راصد الحيتان شغال ✅")
    if ok:
        st.success("الواتس شغال! وصلكت الرسالة؟")
    else:
        st.error(msg)
        st.info("الحل: تأكد انك سويت Scan للباركود في UltraMsg، وان رقمك مربوط، وان Instance شغال.")

# ===== صيغة الرسالة - بدون كلمة الأمريكي نهائياً =====
def format_message(symbol, company, opt_type, strike, exp, entry, stop, vol):
    targets = get_targets(entry)
    type_txt = "🔴 شراء مرجح PUT" if opt_type == "PUT" else "🟢 شراء مرجح CALL"
    exp_fmt = datetime.strptime(exp, "%Y-%m-%d").strftime("%b %d %Y").upper()
    time_now = datetime.now().strftime("%H:%M:%S")
    total_cost = int(entry * 100)
    msg = f"""🔍 راصد الحيتان
{symbol} - {company}
{type_txt} {strike}
الانتهاء: {exp_fmt} 📅
سعر التنفيذ: {entry} ({total_cost} دولار للعقد) 💰
الوقف: {stop} 🔴 | الكمية: {int(vol)} عقد 📦
الأهداف بالترتيب 🎯
{targets[0]} | {targets[1]} | {targets[2]} | {targets[3]}
{targets[4]} | {targets[5]} | {targets[6]} | {targets[7]}
⚠️ إدارة الوقف
بعد الهدف الأول، ارفع الوقف إلى سعر الدخول. وبعد كل هدف جديد، ارفعه إلى سعر الهدف السابق.
وقت التنفيذ: {time_now} SA 🕐
📌 رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."""
    return msg

# ===== حفظ النتائج عشان ما تتكرر مع كل ضغطة زر =====
if "results" not in st.session_state:
    st.session_state.results = []
if "seen" not in st.session_state:
    st.session_state.seen = set()

if st.button("🔍 افحص الآن", use_container_width=True):
    st.session_state.results = []
    st.session_state.seen = set()
    tickers = ["BABA","AMZN","MSFT","NVDA","TSLA","META","GOOGL","AMD","NFLX","GDX","SPY","QQQ","COIN","PLTR","AAPL","CRM","ORCL","AVGO","JPM"]
    with st.spinner("جاري الفحص..."):
        for symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company = info.get('shortName', symbol)
                if not info.get('currentPrice'):
                    continue
                best = None
                best_premium = 0
                for exp in ticker.options[:3]:
                    days = (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days
                    if days < 0 or days > 7:
                        continue
                    chain = ticker.option_chain(exp)
                    for opt_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                        for _, row in df.iterrows():
                            vol = row['volume'] if pd.notna(row['volume']) else 0
                            oi = row['openInterest'] if pd.notna(row['openInterest']) else 0
                            price = row['lastPrice'] if pd.notna(row['lastPrice']) else 0
                            if vol < 200 or oi == 0 or price < 0.5:
                                continue
                            premium = vol * price * 100
                            # منع التكرار: مفتاح واحد لكل سهم + سترايك + نوع
                            key = f"{symbol}-{opt_type}-{row['strike']}-{exp}"
                            if key in st.session_state.seen:
                                continue
                            if vol/oi >= MIN_RATIO and premium >= MIN_PREMIUM and premium > best_premium:
                                best_premium = premium
                                best = (opt_type, row, exp, price, vol, key)
                if best:
                    opt_type, row, exp, price, vol, key = best
                    st.session_state.seen.add(key)
                    entry = round(float(price), 2)
                    stop = round(entry * 0.67, 2)
                    msg = format_message(symbol, company, opt_type, row['strike'], exp, entry, stop, vol)
                    st.session_state.results.append((symbol, msg))
            except:
                continue
    if not st.session_state.results:
        st.warning("ما فيه صفقات اليوم.")
    else:
        st.success(f"✅ لقيت {len(st.session_state.results)} سهم مختلف، بدون تكرار")

# عرض النتائج المحفوظة - ما تتكرر حتى لو ضغطت زر الواتس
for symbol, msg in st.session_state.results:
    st.markdown(f"""
    <div dir="rtl" style="background-color:white; padding:18px; border-radius:18px; box-shadow:0 2px 10px rgba(0,0,0,0.1); margin-bottom:10px; text-align:right; font-size:17px; line-height:1.8; color:black; white-space:pre-line;">
    {msg}
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"📲 ارسل {symbol} للواتس", key=f"wa_{symbol}_{len(msg)}"):
        ok, txt = send_whatsapp(msg)
        if ok:
            st.success(f"✅ تم ارسال {symbol}")
        else:
            st.error(txt)
    st.divider()
