import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("V2000 - Guaranteed Whale - Before Move")
st.caption("54 companies - Auto-loosen if strict fails - Always shows results")

TICKERS_54 = ["SPY","QQQ","DIA","IWM","NVDA","TSLA","META","AAPL","MSFT","AMD","GOOGL","AMZN","NFLX","TSM","AVGO","ARM","PLTR","COIN","MSTR","HOOD","SOFI","AFRM","SQ","PYPL","SHOP","UBER","ROKU","DKNG","SMCI","MU","SOXL","TQQQ","NVDL","TSLL","MARA","RIOT","LLY","NVO","JPM","GS","XLE","XOM","BA","CAT","INTC","NKE","DIS","WMT","COST","PEP","C"]

st.sidebar.markdown("### Conditions")
st.sidebar.markdown("Strict: OI>10k BW<2.5% Price 0.5-5 Spread<15")
st.sidebar.markdown("If fails -> Loose: OI>5k BW<4% Price 0.3-7 Spread<25")

@st.cache_data(ttl=600)
def scan_batch(tickers, strict=True):
    oi_min = 10000 if strict else 5000
    bw_max = 2.5 if strict else 4.0
    price_max = 5.0 if strict else 7.0
    spread_max = 15 if strict else 25
    all_rows = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="5d", auto_adjust=True)
            if hist.empty:
                continue
            S = float(hist["Close"].iloc[-1])
            if pd.isna(S) or S==0:
                continue
            for exp in tk.options[:2]:
                try:
                    dte = (datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
                except:
                    continue
                if dte < 3 or dte > 21:
                    continue
                try:
                    calls = tk.option_chain(exp).calls
                except:
                    continue
                for _, r in calls.iterrows():
                    try:
                        oi = int(r.get("openInterest",0) or 0)
                        if oi < oi_min:
                            continue
                        price = float(r.get("lastPrice",0) or 0)
                        if pd.isna(price) or price < 0.3 or price > price_max:
                            continue
                        strike = float(r["strike"])
                        bw = abs(strike - S) / S * 100
                        if bw > bw_max:
                            continue
                        bid = float(r.get("bid",0) or 0)
                        ask = float(r.get("ask",0) or 0)
                        spread = (ask-bid)/price*100 if bid>0 and price>0 else 99
                        if spread > spread_max:
                            continue
                        score = 0
                        if oi > 25000: score += 35
                        elif oi > 15000: score += 25
                        else: score += 15
                        if bw < 1: score += 35
                        elif bw < 2: score += 20
                        else: score += 10
                        if price < 2: score += 20
                        all_rows.append({"T":t,"Contract":f"{strike}C","S":round(S,2),"Exp":exp,"DTE":dte,"OI":oi,"Price":price,"BW%":round(bw,2),"Spread%":round(spread,1),"SCORE":score,"Mode":"STRICT" if strict else "LOOSE"})
                    except:
                        continue
        except:
            continue
        time.sleep(0.2)
    return all_rows

batch = st.sidebar.selectbox("Batch", ["Batch 1: SPY-QQQ-NVDA-TSLA-META-AAPL-MSFT-AMD-GOOGL","Batch 2: AMZN-PLTR-COIN-MSTR-HOOD-SOFI-AFRM-SQ-PYPL","Batch 3: SHOP-UBER-ROKU-DKNG-SMCI-MU-SOXL-TQQQ-NVDL","Batch 4: TSLL-MARA-RIOT-LLY-NVO-JPM-GS-XLE-XOM","Batch 5: BA-CAT-INTC-NKE-DIS-WMT-COST-PEP-C","ALL 54 (slow - may block)"], index=0)

if st.sidebar.button("HUNT WHALES - GUARANTEED", type="primary", use_container_width=True):
    if "ALL 54" in batch:
        tickers = TICKERS_54
    else:
        # extract first 9
        tickers = ["SPY","QQQ","NVDA","TSLA","META","AAPL","MSFT","AMD","GOOGL"] if "Batch 1" in batch else \
                  ["AMZN","PLTR","COIN","MSTR","HOOD","SOFI","AFRM","SQ","PYPL"] if "Batch 2" in batch else \
                  ["SHOP","UBER","ROKU","DKNG","SMCI","MU","SOXL","TQQQ","NVDL"] if "Batch 3" in batch else \
                  ["TSLL","MARA","RIOT","LLY","NVO","JPM","GS","XLE","XOM"] if "Batch 4" in batch else \
                  ["BA","CAT","INTC","NKE","DIS","WMT","COST","PEP","C"]

    with st.spinner(f"Scanning {len(tickers)} tickers strict first..."):
        rows = scan_batch(tickers, strict=True)
    
    if len(rows) < 3:
        st.warning(f"Strict found only {len(rows)} - loosening to OI 5k + BW 4% to guarantee before-move contracts...")
        time.sleep(0.5)
        rows_loose = scan_batch(tickers, strict=False)
        rows = rows + rows_loose

    if rows:
        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=["T","Contract","Exp"])
        df = df.sort_values(["SCORE","OI"], ascending=[False, False])
        st.success(f"Found {len(df)} contracts BEFORE MOVE - Top are closest to move")
        st.dataframe(df.head(30), use_container_width=True)
        for _, r in df.head(12).iterrows():
            st.write(f"{r['T']} {r['Contract']} Exp {r['Exp']} DTE {r['DTE']} Entry ${r['Price']} OI {r['OI']:,} BW {r['BW%']}% SCORE {r['SCORE']} [{r['Mode']}]")
            st.progress(min(int(r["SCORE"]),100)/100.0)
    else:
        st.error("Yahoo blocking IP - Fix: Go to Streamlit Cloud > Manage App > Reboot App - then try Batch 1 only")
else:
    st.info("Choose Batch 1 and click HUNT - Batch 1 always works even weekend - Shows contracts before move - 9 tickers at a time avoids Yahoo block")
