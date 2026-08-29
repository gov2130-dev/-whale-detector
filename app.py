import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
import random

st.set_page_config(layout="wide")
st.title("👑 V1000 النهائي - يبدل لحاله")
is_weekend = date.today().weekday() >= 5
st.caption(f"اليوم {date.today()} - {'🟡 وضع ديمو (ويكند)' if is_weekend else '🔴 وضع حقيقي (السوق فاتح)'}")

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

t = st.sidebar.selectbox("الشركة", ["QQQ","SPY","NVDA","PLTR","TSLA","COIN"], index=0)

if st.sidebar.button("🚀 افحص V1000", type="primary", use_container_width=True):
    rows=[]; S=0
    if is_weekend:
        S=585.0; random.seed(int(date.today().day))
        for strike in [580,585,590,595,600]:
            rows.append({"T":t,"Strike":strike,"S":S,"Exp":"2026-08-31","DTE":2,"OI":random.randint(8000,25000),"Vol":random.randint(800,2000),"Price":round(random.uniform(3,11),2),"BW%":round(abs(strike-S)/S*100,1),"SCORE":random.randint(85,96),"حالة":"💎 جوهرة + ⚡ SWEEP (ديمو)"})
    else:
        try:
            tk=yf.Ticker(t); S=float(tk.history(period="2d")['Close'].iloc[-1])
            for exp in tk.options[:2]:
                dd=dte(exp)
                for _,r in tk.option_chain(exp).calls.iterrows():
                    oi=int(r.get('openInterest',0) or 0)
                    if oi>3000:
                        strike=float(r['strike']); bw=abs(strike-S)/S*100
                        if bw<6: rows.append({"T":t,"Strike":strike,"S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Vol":int(r.get('volume',0) or 0),"Price":float(r.get('lastPrice',0) or 0),"BW%":round(bw,1),"SCORE":85,"حالة":"🔴 حقيقي"})
        except Exception as e: st.error(f"{e}")

    if rows:
        df=pd.DataFrame(rows).sort_values("SCORE", ascending=False)
        st.success(f"لقيت {len(df)} - أقوى واحد سكور {df.iloc[0]['SCORE']}")
        for _,r in df.head(5).iterrows():
            st.markdown(f"### 🔥 {r['T']} {r['Strike']}C | OI {r['OI']:,} | BW {r['BW%']}% | {r['SCORE']}")
            st.progress(r['SCORE']/100)
        st.dataframe(df, use_container_width=True)
