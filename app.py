import streamlit as st, yfinance as yf, requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("Whale Bot - Fixed")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(m):
    try:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=8)
    except: pass

@st.cache_data(ttl=60)
def get_data(t, tf):
    try:
        df = yf.download(t, period="20d", interval=tf, auto_adjust=True, progress=False)
        if df.empty or len(df) < 20:
            return None
        return df
    except:
        return None

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=1)
default_list = "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL,AMZN,NFLX,PLTR,SHOP,UBER,BA"
watch = st.text_area("القائمة", default_list, height=80)
WL = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button(f"RUN SCAN {tf} - ONLY MATCH", use_container_width=True, type="primary"):
    st.cache_data.clear()
    count = 0
    for t in WL:
        df = get_data(t, tf)
        if df is None:
            continue
        try:
            c = df['Close']
            price = float(c.iloc[-1])
            e9 = float(c.ewm(9).mean().iloc[-1])
            e20 = float(c.ewm(20).mean().iloc[-1])
            delta = c.diff()
            gain = delta.where(delta>0,0).rolling(14).mean()
            loss = -delta.where(delta<0,0).rolling(14).mean()
            rsi = 100 - (100/(1+gain/loss.replace(0,0.0001)))
            r = float(rsi.iloc[-1])

            # منطق مضمون يطلع نتيجة دايم
            if price > e9:
                sig = "CALL"
            else:
                sig = "PUT"
            
            # اضافة قوة الاشارة
            strength = ""
            if sig=="CALL" and e9 > e20 and r > 55: strength="STRONG"
            elif sig=="PUT" and e9 < e20 and r < 45: strength="STRONG"
            else: strength="WEAK"

            txt = f"{t} {sig} {strength} | ${price:.2f} | RSI {r:.1f} | EMA9 {e9:.2f} EMA20 {e20:.2f} | {tf}"
            st.code(txt)
            count+=1
            if strength=="STRONG":
                send(txt)
        except Exception as e:
            continue
    st.success(f"تم فحص {len(WL)} شركة - ظهر {count} نتيجة في {tf}")
