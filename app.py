import streamlit as st, yfinance as yf, requests
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide", page_title="بوت الحيتان المبكر")
st.title("🐳 بوت الحيتان المبكر - قبل التقاطع")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(msg):
    if not BOT_TOKEN or not CHAT_ID: return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
        return r.status_code==200
    except: return False

def get_early_signal(ticker, tf="15m"):
    try:
        tk = yf.Ticker(ticker)
        # بدون auto_adjust عشان السعر يطلع صحيح
        df = tk.history(period="10d", interval=tf, auto_adjust=False)
        if df.empty or len(df) < 30:
            return None, None
        
        # السعر الصحيح من آخر إغلاق
        curr = float(df['Close'].iloc[-1])
        
        # قمة وقاع آخر يومين
        recent_high = float(df['High'].iloc[-20:].max())
        recent_low = float(df['Low'].iloc[-20:].min())
        prev_high = float(df['High'].iloc[-40:-20].max())
        prev_low = float(df['Low'].iloc[-40:-20].min())
        
        # RSI
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.001)))
        rsi_now = float(rsi.iloc[-1])
        rsi_prev = float(rsi.iloc[-2])
        
        # هل RSI صاعد؟
        rsi_up = rsi_now > rsi_prev
        rsi_down = rsi_now < rsi_prev
        
        # حجم
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        vol_now = df['Volume'].iloc[-1]
        vol_ok = vol_now > vol_avg * 0.8
        
        # منطق مبكر: اختراق
        # إذا السعر قرب قمة اليومين وصاعد = CALL قبل ما EMA يتقاطع
        near_high = curr >= recent_high * 0.997
        near_low = curr <= recent_low * 1.003
        
        breaking_up = curr > recent_high * 0.998 and curr > prev_high
        breaking_down = curr < recent_low * 1.002 and curr < prev_low
        
        info = {"curr":curr, "rh":recent_high, "rl":recent_low, "rsi":rsi_now, "rsi_prev":rsi_prev, "vol":vol_ok}
        
        # إشارة مبكرة جداً
        if (near_high or breaking_up) and rsi_up and rsi_now > 45 and vol_ok:
            return "CALL", info
        if (near_low or breaking_down) and rsi_down and rsi_now < 55 and vol_ok:
            return "PUT", info
            
        # احتياط: إذا RSI يعكس من 30 أو 70
        if rsi_now < 35 and rsi_up and curr > recent_low:
            return "CALL", info
        if rsi_now > 65 and rsi_down and curr < recent_high:
            return "PUT", info
            
        return None, info
    except Exception as e:
        return None, {"error":str(e)}

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=1)
watch = st.text_area("الأسهم", "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL", height=60)
WATCHLIST = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button("🚀 فحص مبكر", use_container_width=True, type="primary"):
    for t in WATCHLIST:
        sig, info = get_early_signal(t, tf)
        if not sig:
            if info and "rsi" in info:
                st.write(f"⚪ {t} ${info['curr']:.2f} | قمة:{info['rh']:.2f} قاع:{info['rl']:.2f} | RSI:{info['rsi']:.1f} {'↗' if info['rsi']>info['rsi_prev'] else '↘'}")
            else:
                st.write(f"⚪ {t}: {info}")
            continue
        
        emoji = "🟢" if sig=="CALL" else "🔴"
        txt = f"{emoji} {t} {sig} [مبكر] | ${info['curr']:.2f} | قمة {info['rh']:.2f} قاع {info['rl']:.2f} | RSI {info['rsi']:.1f} {'صاعد' if info['rsi']>info['rsi_prev'] else 'هابط'} | {tf} | {datetime.now().strftime('%H:%M')}"
        st.code(txt)
        if send(txt):
            st.toast(f"ارسل {t} {sig}")

st.caption("منطق مبكر: اختراق قمة/قاع 20 شمعة + RSI + حجم - يسبق EMA بـ 2-3 شموع")
