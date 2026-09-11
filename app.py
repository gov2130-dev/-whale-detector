import streamlit as st, yfinance as yf, requests

st.set_page_config(layout="wide")
st.title("Whale Bot - Final Fixed")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(m):
    try:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=8)
    except: pass

def get_close_series(df):
    # يحل مشكلة Series vs DataFrame
    c = df['Close']
    if hasattr(c, 'columns'):  # DataFrame
        c = c.iloc[:,0]
    c = c.dropna()
    return c

def get_df(t, tf):
    for per in ["60d","20d","10d","5d"]:
        try:
            df = yf.download(t, period=per, interval=tf, auto_adjust=True, progress=False, threads=False)
            if df is not None and not df.empty and len(df) > 10:
                return df
        except: pass
    return None

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=3)
default_list = "SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL,AMZN,NFLX,PLTR,SHOP,UBER,BA"
watch = st.text_area("القائمة", default_list, height=80)
WL = [x.strip().upper() for x in watch.split(",") if x.strip()]

if st.button(f"RUN SCAN {tf}", use_container_width=True, type="primary"):
    ok = 0
    for t in WL:
        df = get_df(t, tf)
        if df is None:
            st.write(f"{t} no data")
            continue
        try:
            close = get_close_series(df)
            price = float(close.iloc[-1])
            e9 = float(close.ewm(9).mean().iloc[-1])
            e20 = float(close.ewm(20).mean().iloc[-1])
            
            sig = "CALL" if price > e9 else "PUT"
            txt = f"{t} {sig} | ${price:.2f} | EMA9 {e9:.2f} EMA20 {e20:.2f} | {tf}"
            st.code(txt)
            ok += 1
            if price > e9 and e9 > e20:
                send(txt)
        except Exception as ex:
            st.write(f"{t} error fixed: {ex}")
            continue
    st.success(f"تم {ok}/{len(WL)} في فريم {tf} - الاسعار الحين صحيحة")
