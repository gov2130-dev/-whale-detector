import streamlit as st, yfinance as yf, requests, pandas as pd
from datetime import datetime, date, timedelta

st.set_page_config(layout="wide", page_title="Whale Bot")
st.markdown("""
<style>
.stApp {background:#0a0e14; color:white}
div[data-testid="stCode"] {background:#111827; border-left:4px solid #00ff88; border-radius:10px}
h1 {color:#00ff88}
</style>
""", unsafe_allow_html=True)

st.title("🐳 بوت الحيتان - قراءة مبكرة")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(msg):
    if not BOT_TOKEN or not CHAT_ID: return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
        return r.status_code==200
    except: return False

def get_data_fixed(ticker, tf="15m"):
    try:
        tk = yf.Ticker(ticker)
        # 1. السعر الحقيقي من فريم 1دقيقة لآخر يوم - هذا الوحيد الصحيح
        df1 = tk.history(period="1d", interval="1m", auto_adjust=True)
        if df1.empty:
            return None, None
        real_price = float(df1['Close'].iloc[-1])
        
        # 2. بيانات المؤشرات من فريم اللي اخترته
        df = tk.history(period="5d", interval=tf, auto_adjust=True)
        if df.empty or len(df) < 30:
            return None, None
        
        # صحح السعر في df عشان EMA و RSI يصير على السعر الحقيقي
        # اذا فرق كبير بين df و real_price نسوي normalize
        last_close = float(df['Close'].iloc[-1])
        if abs(last_close - real_price) / real_price > 0.15:
            factor = real_price / last_close
            df['Close'] = df['Close'] * factor
            df['High'] = df['High'] * factor
            df['Low'] = df['Low'] * factor
            df['Open'] = df['Open'] * factor

        # المؤشرات
        ema9 = df['Close'].ewm(span=9).mean()
        ema20 = df['Close'].ewm(span=20).mean()
        ema9_now = float(ema9.iloc[-1])
        ema20_now = float(ema20.iloc[-1])
        ema9_prev = float(ema9.iloc[-2])
        ema20_prev = float(ema20.iloc[-2])

        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.001)))
        rsi_now = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
        rsi_prev = float(rsi.iloc[-2]) if not pd.isna(rsi.iloc[-2]) else 50

        recent_high = float(df['High'].iloc[-20:].max())
        recent_low = float(df['Low'].iloc[-20:].min())

        # منطق مبكر: قبل التقاطع
        dist = abs(ema9_now - ema20_now) / ema20_now * 100
        ema_bullish_soon = ema9_now > ema20_prev and ema9_now < ema20_now and dist < 0.4
        ema_bearish_soon = ema9_now < ema20_prev and ema9_now > ema20_now and dist < 0.4
        
        # قراءة مبكرة
        is_early_call = (ema_bullish_soon and rsi_now > rsi_prev and rsi_now > 45) or (real_price >= recent_high*0.998 and rsi_now>50)
        is_early_put = (ema_bearish_soon and rsi_now < rsi_prev and rsi_now < 55) or (real_price <= recent_low*1.002 and rsi_now<50)

        info = {
            "curr": real_price,
            "ema9": ema9_now,
            "ema20": ema20_now,
            "rsi": rsi_now,
            "rsi_prev": rsi_prev,
            "rh": recent_high,
            "rl": recent_low,
            "dist": dist
        }
        
        if is_early_call:
            return "CALL", info
        if is_early_put:
            return "PUT", info
        
        # اذا مافي مبكر نرجع العادي
        if ema9_now > ema20_now and rsi_now > 50:
            return "CALL", info
        if ema9_now < ema20_now and rsi_now < 50:
            return "PUT", info
            
        return None, info
    except Exception as e:
        return None, {"error":str(e)}

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=1)
watch = st.text_area("الأسهم", "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL")
WATCHLIST = [x.strip().upper() for x in watch.split(",") if x.strip()]

col1, col2 = st.columns(2)
with col1:
    run = st.button("🚀 فحص مبكر + عادي", use_container_width=True, type="primary")
with col2:
    if st.button("🧪 تست تيليجرام", use_container_width=True):
        if send("تست البوت المبكر شغال ✅"):
            st.success("ارسل")
        else:
            st.error("حط BOT_TOKEN و CHAT_ID")

if run:
    st.subheader(f"Real Prices Now - {datetime.now().strftime('%H:%M:%S')}")
    for t in WATCHLIST:
        sig, info = get_data_fixed(t, tf)
        if not info or "curr" not in info:
            st.write(f"⚪ {t}: لا بيانات")
            continue
        
        price = info['curr']
        rsi = info['rsi']
        arrow = "↗" if rsi > info['rsi_prev'] else "↘"
        early_tag = "EARLY" if (abs(info['ema9']-info['ema20'])/info['ema20']*100 < 0.5) else ""
        
        if sig:
            emoji = "🟢" if sig=="CALL" else "🔴"
            txt = f"{emoji} {t} {sig} {early_tag} | ${price:.2f} | RSI:{rsi:.1f} {arrow} | EMA9:{info['ema9']:.2f} EMA20:{info['ema20']:.2f} | H:{info['rh']:.2f} L:{info['rl']:.2f} | {tf}"
            st.code(txt)
            send(txt)
        else:
            st.write(f"⚪ {t} ${price:.2f} | High:{info['rh']:.2f} Low:{info['rl']:.2f} | RSI:{rsi:.1f} {arrow} | EMA9:{info['ema9']:.2f} EMA20:{info['ema20']:.2f}")

st.caption("Fixed: price from 1m chart + early detection before EMA cross (0.4% distance) + breakout")            return float(df['Close'].iloc[-1])
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
