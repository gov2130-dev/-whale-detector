import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse
import time

st.set_page_config(layout="wide")
st.title("Whale V8.2 AUTO - All Market Scanner")

@st.cache_data(ttl=86400)
def get_all_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"
        nasdaq = pd.read_csv(url, sep="\n", header=None)[0].tolist()
        url2 = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_tickers.txt"
        nyse = pd.read_csv(url2, sep="\n", header=None)[0].tolist()
        all_t = nasdaq + nyse
        all_t = [t for t in all_t if len(t)<=5 and "^" not in t and "/" not in t]
        return list(set(all_t))[:3000]
    except:
        return ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","V","UNH","MA","HD","COST","PG","XOM","LLY","AVGO","CVX","ABBV","MRK","PEP","KO","ADBE","WMT","CRM","BAC","NFLX","ORCL","AMD","TMO","CSCO","ACN","MCD","ABT","DHR","LIN","VZ","QCOM","TXN","WFC","INTC","AMGN","CAT","UNP","MS","INTU","AMAT","IBM","GE","NOW","LOW","HON","BLK","BA","SPG","PFE","DIS"]*20

all_tickers = get_all_tickers()

if "results" not in st.session_state:
    st.session_state.results = pd.DataFrame()
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0

min_prem = st.sidebar.slider("Min Whale $", 500000, 5000000, 1000000, 250000)
batch = 100
auto = st.sidebar.checkbox("AUTO SCAN ALL MARKET", value=True)
st.sidebar.write(f"Scanned: {st.session_state.current_idx} / {len(all_tickers)}")
st.sidebar.write(f"Whales found: {len(st.session_state.results)}")

if st.sidebar.button("RESET"):
    st.session_state.results = pd.DataFrame()
    st.session_state.current_idx = 0
    st.rerun()

if auto and st.session_state.current_idx < len(all_tickers):
    start = st.session_state.current_idx
    end = min(start + batch, len(all_tickers))
    batch_list = all_tickers[start:end]
    st.info(f"AUTO scanning {start} to {end} - remaining {len(all_tickers)-end}")
    prog = st.progress(start/len(all_tickers))
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
        combined = pd.concat([st.session_state.results, new_df])
        combined = combined.sort_values("premium", ascending=False)
        combined = combined.drop_duplicates(subset=["ticker","strike","exp","signal"])
        st.session_state.results = combined.head(200)
    st.session_state.current_idx = end
    prog.progress(end/len(all_tickers))
    time.sleep(1)
    st.rerun()

if not st.session_state.results.empty:
    final = st.session_state.results.sort_values("premium", ascending=False)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish = put_sum > call_sum
    if is_bearish:
        st.error(f"BEARISH PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else:
        st.success(f"BULLISH CALL ${call_sum/1e6:.1f}M - {len(final)} whales")
    final["decision"] = final.apply(lambda r: "ENTER" if (("PUT" in r["signal"]) == is_bearish) else "REVERSE" if r["premium"]>3000000 else "SKIP", axis=1)
    if not final[final["premium"]>5000000].empty:
        st.balloons()
    for _, w in final.head(5).iterrows():
        if w["premium"]>2000000:
            msg = f"WHALE {w['ticker']} {w['signal']} {w['strike']} ${w['premium']:,.0f}"
            st.warning(f"{msg} - {w['decision']}")
            st.link_button(f"WhatsApp {w['ticker']}", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{w['ticker']}_{w['strike']}_{w['exp']}_{w['premium']}")
    st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","decision","exp"]].head(100), use_container_width=True)
    if st.session_state.current_idx >= len(all_tickers):
        st.success("Finished scanning 3000 stocks!")
else:
    st.info("Enable AUTO SCAN from sidebar to start")

st.caption(f"Last update {datetime.now().strftime('%H:%M:%S')}")
