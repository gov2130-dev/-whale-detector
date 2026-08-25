import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime
import urllib.parse, time

st.set_page_config(layout="wide", page_title="Whale V11 Mobile Alert")
st.title("🐋 Whale V11.0 - تنبيه جوال مباشر")

@st.cache_data(ttl=86400)
def get_all_tickers():
    try:
        url="https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"
        nasdaq=pd.read_csv(url, sep="\n", header=None)[0].tolist()
        url2="https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_tickers.txt"
        nyse=pd.read_csv(url2, sep="\n", header=None)[0].tolist()
        all_t=[t for t in nasdaq+nyse if len(t)<=5 and "^" not in t and "/" not in t]
        return list(set(all_t))[:2500]
    except:
        return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX"]

HOT_OPTIONS=["SPY","QQQ","IWM","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME"]

def send_telegram(msg):
    try:
        token=st.secrets.get("TELEGRAM_TOKEN","")
        chat=st.secrets.get("TELEGRAM_CHAT_ID","")
        if not token or not chat:
            return False
        url=f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id":chat,"text":msg, "parse_mode":"Markdown"}, timeout=5)
        return True
    except:
        return False

all_tickers=get_all_tickers()
if "results" not in st.session_state:
    st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state:
    st.session_state.current_idx=0
if "page" not in st.session_state:
    st.session_state.page="TOP10"
if "hot_results" not in st.session_state:
    st.session_state.hot_results=pd.DataFrame()
if "sent" not in st.session_state:
    st.session_state.sent=set()

st.sidebar.title("لوحة التحكم")
min_prem=st.sidebar.slider("Min Whale $", 500000, 10000000, 2000000, 500000)
auto=st.sidebar.checkbox("AUTO SCAN ALL MARKET", value=True)
enable_mob=st.sidebar.checkbox("📲 فعل تنبيه الجوال", value=True)
st.sidebar.write(f"Scanned: {st.session_state.current_idx}/{len(all_tickers)} | Whales: {len(st.session_state.results)}")

st.sidebar.markdown("---")
st.sidebar.subheader("النوافذ")
if st.sidebar.button("🏆 اقوى 10 CALL و PUT"): st.session_state.page="TOP10"
if st.sidebar.button("🔥 الاكثر تذبذبا"): st.session_state.page="HOT"
if st.sidebar.button("🟢 اقوى CALL فقط"): st.session_state.page="CALL"
if st.sidebar.button("🔴 اقوى PUT فقط"): st.session_state.page="PUT"
if st.sidebar.button("📋 كل الحيتان"): st.session_state.page="ALL"
if st.sidebar.button("📱 تنبيهات واتساب"): st.session_state.page="WA"

st.sidebar.markdown("---")
if st.sidebar.button("🧪 جرب تنبيه الجوال الآن"):
    ok=send_telegram("🐋 *تجربة تنبيه الحيتان*\nNVDA CALL BUY $29.5M ✅\nنظام التنبيه شغال!")
    if ok:
        st.sidebar.success("تم الإرسال لجوالك!")
    else:
        st.sidebar.error("حط TOKEN و CHAT_ID في Secrets")

if st.sidebar.button("RESET"):
    st.session_state.results=pd.DataFrame()
    st.session_state.current_idx=0
    st.session_state.hot_results=pd.DataFrame()
    st.session_state.sent=set()
    st.rerun()

if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+80, len(all_tickers))
    st.info(f"يفحص {start} الى {end}")
    st.progress(end/len(all_tickers))
    all_data=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            chain=s.option_chain(s.options[0])
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=200)].copy()
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    f["exp"]=s.options[0]
                    all_data.append(f)
        except:
            pass
    if all_data:
        new_df=pd.concat(all_data)
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300)
        st.session_state.results=combined
        # تنبيه جوال للحيتان الجديدة الكبيرة
        if enable_mob:
            for _, w in new_df.sort_values("premium", ascending=False).head(3).iterrows():
                key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{int(w['premium'])}"
                if key not in st.session_state.sent and w['premium']>=3000000:
                    msg=f"🐋 *حوت جديد!* \n*{w['ticker']}* {w['signal']}\nStrike: {w['strike']}\nPremium: ${w['premium']/1e6:.2f}M\nExp: {w['exp']}\nTime: {datetime.now().strftime('%H:%M:%S')}"
                    if send_telegram(msg):
                        st.session_state.sent.add(key)
    st.session_state.current_idx=end
    time.sleep(1)
    st.rerun()

if not st.session_state.results.empty:
    final=st.session_state.results.sort_values("premium", ascending=False)
    call_sum=final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum=final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish=put_sum>call_sum
    final["قرار"]=final.apply(lambda r: f"ادخل {r['signal']}" if (("PUT" in r["signal"])==is_bearish) else "REVERSE لا تدخل", axis=1)

    if is_bearish: st.error(f"BEARISH PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else: st.success(f"BULLISH CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M - {len(final)} حوت")

    page=st.session_state.page
    if page=="TOP10":
        st.subheader("🏆 اقوى 10 حيتان")
        st.dataframe(final.head(10), use_container_width=True)
    elif page=="HOT":
        st.subheader("🔥 الاكثر تذبذبا")
        st.dataframe(st.session_state.hot_results, use_container_width=True)
    elif page=="CALL":
        st.subheader("🟢 CALL فقط")
        st.dataframe(final[final["signal"].str.contains("CALL")].head(20), use_container_width=True)
    elif page=="PUT":
        st.subheader("🔴 PUT فقط")
        st.dataframe(final[final["signal"].str.contains("PUT")].head(20), use_container_width=True)
    elif page=="ALL":
        st.subheader("📋 كل الحيتان")
        st.dataframe(final, use_container_width=True, height=700)
    elif page=="WA":
        st.subheader("📱 واتساب + تليجرام")
        cols=st.columns(2)
        for i, (_, w) in enumerate(final.head(10).iterrows()):
            msg=f"WHALE {w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M Strike {w['strike']}"
            with cols[i%2]:
                st.warning(f"{w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M")
                c1,c2=st.columns(2)
                c1.link_button("واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{i}")
                if c2.button("تليجرام", key=f"tg_{i}"):
                    send_telegram(f"🐋 {msg}\nقرار: {w['قرار']}")
                    st.success("تم الإرسال!")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V11 Mobile Alert - فعل التنبيه من اليسار")
