import streamlit as st, yfinance as yf, requests, pandas as pd
from datetime import datetime

st.set_page_config(layout="wide", page_title="Whale Bot")
st.markdown("<style>.stApp{background:#0a0e14;color:white} div[data-testid='stCode']{background:#111827;border-left:4px solid #00ff88;border-radius:10px} h1{color:#00ff88}</style>", unsafe_allow_html=True)
st.title("Whale Bot - Early")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
        return r.status_code==200
    except:
        return False

def get_price(ticker):
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="1d", interval="1m", auto_adjust=True)
        if not df.empty:
            return float(df['Close'].iloc[-1]), df
        df = tk.history(period="5d", interval="5m", auto_adjust=True)
        if not df.empty:
            return float(df['Close'].iloc[-1]), df
        return None, None
    except:
        return None, None

def get_signal(ticker, tf):
    try:
        price, _ = get_price(ticker)
        if not price:
            return None, None
        tk = yf.Ticker(ticker)
        df = tk.history(period="5d", interval=tf, auto_adjust=True)
        if df.empty or len(df) < 25:
            return None, None
        last = float(df['Close'].iloc[-1])
        if abs(last - price) / price > 0.15:
            factor = price / last
            df['Close'] = df['Close'] * factor
            df['High'] = df['High'] * factor
            df['Low'] = df['Low'] * factor
        ema9 = df['Close'].ewm(span=9).mean()
        ema20 = df['Close'].ewm(span=20).mean()
        e9 = float(ema9.iloc[-1])
        e20 = float(ema20.iloc[-1])
        e9p = float(ema9.iloc[-2])
        e20p = float(ema20.iloc[-2])
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.001)))
        rsi_now = float(rsi.iloc[-1])
        rsi_prev = float(rsi.iloc[-2])
        rh = float(df['High'].iloc[-20:].max())
        rl = float(df['Low'].iloc[-20:].min())
        dist = abs(e9 - e20) / e20 * 100
        early_call = (e9 > e20p and dist < 0.5 and rsi_now > rsi_prev) or (price >= rh*0.998 and rsi_now > 50)
        early_put = (e9 < e20p and dist < 0.5 and rsi_now < rsi_prev) or (price <= rl*1.002 and rsi_now < 50)
        info = {"curr":price,"ema9":e9,"ema20":e20,"rsi":rsi_now,"rsi_prev":rsi_prev,"rh":rh,"rl":rl,"dist":dist}
        if early_call:
            return "CALL", info
        if early_put:
            return "PUT", info
        if e9 > e20 and rsi_now > 50:
            return "CALL", info
        if e9 < e20 and rsi_now < 50:
            return "PUT", info
        return None, info
    except:
        return None, None

tf = st.selectbox("Timeframe", ["5m","15m","30m","1h","1d"], index=1)
watch = st.text_area("Tickers", "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL")
WATCHLIST = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button("RUN SCAN", use_container_width=True, type="primary"):
    for t in WATCHLIST:
        sig, info = get_signal(t, tf)
        if not info:
            st.write(f"{t} no data")
            continue
        price = info['curr']
        rsi = info['rsi']
        arrow = "UP" if rsi > info['rsi_prev'] else "DOWN"
        tag = "EARLY" if info['dist'] < 0.5 else ""
        if sig:
            txt = f"{t} {sig} {tag} | ${price:.2f} | RSI {rsi:.1f} {arrow} | EMA9 {info['ema9']:.2f} EMA20 {info['ema20']:.2f} | H {info['rh']:.2f} L {info['rl']:.2f} | {tf}"
            st.code(txt)
            send(txt)
        else:
            st.write(f"{t} ${price:.2f} | H {info['rh']:.2f} L {info['rl']:.2f} | RSI {rsi:.1f} {arrow} | EMA9 {info['ema9']:.2f} EMA20 {info['ema20']:.2f}")

st.write("Fixed price from 1m chart")
