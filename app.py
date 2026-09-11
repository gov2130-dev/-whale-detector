import streamlit as st, yfinance as yf, requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("Whale Bot - Fixed Price")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(m):
    try:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=8)
    except: pass

def get_price_fixed(t):
    try:
        tk = yf.Ticker(t)
        # جرب 3 مصادر وخذ الاصغر المنطقي
        prices = []
        try:
            p = tk.fast_info.get('last_price')
            if p and 10 < p < 3000: prices.append(float(p))
        except: pass
        try:
            df1 = tk.history(period="1d", interval="1d", auto_adjust=False)
            if not df1.empty:
                prices.append(float(df1['Close'].iloc[-1]))
        except: pass
        try:
            info = tk.info
            p = info.get('currentPrice') or info.get('regularMarketPrice')
            if p and 10 < p < 3000: prices.append(float(p))
        except: pass
        if not prices:
            return None
        # خذ الوسيط عشان لو واحد مضروب 765 ينحذف
        prices.sort()
        return prices[len(prices)//2]
    except:
        return None

def get_signal(t, tf):
    price = get_price_fixed(t)
    if not price: return None, None
    try:
        df = yf.Ticker(t).history(period="10d", interval=tf, auto_adjust=False)
        if len(df) < 30: return None, None
        e9 = df['Close'].ewm(9).mean().iloc[-1]
        e20 = df['Close'].ewm(20).mean().iloc[-1]
        e50 = df['Close'].ewm(50).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain/loss.replace(0,0.001)
        rsi = 100 - (100/(1+rs))
        r = float(rsi.iloc[-1])
        r_prev = float(rsi.iloc[-2])
        rh = float(df['High'].iloc[-20:].max())
        rl = float(df['Low'].iloc[-20:].min())
        vol = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1]

        # منطق متوازن CALL و PUT
        call_cond = (price > e9 > e20) and (r > 55) and (r > r_prev) and (price < rh*1.01)
        put_cond = (price < e9 < e20) and (r < 45) and (r < r_prev) and (price > rl*0.99)
        # مناطق تشبع تعطي PUT حتى لو صاعد
        overbought_put = r > 78 and r < r_prev
        oversold_call = r < 22 and r > r_prev

        info = (price, e9, e20, r, r_prev, rh, rl, vol)
        if oversold_call or call_cond:
            return "CALL", info
        if overbought_put or put_cond:
            return "PUT", info
        return None, info
    except:
        return None, None

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=1)
default_list = "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL,AMZN,NFLX,PLTR,BA,SHOP,UBER"
watch = st.text_area("الشركات", default_list, height=80)
WL = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button("RUN SCAN", use_container_width=True, type="primary"):
    calls = 0
    puts = 0
    for t in WL:
        sig, info = get_signal(t, tf)
        if not info:
            st.write(f"{t} no data")
            continue
        price, e9, e20, r, r_prev, rh, rl, vol = info
        if sig:
            tag = "CALL" if sig=="CALL" else "PUT"
            if sig=="CALL": calls+=1
            else: puts+=1
            txt = f"{t} {tag} | ${price:.2f} | RSI {r:.1f} | EMA9 {e9:.1f} EMA20 {e20:.1f} | Vol x{vol:.1f} | {tf}"
            st.code(txt)
            send(txt)
        else:
            st.write(f"{t} ${price:.2f} | RSI {r:.1f} | EMA9 {e9:.1f}")
    st.success(f"Total: {calls} CALL / {puts} PUT من {len(WL)} شركة")

st.caption("Fixed: median price from 3 sources + balanced CALL/PUT + 20 companies")
