import streamlit as st, yfinance as yf, requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("Whale Bot - All TF")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(m):
    try:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=8)
    except: pass

@st.cache_data(ttl=120)
def get_price(t):
    try:
        df = yf.download(t, period="2d", interval="1d", auto_adjust=True, progress=False)
        if not df.empty: return float(df['Close'].iloc[-1])
    except: pass
    return None

def analyze(t, tf):
    price = get_price(t)
    if not price: return None
    try:
        df = yf.download(t, period="15d", interval=tf, auto_adjust=True, progress=False)
        if len(df) < 30: return None
        c = df['Close']
        e9 = c.ewm(9).mean().iloc[-1]
        e20 = c.ewm(20).mean().iloc[-1]
        e50 = c.ewm(50).mean().iloc[-1]
        delta = c.diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.0001)))
        r = float(rsi.iloc[-1])
        rp = float(rsi.iloc[-2])
        
        score = 0
        # تسعير مرن حسب الفريم
        if price > e9: score += 1
        if e9 > e20: score += 1
        if e20 > e50: score += 1
        if r > rp: score += 1
        if r > 50: score += 1
        
        # CALL
        if score >= 3:
            return {"type":"CALL", "score":score, "price":price, "rsi":r, "e9":e9, "e20":e20, "ticker":t}
        # PUT - عكسها
        score_put = 0
        if price < e9: score_put+=1
        if e9 < e20: score_put+=1
        if r < rp: score_put+=1
        if r < 50: score_put+=1
        if r > 70 or r < 30: score_put+=2
        
        if score_put >= 3:
            return {"type":"PUT", "score":score_put, "price":price, "rsi":r, "e9":e9, "e20":e20, "ticker":t}
        # قريب للاشارة
        return {"type":"WATCH", "score":max(score,score_put), "price":price, "rsi":r, "e9":e9, "e20":e20, "ticker":t}
    except:
        return None

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=3)
default_list = "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL,AMZN,NFLX,PLTR,SHOP,UBER,BA"
watch = st.text_area("القائمة", default_list, height=80)
WL = [x.strip().upper() for x in watch.split(",") if x.strip()]

col1, col2 = st.columns(2)
with col1:
    only = st.button("RUN - ONLY SIGNALS", use_container_width=True, type="primary")
with col2:
    allb = st.button("RUN - BEST 5 حتى لو مراقبة", use_container_width=True)

if only or allb:
    st.cache_data.clear()
    signals = []
    watches = []
    for t in WL:
        res = analyze(t, tf)
        if not res: continue
        if res['type'] in ["CALL","PUT"]:
            signals.append(res)
        else:
            watches.append(res)
    
    # اعرض الاشارات فقط
    if signals:
        signals = sorted(signals, key=lambda x: x['score'], reverse=True)
        for s in signals:
            txt = f"{s['ticker']} {s['type']} | ${s['price']:.2f} | RSI {s['rsi']:.1f} | EMA9 {s['e9']:.1f} > EMA20 {s['e20']:.1f} | Score {s['score']}/5 | {tf}"
            st.code(txt)
            send(txt)
        st.success(f"وجد {len(signals)} اشارة في فريم {tf}")
    else:
        st.warning(f"لا يوجد CALL/PUT صريح في {tf}")
    
    # اذا ضغط BEST 5 اعرض اقرب 5 للمراقبة
    if allb:
        watches = sorted(watches, key=lambda x: x['score'], reverse=True)[:5]
        st.divider()
        st.write("اقرب 5 للانفجار (مراقبة):")
        for w in watches:
            st.write(f"👀 {w['ticker']} ${w['price']:.2f} | RSI {w['rsi']:.1f} | Score {w['score']}/5")
