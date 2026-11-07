import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import urllib.parse
import re
import requests

st.set_page_config(page_title="راصد الحيتان", layout="centered")
st.title("📊 راصد الحيتان")

# ===== الرقم - ينظف لحاله =====
def clean_phone(raw):
    p = re.sub(r'\D', '', str(raw))
    if p.startswith("00"):
        p = p[2:]
    if p.startswith("0"):
        p = "966" + p[1:]
    if p.startswith("5") and len(p) == 9:
        p = "966" + p
    return p

raw_phone = st.text_input("رقم الواتس", value="0555371577")
MY_WHATSAPP = clean_phone(raw_phone)
st.caption(f"✅ الرقم الصح: {MY_WHATSAPP}")

# ===== اعدادات الارسال - اختر الطريقتين =====
st.write("### 📲 طريقة الارسال")
send_mode = st.radio("كيف تبي يرسل؟", 
    ["كل توصية لوحدها", "الكل في رسالة واحدة", "بكلا الطريقتين - لوحدها + مجمعة"],
    horizontal=False)

# خيار CallMeBot للارسال التلقائي - اختياري
with st.expander("⚙️ تبي ارسال تلقائي بدون ما تفتح الواتس؟ (اختياري)"):
    st.write("اذا تبيه يرسل لحاله بدون ما تضغط ارسال في الواتس، ارسل لـ +34 644 71 27 73 كلمة: I allow callmebot to send me messages وخذ الـ apikey")
    CALLMEBOT_APIKEY = st.text_input("حط الـ apikey هنا اذا عندك (اذا ما عندك اتركه فاضي)", value="")
    def send_auto(msg):
        if not CALLMEBOT_APIKEY:
            return False, "ما حطيت apikey - استخدم زر الواتس اليدوي اللي تحت"
        try:
            url = "https://api.callmebot.com/whatsapp.php"
            res = requests.get(url, params={"phone": MY_WHATSAPP, "text": msg, "apikey": CALLMEBOT_APIKEY}, timeout=20)
            return res.status_code == 200, "تم الارسال التلقائي ✅"
        except Exception as e:
            return False, f"خطأ: {e}"
    st.caption("اذا تركته فاضي، بيشتغل زر الواتس العادي اللي يفتح لك الواتس جاهز")

MIN_PREMIUM = 30000
MIN_RATIO = 1.2

def get_targets(entry):
    return [round(entry*1.25,2), round(entry*1.35,2), round(entry*1.50,2), round(entry*1.65,2),
            round(entry*1.75,2), round(entry*1.85,2), round(entry*1.90,2), round(entry*2.00,2)]

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
    st.success(f"✅ لقيت {len(st.session_state.results)} سهم")

# ===== عرض النتائج بكلا الطريقتين =====
if st.session_state.results:
    # الطريقة 1: الكل في رسالة واحدة - يطلع فوق
    if send_mode in ["الكل في رسالة واحدة", "بكلا الطريقتين - لوحدها + مجمعة"]:
        st.markdown("### 📦 الطريقة 1: الكل في رسالة واحدة")
        all_msg = "\n\n━━━━━━━━━━━━━━\n\n".join([m for _, m in st.session_state.results])
        wa_all = f"https://wa.me/{MY_WHATSAPP}?text={urllib.parse.quote(all_msg)}"
        st.info(f"الرسالة المجمعة فيها {len(st.session_state.results)} توصية في رسالة واتس واحدة")
        st.link_button("📲 ارسل الكل في رسالة واحدة للواتس", wa_all, use_container_width=True)
        st.divider()

    # الطريقة 2: كل توصية لوحدها
    if send_mode in ["كل توصية لوحدها", "بكلا الطريقتين - لوحدها + مجمعة"]:
        st.markdown("### 📄 الطريقة 2: كل توصية لوحدها")
        for symbol, msg in st.session_state.results:
            st.markdown(f"""
            <div dir="rtl" style="background-color:white; padding:18px; border-radius:18px; box-shadow:0 2px 10px rgba(0,0,0,0.1); margin-bottom:10px; text-align:right; font-size:17px; line-height:1.8; color:black; white-space:pre-line;">
            {msg}
            </div>
            """, unsafe_allow_html=True)
            wa_link = f"https://wa.me/{MY_WHATSAPP}?text={urllib.parse.quote(msg)}"
            st.link_button(f"📲 ارسل {symbol} لوحدها للواتس", wa_link, use_container_width=True)
            st.divider()
