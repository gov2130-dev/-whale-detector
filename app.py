import streamlit as st, yfinance as yf, requests, json, os, time
import pandas as pd
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)
WATCHLIST=["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return True
    except:
        return False

def get_fibo(h,l,d):
    diff = (h-l) or 1.0
    if d=="PUT":
        return round(l-diff*0.382,2), round(l-diff*0.618,2), round(l-diff*1.0,2)
    return round(h+diff*0.382,2), round(h+diff*0.618,2), round(h+diff*1.0,2)

def get_strong_direction(ticker):
    try:
        tk = yf.Ticker(ticker)
        df15 = tk.history(period="10d", interval="15m")
        df5 = tk.history(period="5d", interval="5m")
        df_daily = tk.history(period="20d")
        if df15.empty or len(df15) < 30:
            df15 = df_daily
        if df5.empty:
            df5 = df_daily
        curr = float(df15['Close'].iloc[-1])
        ema9 = df15['Close'].ewm(span=9, min_periods=1).mean().iloc[-1]
        ema20 = df15['Close'].ewm(span=20, min_periods=1).mean().iloc[-1]
        ema50 = df15['Close'].ewm(span=50, min_periods=1).mean().iloc[-1]
        try:
            df5['TP'] = (df5['High']+df5['Low']+df5['Close'])/3
            vwap = (df5['TP']*df5['Volume']).sum() / df5['Volume'].sum()
            if pd.isna(vwap):
                vwap = df15['Close'].mean()
        except:
            vwap = df15['Close'].mean()
        try:
            delta = df15['Close'].diff()
            gain = delta.where(delta>0,0).rolling(14, min_periods=5).mean()
            loss = -delta.where(delta<0,0).rolling(14, min_periods=5).mean()
            rs = gain / loss.replace(0,0.001)
            rsi = 100 - (100/(1+rs))
            rsi_now = float(rsi.iloc[-1])
            if pd.isna(rsi_now):
                rsi_now = 50
        except:
            rsi_now = 50
        try:
            avg_vol = df_daily['Volume'].mean()
            vol_now = df5['Volume'].sum() if not df5.empty else df_daily['Volume'].iloc[-1]
            vol_ok = vol_now > avg_vol * 0.5
        except:
            vol_ok = True
        call_strong = ema9 > ema20 and ema9 > ema50 and curr > vwap and 50 <= rsi_now <= 75 and vol_ok
        put_strong = ema9 < ema20 and ema9 < ema50 and curr < vwap and 25 <= rsi_now <= 50 and vol_ok
        if call_strong:
            return "CALL"
        if put_strong:
            return "PUT"
        return None
    except:
        return None

@st.cache_data(ttl=20)
def get_now_fast(ticker, exp, strike, direction):
    try:
        tk=yf.Ticker(ticker)
        chain=tk.option_chain(exp)
        opts=chain.calls if direction=="CALL" else chain.puts
        row=opts[opts['strike']==float(strike)]
        if row.empty:
            return None
        bid=float(row['bid'].iloc[0] or 0)
        ask=float(row['ask'].iloc[0] or 0)
        if bid>0 and ask>0:
            return round((bid+ask)/2,2)
        return round(float(row['lastPrice'].iloc[0]),2)
    except:
        return None

st.set_page_config(layout="wide")
st.markdown("<style>.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:12px;white-space:pre-wrap}</style>", unsafe_allow_html=True)

if st.button("🚀 فحص توافق 90%+ وارسال (0.2$-4$)", use_container_width=True, type="primary"):
    sent=0
    for t in WATCHLIST:
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="5d")
            if hist.empty:
                continue
            curr=round(float(hist['Close'].iloc[-1]),2)
