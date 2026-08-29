import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("V1900 Final - 54 Companies - Before Move")
st.caption("54 tickers - Strict whale conditions - Works 24/7 - Auto update ready")

# 54 شركة اللي اتفقنا عليها من اول
TICKERS_54 = [
"SPY","QQQ","DIA","IWM","VIX",
"NVDA","TSLA","META","AAPL","MSFT","AMD","GOOGL","AMZN","NFLX","TSM","AVGO","ARM",
"PLTR","COIN","MSTR","HOOD","SOFI","AFRM","SQ","PYPL","SHOP","UBER","ROKU","DKNG",
"SMCI","MU","SMH","SOXL","TQQQ","SQQQ","NVDL","TSLL","MSTU","MARA","RIOT","BITX",
"LLY","NVO","UNH","JPM","GS","XLF","XLE","XOM","CVX","BA","CAT","NFLX"
]

@st.cache_data(ttl=600)
def scan_ticker(t):
    try:
        tk = yf.Ticker(t)
        hist = tk.history(period="10d", auto_adjust=True)
        if hist.empty:
            return []
        S = float(hist["Close"].iloc[-1])
        if pd.isna(S) or S == 0:
            return []
        rows = []
        exps = tk.options[:3]
        for exp in exps:
            try:
                dte = (datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            except:
                continue
            if dte < 4 or dte > 21:
                continue
            try:
                calls = tk.option_chain(exp).calls
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
                    if oi > 30000:
                        score += 40
                    elif oi > 20000:
                        score += 30
                    elif oi > 10000:
                        score += 20
                    if bw < 1.0:
                        score += 30
                    elif bw < 2.0:
                        score += 20
                    else:
                        score += 10
                    if price < 2.0:
                        score += 20
                    if score >= 60:
                        rows.append({
                            "T": t,
                            "Contract": f"{strike}C",
                            "S": round(S,2),
                            "Exp": exp,
                            "DTE": dte,
                            "OI": oi,
                            "Price": price,
                            "BW%": round(bw,2),
                            "Spread%": round(spread,1),
                            "SCORE": score
                        })
                except:
                    continue
        return rows
    except:
        return []

auto = st.sidebar.checkbox("Auto refresh every 5 min (for later)")
if auto:
    st.sidebar.write("Auto ON - will refresh")

if st.sidebar.button("HUNT 54 WHALES - BEFORE MOVE", type="primary", use_container_width=True):
    all_rows = []
    prog = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(TICKERS_54):
        txt.text(f"Scanning {t} {i+1}/{len(TICKERS_54)}")
        prog.progress((i+1)/len(TICKERS_54))
        rows = scan_ticker(t)
        all_rows.extend(rows)
        time.sleep(0.15)

    prog.empty()
    txt.empty()

    if all_rows:
        df = pd.DataFrame(all_rows)
        df = df.sort_values(["SCORE","OI"], ascending=[False, False])
        st.success(f"Found {len(df)} whale contracts BEFORE move - from 54 companies")
        st.dataframe(df.head(50), use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV - All 54", csv, "whale_54_before_move.csv", "text/csv")
        for _, r in df.head(15).iterrows():
            st.write(f"{r['T']} {r['Contract']} Exp {r['Exp']} Entry ${r['Price']} OI {r['OI']:,} BW {r['BW%']}% SCORE {r['SCORE']}")
            st.progress(min(int(r["SCORE"]),100)/100.0)
    else:
        st.error("No whale found - try loosening OI to 8000 or BW to 3% - yahoo may be blocking")
        st.info("Click again - yahoo sometimes blocks 54 tickers - cache will help second time")
else:
    st.info("This is your original idea: 54 companies - OI>10k + BW<2.5% + Price 0.5-5 + Spread<15 + DTE 4-21 = BEFORE MOVE")
    st.info("Works Saturday/Sunday/Monday - anytime - finds old whale accumulation not today volume")
    st.write(f"Total companies: {len(TICKERS_54)}")
    st.write(TICKERS_54)

if auto:
    time.sleep(300)
    st.rerun()
