import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse
import time

st.set_page_config(layout="wide", page_title="Whale V10 PRO")
st.title("Whale V10.0 - نوافذ ذكية")

@st.cache_data(ttl=86400)
def get_all_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"
        nasdaq = pd.read_csv(url, sep="\n", header=None)[0].tolist()
        url2 = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_tickers.txt"
        nyse = pd.read_csv(url2, sep="\n", header=None)[0].tolist()
        all_t = nasdaq + nyse
        all_t = [t for t in all_t if len(t)<=5 and "^" not in t and "/" not in t]
        return list(set(all_t))[:2500]
    except:
        return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","SMCI","COIN"]

HOT_OPTIONS = ["SPY","QQQ","IWM","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","SMCI","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO"]

all_tickers = get_all_tickers()

if "results" not in st.session_state:
    st.session_state.results = pd.DataFrame()
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "page" not in st.session_state:
    st.session_state.page = "TOP10"
if "hot_results" not in st.session_state:
    st.session_state.hot_results = pd.DataFrame()

st.sidebar.title("لوحة التحكم")
min_prem = st.sidebar.slider("Min Whale $", 500000, 5000000, 1000000, 250000)
auto = st.sidebar.checkbox("AUTO SCAN ALL MARKET", value=True)
st.sidebar.write(f"Scanned: {st.session_state.current_idx}/{len(all_tickers)}")
st.sidebar.write(f"Whales: {len(st.session_state.results)}")

st.sidebar.markdown("---")
st.sidebar.subheader("النوافذ - اضغط لتظهر")

if st.sidebar.button("🏆 اقوى 10 CALL و PUT"):
    st.session_state.page = "TOP10"
if st.sidebar.button("🔥 الاكثر تذبذبا"):
    st.session_state.page = "HOT"
if st.sidebar.button("🟢 اقوى CALL فقط"):
    st.session_state.page = "CALL"
if st.sidebar.button("🔴 اقوى PUT فقط"):
    st.session_state.page = "PUT"
if st.sidebar.button("📋 كل الحيتان"):
    st.session_state.page = "ALL"
if st.sidebar.button("📱 تنبيهات واتساب"):
    st.session_state.page = "WA"

st.sidebar.markdown("---")
st.sidebar.subheader("واتساب سريع")
if not st.session_state.results.empty:
    for _, w in st.session_state.results.sort_values("premium", ascending=False).head(3).iterrows():
        msg = f"WHALE {w['ticker']} {w['signal']} {w['strike']} ${w['premium']:,.0f}"
        st.sidebar.link_button(f"{w['ticker']} ${w['premium']/1e6:.1f}M", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"qwa_{w['ticker']}_{w['premium']}")

if st.sidebar.button("RESET"):
    st.session_state.results = pd.DataFrame()
    st.session_state.current_idx = 0
    st.session_state.hot_results = pd.DataFrame()
    st.rerun()

if auto and st.session_state.current_idx < len(all_tickers):
    start = st.session_state.current_idx
    end = min(start+80, len(all_tickers))
    batch_list = all_tickers[start:end]
    st.info(f"يفحص {start} الى {end}")
    st.progress(end/len(all_tickers))
    all_data = []
    for t in batch_list:
        try:
            s = yf.Ticker(t)
            if not s.options:
                continue
            chain = s.option_chain(s.options[0])
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty:
                    continue
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                f = df[(df["premium"]>=min_prem) & (df["volume"]>=200)].copy()
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    f["exp"]=s.options[0]
                    all_data.append(f)
        except:
            pass
    if all_data:
        new_df = pd.concat(all_data)
        combined = pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300)
        st.session_state.results = combined
    st.session_state.current_idx = end
    time.sleep(1)
    st.rerun()

if st.button("🔥 افحص الاكثر تذبذبا الآن"):
    hot_data=[]
    for t in HOT_OPTIONS:
        try:
            s=yf.Ticker(t)
            if not s.options:
                continue
            chain=s.option_chain(s.options[0])
            for typ, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if df.empty:
                    continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                top=df.sort_values("premium", ascending=False).head(1)
                if not top.empty and top.iloc[0]["premium"]>500000:
                    top["ticker"]=t
                    top["signal"]=typ
                    top["exp"]=s.options[0]
                    hot_data.append(top)
        except:
            pass
    if hot_data:
        st.session_state.hot_results=pd.concat(hot_data).sort_values("premium", ascending=False)

if not st.session_state.results.empty:
    final = st.session_state.results.sort_values("premium", ascending=False)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish = put_sum > call_sum
    final["قرار"] = final.apply(lambda r: f"ادخل {r['signal']}" if (("PUT" in r["signal"]) == is_bearish) else "REVERSE لا تدخل", axis=1)

    if is_bearish:
        st.error(f"BEARISH PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else:
        st.success(f"BULLISH CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M - {len(final)} حوت")

    page = st.session_state.page

    if page == "TOP10":
        st.subheader("🏆 اقوى 10 حيتان - قرار الدخول")
        top10 = final.head(10)
        st.dataframe(top10[["ticker","signal","strike","premium","قرار","exp"]], use_container_width=True, height=500)

    elif page == "HOT":
        st.subheader("🔥 الاكثر تذبذبا - اسهم مشهورة")
        if not st.session_state.hot_results.empty:
            st.dataframe(st.session_state.hot_results, use_container_width=True, height=600)
        else:
            st.info("اضغط زر افحص الاكثر تذبذبا")
            st.write(HOT_OPTIONS)

    elif page == "CALL":
        st.subheader("🟢 اقوى CALL فقط")
        calls = final[final["signal"].str.contains("CALL")].head(15)
        st.dataframe(calls, use_container_width=True, height=600)

    elif page == "PUT":
        st.subheader("🔴 اقوى PUT فقط")
        puts = final[final["signal"].str.contains("PUT")].head(15)
        st.dataframe(puts, use_container_width=True, height=600)

    elif page == "ALL":
        st.subheader(f"📋 كل الحيتان ({len(final)})")
        st.dataframe(final, use_container_width=True, height=700)

    elif page == "WA":
        st.subheader("📱 تنبيهات واتساب - اقوى الحيتان")
        cols = st.columns(2)
        for i, (_, w) in enumerate(final.head(10).iterrows()):
            msg = f"WHALE {w['ticker']} {w['signal']} Strike {w['strike']} Premium ${w['premium']:,.0f} Exp {w['exp']} Decision {w['قرار']}"
            with cols[i%2]:
                st.warning(f"{w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M - {w['قرار']}")
                st.link_button(f"واتساب {w['ticker']}", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"main_wa_{i}_{w['ticker']}_{w['premium']}")

st.caption(f"Last update {datetime.now().strftime('%H:%M:%S')} | V10 Windows")
