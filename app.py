import streamlit as st, yfinance as yf, requests, pandas as pd
st.set_page_config(layout="wide")
st.title("Whale Bot")
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")
def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=10)
    except: pass
def get_sig(tk_sym, tf):
    try:
        tk = yf.Ticker(tk_sym)
        d1 = tk.history(period="1d", interval="1m", auto_adjust=True)
        if d1.empty: return None, None
        price = float(d1['Close'].iloc[-1])
        df = tk.history(period="5d", interval=tf, auto_adjust=True)
        if df.empty: return None, None
        e9 = float(df['Close'].ewm(9).mean().iloc[-1])
        e20 = float(df['Close'].ewm(20).mean().iloc[-1])
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.001)))
        r = float(rsi.iloc[-1])
        rh = float(df['High'].iloc[-20:].max())
        rl = float(df['Low'].iloc[-20:].min())
        info = (price, e9, e20, r, rh, rl)
        if price >= rh*0.998 and r>50: return "CALL", info
        if price <= rl*1.002 and r<50: return "PUT", info
        if e9>e20 and r>50: return "CALL", info
        if e9<e20 and r<50: return "PUT", info
        return None, info
    except: return None, None

tf = st.selectbox("TF", ["5m","15m","30m","1h"], index=1)
watch = st.text_area("Tickers", "SPY,QQQ,AAPL,META,NVDA,TSLA")
WL = [x.strip().upper() for x in watch.split(",") if x.strip()]
if st.button("RUN"):
    for t in WL:
        sig, info = get_sig(t, tf)
        if not info:
            st.write(t+" no data")
            continue
        price, e9, e20, r, rh, rl = info
        if sig:
            msg = f"{t} {sig} | ${price:.2f} | RSI {r:.1f} | EMA9 {e9:.1f} EMA20 {e20:.1f}"
            st.code(msg)
            send(msg)
        else:
            st.write(f"{t} ${price:.2f} RSI {r:.1f}")
