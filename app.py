import streamlit as st, yfinance as yf, requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("Whale Bot - Always Results")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(m):
    try:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=8)
    except: pass

def get_df(t, tf):
    # جرب 3 طرق
    for per in ["60d","20d","5d"]:
        try:
            df = yf.download(t, period=per, interval=tf, auto_adjust=True, progress=False, threads=False)
            if df is not None and not df.empty and len(df) >= 10:
                return df
        except: pass
    # اذا فشل جرب history
    try:
        df = yf.Ticker(t).history(period="60d", interval=tf, auto_adjust=True)
        if not df.empty: return df
    except: pass
    return None

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=3)
default_list = "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL,AMZN,NFLX,PLTR,SHOP,UBER,BA"
watch = st.text_area("القائمة", default_list, height=80)
WL = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button(f"RUN SCAN {tf}", use_container_width=True, type="primary"):
    results = 0
    for t in WL:
        df = get_df(t, tf)
        if df is None:
            st.write(f"⚠️ {t}: no data from Yahoo - جرب فريم 1d")
            continue
        try:
            price = float(df['Close'].iloc[-1])
            e9 = float(df['Close'].ewm(9).mean().iloc[-1])
            e20 = float(df['Close'].ewm(20).mean().iloc[-1])
            # ابسط منطق يضمن نتيجة
            sig = "CALL" if price > e9 else "PUT"
            txt = f"{t} {sig} | ${price:.2f} | EMA9 {e9:.2f} EMA20 {e20:.2f} | {tf}"
            st.code(txt)
            results += 1
        except Exception as ex:
            st.write(f"{t} error {ex}")
            continue
    st.success(f"ظهر {results} نتيجة من {len(WL)} في فريم {tf}")
    if results == 0:
        st.error("Yahoo مقفل الان - اختر فريم 1d او انتظر افتتاح السوق. هذا مو من الكود")
