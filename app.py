import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("V1801 Whale Hunter - Before Move")
st.caption("Strict conditions - All tickers at once - No nan")

TICKERS = ["SPY","QQQ","NVDA","TSLA","META","AAPL","MSFT","AMD","PLTR","COIN","MSTR","AVGO","HOOD","SOFI","GOOGL","AMZN"]

st.sidebar.markdown("### Strict Whale Conditions:")
st.sidebar.markdown("1. OI > 10000")
st.sidebar.markdown("2. BW% < 2.5%")
st.sidebar.markdown("3. Price 0.5-5$")
st.sidebar.markdown("4. Spread < 15%")
st.sidebar.markdown("5. DTE 4-21")
st.sidebar.markdown("6. Range < 3%")

@st.cache_data(ttl=600)
def get_ticker(t):
    try:
        tk = yf.Ticker(t)
        hist = tk.history(period="10d", auto_adjust=True)
        if hist.empty:
            return None, 0, 0
        close_price = float(hist["Close"].iloc[-1])
        if pd.isna(close_price) or close_price == 0:
            return None, 0, 0
        high_max = hist["High"].iloc[-5:].max()
        low_min = hist["Low"].iloc[-5:].min()
        rng = (high_max - low_min) / close_price * 100
        return tk, close_price, rng
    except:
        return None, 0, 0

if st.sidebar.button("HUNT ALL WHALES", type="primary", use_container_width=True):
    all_rows = []
    prog = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(TICKERS):
        txt.text(f"Scanning {t} {i+1}/{len(TICKERS)}")
        prog.progress((i+1)/len(TICKERS))
        tk, S, rng = get_ticker(t)
        if tk is None:
            continue
        if rng > 3.0:
            continue
        try:
            options = tk.options[:3]
            for exp in options:
                try:
                    dte = (datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
                except:
                    continue
                if dte < 4 or dte > 21:
                    continue
                try:
                    chain = tk.option_chain(exp)
                    calls = chain.calls
                except:
                    continue
                for _, r in calls.iterrows():
                    try:
                        oi = int(r.get("openInterest", 0) or 0)
                        if oi < 10000:
                            continue
                        price = float(r.get("lastPrice", 0) or 0)
                        if pd.isna(price):
                            continue
                        if price < 0.5 or price > 5.0:
                            continue
                        strike = float(r["strike"])
                        bw = abs(strike - S) / S * 100
                        if bw > 2.5:
                            continue
                        bid = float(r.get("bid", 0) or 0)
                        ask = float(r.get("ask", 0) or 0)
                        spread = (ask - bid) / price * 100 if bid > 0 and price > 0 else 99
                        if spread > 15:
                            continue
                        score = 0
                        if oi > 25000:
                            score += 35
                        elif oi > 15000:
                            score += 25
                        else:
                            score += 15
                        if bw < 1.0:
                            score += 30
                        elif bw < 2.0:
                            score += 20
                        else:
                            score += 10
                        if price < 2.0:
                            score += 20
                        if rng < 1.5:
                            score += 15
                        if score >= 60:
                            all_rows.append({
                                "T": t,
                                "Contract": f"{strike}C",
                                "S": round(S, 2),
                                "Exp": exp,
                                "DTE": dte,
                                "OI": oi,
                                "Price": price,
                                "BW%": round(bw, 2),
                                "Spread%": round(spread, 1),
                                "Range%": round(rng, 2),
                                "SCORE": score
                            })
                    except:
                        continue
        except:
            continue
        time.sleep(0.2)

    prog.empty()
    txt.empty()

    if all_rows:
        df = pd.DataFrame(all_rows)
        df = df.sort_values(["SCORE", "OI"], ascending=[False, False])
        st.success(f"Found {len(df)} contracts before move")
        for _, r in df.head(20).iterrows():
            st.write(f"{r['T']} {r['Contract']} Exp {r['Exp']} Entry ${r['Price']} OI {r['OI']:,} BW {r['BW%']}% SCORE {r['SCORE']}")
            st.progress(min(int(r["SCORE"]), 100) / 100.0)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No whale found with strict conditions today - market is weekend. Try again Monday 10:30 NY time")
else:
    st.info("Click HUNT ALL WHALES - scans 16 tickers at once with strict original conditions")
