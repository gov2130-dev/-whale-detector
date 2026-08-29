import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
import random

st.set_page_config(layout="wide")
st.title("👑 V900 - يشتغل ويكند + سوق حقيقي")

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

is_weekend = date.today().weekday() >= 5

t = st.sidebar.selectbox("الشركة", ["QQQ","SPY","NVDA","PLTR","TSLA"], index=0)
mode = st.sidebar.radio("الوضع", ["🔴 حقيقي (يوم الاثنين)", "🟡 ديمو (عشان تشوف الشكل الحين ويكند)"])

if st.sidebar.button("🚀 افحص", type="primary", use_container_width=True):
    if is_weekend and "حقيقي" in mode:
        st.warning(f"اليوم {date.today()} ويكند - OI الحقيقي صفر عند yfinance. اختر وضع 🟡 ديمو عشان تشوف كيف بيكون يوم الاثنين، أو انتظر الاثنين 4:30 العصر.")
    
    rows=[]
    if "ديمو" in mode:
        # بيانات تجريبية تشبه يوم الاثنين الحقيقي
        S=585.0 if t=="QQQ" else 645.0
        for strike in [S-5, S, S+5, S+10]:
            rows.append({"T":t,"Strike":strike,"S":S,"Exp":"2026-08-31","DTE":2,"OI":random.randint(8000,25000),"Vol":random.randint(200,2000),"Price":round(random.uniform(2,12),2),"BW%":round(abs(strike-S)/S*100,1),"SCORE":random.randint(75,96),"حالة":"💎 جوهرة + ⚡ SWEEP"})
        st.success("هذا شكل الديمو - يوم الاثنين بيطلع نفسه بس بأرقام حقيقية")
    else:
        try:
            tk=yf.Ticker(t)
            S=float(tk.history(period="2d")['Close'].iloc[-1])
            for exp in tk.options[:2]:
                dd=dte(exp)
                try:
                    for _,r in tk.option_chain(exp).calls.iterrows():
                        oi=int(r.get('openInterest',0) or 0)
                        if oi>0:
                            strike=float(r['strike']); bw=abs(strike-S)/S*100
                            if bw<8:
                                rows.append({"T":t,"Strike":strike,"S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Vol":int(r.get('volume',0) or 0),"Price":float(r.get('lastPrice',0) or 0),"BW%":round(bw,1),"SCORE":85,"حالة":"حقيقي"})
                except: continue
        except Exception as e:
            st.error(f"yfinance معلق: {e}")

    if rows:
        df=pd.DataFrame(rows).sort_values("OI", ascending=False)
        for _,r in df.head(6).iterrows():
            st.markdown(f"### 🔥 {r['T']} {r['Strike']}C | OI {r['OI']:,} | BW {r['BW%']}% | سكور {r['SCORE']}")
            st.progress(min(r['SCORE']/100,1.0))
            c1,c2,c3=st.columns(3)
            c1.metric("OI", f"{r['OI']:,}"); c2.metric("سعر العقد", f"${r['Price']}"); c3.metric("Vol", r['Vol'])
            st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        if not is_weekend:
            st.error("ما لقى - جرب QQQ لحاله")

else:
    st.info("👈 اختار 🟡 ديمو الحين عشان تشوف الشكل - ويوم الاثنين اختار 🔴 حقيقي")
