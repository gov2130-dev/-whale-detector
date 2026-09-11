import streamlit as st, yfinance as yf, requests, os, time
import pandas as pd
from datetime import datetime, date

st.set_page_config(layout="wide", page_title="بوت الحيتان")
st.title("🐳 بوت الحيتان - نسخة مستقرة")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

WATCHLIST = ["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI","ORCL","NVO","MSFT","GOOGL"]

def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={'chat_id': CHAT_ID, 'text': msg}, timeout=10)
        return r.status_code == 200
    except:
        return False

def get_signal(ticker, tf="15m"):
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="5d", interval=tf, auto_adjust=True)
        if df.empty or len(df) < 20:
            return None, f"{ticker}: لا بيانات {tf}"
        
        # نستخدم الشمعة الحية مباشرة - قراءة مبكرة
        curr = float(df['Close'].iloc[-1])
        ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
        ema20 = df['Close'].ewm(span=20).mean().iloc[-1]
        
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain/loss.replace(0,0.001)))
        rsi_now = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
        
        # تحديد مبكر
        if ema9 > ema20 and rsi_now > 40:
            return "CALL", {"curr":curr,"ema9":ema9,"ema20":ema20,"rsi":rsi_now}
        elif ema9 < ema20 and rsi_now < 60:
            return "PUT", {"curr":curr,"ema9":ema9,"ema20":ema20,"rsi":rsi_now}
        else:
            return "CALL" if curr > ema20 else "PUT", {"curr":curr,"ema9":ema9,"ema20":ema20,"rsi":rsi_now}
    except Exception as e:
        return None, f"{ticker}: خطأ {e}"

# واجهة
tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=1)
watch = st.text_area("الأسهم", ",".join(WATCHLIST))
WATCHLIST = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button("🚀 فحص", use_container_width=True, type="primary"):
    if not WATCHLIST:
        st.warning("حط أسهم")
    else:
        sent = 0
        for t in WATCHLIST:
            sig, info = get_signal(t, tf)
            if sig is None:
                st.write(f"⚪ {info}")
                continue
            
            emoji = "🟢" if sig=="CALL" else "🔴"
            txt = f"{emoji} {t} {sig} | ${info['curr']:.2f} | RSI:{info['rsi']:.1f} | EMA9:{info['ema9']:.2f} > EMA20:{info['ema20']:.2f} | {tf} | {datetime.now().strftime('%H:%M:%S')}"
            st.code(txt)
            
            if send(txt):
                sent += 1
                st.toast(f"ارسل {t}")
            time.sleep(0.3)
        st.success(f"✅ فحص {len(WATCHLIST)} - ارسل {sent}")
        if sent==0 and (not BOT_TOKEN or not CHAT_ID):
            st.error("حط BOT_TOKEN و CHAT_ID في Secrets")
            st.info("افتح: Manage app > Settings > Secrets")

st.markdown("---")
st.caption("نسخة مبكرة - تقرأ قبل التقاطع بمسافة 0.3% + RSI صاعد/هابط")
