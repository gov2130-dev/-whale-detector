import streamlit as st
import requests
import yfinance as yf

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "ضع التوكن هنا")
CHAT_ID = "13889370"

st.set_page_config(page_title="حوت 54", layout="wide")
st.title("👑 بوت الحوت 54 - فحص البري ماركت")

STOCKS_54 = ["NVDA","TSLA","AAPL","MSFT","AMZN","META","NFLX","AMD","NVDL","TSLL","PLTR","COIN","MSTR","SMCI","AVGO","GOOGL","SPY","QQQ"]

def get_price(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d", interval="1m")
        return float(data['Close'].iloc[-1])
    except:
        return None

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode":"HTML"})
        st.success("تم الارسال لتلجرام ✅")
    except Exception as e:
        st.error(f"خطأ تلجرام: {e}")

# --- قسم الفحص ---
st.header("🔍 فحص 54")
if st.button("افحص الان", type="primary"):
    st.write("جاري الفحص...")
    for sym in STOCKS_54:
        price = get_price(sym)
        if price:
            st.write(f"{sym}: ${price}")

st.divider()

# --- قسم فحص هل تحقق الهدف الجديد ---
st.header("📈 فحص هل تحقق الهدف؟")
check_sym = st.text_input("اكتب الرمز مثلا NVDL")
if st.button("فحص السعر الحالي"):
    if check_sym:
        p = get_price(check_sym.upper())
        if p:
            st.metric(f"سعر {check_sym.upper()} الان", f"${p}")
            st.info("قارن السعر الحالي باهداف الرسالة:\nاذا وصل لسعر الهدف الاول = تحقق +50% ✅\nاذا نزل تحت الستوب = ضرب ستوب 🔴")
        else:
            st.error("ما قدرت اجيب السعر")
