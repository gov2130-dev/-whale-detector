import streamlit as st, yfinance as yf, requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("Whale Bot - Signals Only")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(m):
    try:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=8)
    except: pass

@st.cache_data(ttl=60)
def get_true_price(t):
    try:
        # مصدر جديد ما يتأثر بالكاش المضروب - ناخذ اخر يومين يومي
        df = yf.download(t, period="2d", interval="1d", auto_adjust=True, progress=False)
        if not df.empty:
            return float(df['Close'].iloc[-1])
    except: pass
    try:
        tk = yf.Ticker(t)
        return float(tk.fast_info['last_price'])
    except:
        return None

def scan(t, tf):
    price = get_true_price(t)
    if not price:
        return None
    try:
        df = yf.download(t, period="10d", interval=tf, auto_adjust=True, progress=False)
        if len(df) < 30:
            return None
        close = df['Close']
        e9 = close.ewm(9).mean().iloc[-1]
        e20 = close.ewm(20).mean().iloc[-1]
        delta = close.diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.0001)))
        r = float(rsi.iloc[-1])
        r_prev = float(rsi.iloc[-2])
        vol = float(df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1])

        is_call = (price > e9 > e20 and r > 55 and r > r_prev and vol > 1.1)
        is_put = (price < e9 < e20 and r < 45 and r < r_prev) or (r > 75 and r < r_prev) or (r < 25 and r > r_prev)

        if is_call:
            return ("CALL", price, r, e9, e20, vol)
        if is_put:
            return ("PUT", price, r, e9, e20, vol)
        return None
    except:
        return None

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=1)
default_list = "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL,AMZN,NFLX,PLTR,SHOP,UBER,BA"
watch = st.text_area("القائمة", default_list, height=80)
WL = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button("RUN SCAN - ONLY SIGNALS", use_container_width=True, type="primary"):
    st.cache_data.clear()
    found = []
    for t in WL:
        res = scan(t, tf)
        if res:
            sig, price, r, e9, e20, vol = res
            found.append(res)
            color = "CALL" if sig=="CALL" else "PUT"
            txt = f"{t} {color} | ${price:.2f} | RSI {r:.1f} | EMA9 {e9:.1f} EMA20 {e20:.1f} | Vol x{vol:.1f} | {tf}"
            st.code(txt)
            send(txt)
    if not found:
        st.warning(f"لا يوجد اشارات مطابقة الان في {tf} - السوق هادي")
    else:
        st.success(f"تم العثور على {len(found)} اشارة فقط")
