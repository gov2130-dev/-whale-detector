import streamlit as st, yfinance as yf, requests
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Whale Early Bot - Real Price")

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

def get_real_price(ticker):
    try:
        tk = yf.Ticker(ticker)
        price = None
        try:
            price = tk.fast_info.get('last_price')
        except:
            pass
        if not price:
            try:
                price = tk.info.get('currentPrice') or tk.info.get('regularMarketPrice')
            except:
                pass
        if price:
            return float(price)
        df = tk.history(period="1d", interval="1m", auto_adjust=False)
        if not df.empty:
            return float(df['Close'].iloc[-1])
        return None
    except:
        return None

def get_early_signal(ticker, tf="15m"):
    try:
        tk = yf.Ticker(ticker)
        real_price = get_real_price(ticker)
        if not real_price:
            return None, None
        df = tk.history(period="5d", interval=tf, auto_adjust=False)
        if df.empty or len(df) < 30:
            return None, None
        recent_high = float(df['High'].iloc[-20:].max())
        recent_low = float(df['Low'].iloc[-20:].min())
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.001)))
        rsi_now = float(rsi.iloc[-1])
        rsi_prev = float(rsi.iloc[-2])
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        vol_now = df['Volume'].iloc[-1]
        vol_ratio = float(vol_now/vol_avg) if vol_avg else 1.0
        near_high = real_price >= recent_high * 0.995
        near_low = real_price <= recent_low * 1.005
        info = {"curr":real_price, "rh":recent_high, "rl":recent_low, "rsi":rsi_now, "rsi_prev":rsi_prev, "vol":vol_ratio}
        if near_high and rsi_now > rsi_prev and rsi_now > 45:
            return "CALL", info
        if near_low and rsi_now < rsi_prev and rsi_now < 55:
            return "PUT", info
        if rsi_now < 32 and rsi_now > rsi_prev:
            return "CALL", info
        if rsi_now > 68 and rsi_now < rsi_prev:
            return "PUT", info
        return None, info
    except Exception as e:
        return None, {"error":str(e)}

tf = st.selectbox("Timeframe", ["5m","15m","30m","1h","1d"], index=1)
watch = st.text_area("Tickers", "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL")
WATCHLIST = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button("RUN EARLY SCAN", use_container_width=True, type="primary"):
    st.subheader("Real Prices Now:")
    for t in WATCHLIST:
        real = get_real_price(t)
        sig, info = get_early_signal(t, tf)
        if real is None:
            st.warning(f"{t}: no price")
            continue
        if sig:
            emoji = "CALL" if sig=="CALL" else "PUT"
            txt = f"{emoji} {t} {sig} EARLY | ${real:.2f} | RSI:{info['rsi']:.1f} | High:{info['rh']:.2f} Low:{info['rl']:.2f} | {tf}"
            st.code(txt)
            send(txt)
        else:
            if info and "rsi" in info:
                arrow = "UP" if info['rsi'] > info['rsi_prev'] else "DOWN"
                st.write(f"{t} ${real:.2f} | High:{info['rh']:.2f} Low:{info['rl']:.2f} | RSI:{info['rsi']:.1f} {arrow}")
            else:
                st.write(f"{t} ${real:.2f} | neutral")

st.caption("Early logic: breakout 20-bar high/low + RSI - before EMA cross")
