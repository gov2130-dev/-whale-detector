import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Whale Detector V6.5 - Live")
st.caption(f"Live: {datetime.now().strftime('%H:%M:%S')}")

stocks = ["TSLA","NVDA","AAPL","SPY","QQQ","MSFT","AMZN","META","AMD","NFLX"]
all_data = []
for t in stocks:
    try:
        s = yf.Ticker(t)
        if not s.options: continue
        for exp in s.options[:1]:
            chain = s.option_chain(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                f = df[df["premium"]>100000]
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    all_data.append(f)
    except: continue

if all_data:
    final = pd.concat(all_data).sort_values("premium", ascending=False).head(30)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    if call_sum > put_sum:
        st.success(f"🟢 BULLISH - CALL ${call_sum:,.0f} > PUT ${put_sum:,.0f}")
    else:
        st.error(f"🔴 BEARISH - PUT ${put_sum:,.0f} > CALL ${call_sum:,.0f}")
    st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium"]], use_container_width=True)
else:
    st.warning("Market Closed - No data")
