import streamlit as st, yfinance as yf, pandas as pd
st.set_page_config(page_title="Whale LIVE", layout="wide")
st.title("🐋 كاشف الحيتان V3 - مباشر")
tickers = st.sidebar.multiselect("الأسهم", ["TSLA","NVDA","SPY","AAPL"], default=["TSLA","NVDA","SPY"])
@st.cache_data(ttl=900)
def get_whales(symbols):
    rows=[]
    for s in symbols:
        try:
            tk=yf.Ticker(s)
            for exp in tk.options[:2]:
                df=tk.option_chain(exp).calls
                df=df[(df.volume>1000)&(df.volume/(df.openInterest+1)>1.2)]
                for _,r in df.iterrows():
                    prem=r.volume*r.lastPrice*100/1e6
                    if prem>1: rows.append([s,r.strike,exp,r.lastPrice,int(r.volume),round(prem,2)])
        except: pass
    return pd.DataFrame(rows, columns=["Symbol","Strike","Exp","Price","Vol","Premium M"])
st.dataframe(get_whales(tickers), use_container_width=True)
st.button("🔄 تحديث")
