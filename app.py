import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
st.set_page_config(layout="wide")
st.title("👑 V810 - يشتغل ويكند")

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

tickers = st.sidebar.multiselect("شركات", ["SPY","QQQ","NVDA","PLTR","TSLA","COIN"], default=["SPY"])
min_score = st.sidebar.slider("سكور", 0, 100, 30)

if st.sidebar.button("🚀 احسب", type="primary", use_container_width=True):
    rows=[]
    for t in tickers:
        try:
            tk=yf.Ticker(t)
            S=float(tk.history(period="2d")['Close'].iloc[-1])
            for exp in tk.options[:2]:
                dd=dte(exp)
                if dd<0 or dd>10: continue
                try:
                    for _,r in tk.option_chain(exp).calls.iterrows():
                        oi=int(r.get('openInterest',0) or 0)
                        vol=int(r.get('volume',0) or 0)
                        if oi<500: continue
                        strike=float(r['strike']); price=float(r.get('lastPrice',0) or 0)
                        bw=abs(strike-S)/S*100
                        if bw>10: continue
                        score=0
                        if oi>2000: score+=25
                        if oi>10000: score+=25
                        if bw<3: score+=30
                        if dd<=2: score+=20
                        if score>=min_score:
                            rows.append({"T":t,"Strike":strike,"S":S,"Exp":exp,"DTE":dd,"OI":oi,"Vol":vol,"BW":round(bw,1),"SCORE":score,"$":price})
                except: continue
        except: continue
    if rows:
        df=pd.DataFrame(rows).sort_values("SCORE", ascending=False)
        st.success(f"لقيت {len(df)}")
        for _,r in df.head(8).iterrows():
            st.markdown(f"### 🔥 {r['T']} {r['Strike']}C سكور {r['SCORE']} - OI {r['OI']} - BW {r['BW']}%")
            st.progress(r['SCORE']/100)
    else:
        st.error("ما لقى - هذا بسبب yfinance في الويكند يعلق. جرب SPY لحاله وسكور 20")

else:
    st.info("اختار SPY لحاله + سكور 30 + اضغط 🚀")
