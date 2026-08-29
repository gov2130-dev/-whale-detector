import streamlit as st, yfinance as yf, pandas as pd, os, math
from datetime import date, datetime
st.set_page_config(layout="wide", page_title="V800")
st.title("👑 V800 - محرك الانفجار (مو جدول تقليدي)")
st.caption("يسجل كل عقد من 100 - فوق 80 = انفجار خلال يومين")

def dte(exp):
    try: return (datetime.strptime(exp, "%Y-%m-%d").date()-date.today()).days
    except: return 99

tickers = st.sidebar.multiselect("شركات", ["SPY","QQQ","NVDA","TSLA","PLTR","COIN","MSTR","AMD","META"], default=["SPY","QQQ","NVDA","PLTR"])
min_score = st.sidebar.slider("🔥 اقل سكور انفجار", 0, 100, 60)

if st.sidebar.button("🚀 احسب الانفجار الآن", type="primary", use_container_width=True):
    rows=[]
    for t in tickers:
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="5d")
            if hist.empty: continue
            S=float(hist['Close'].iloc[-1])
            vol_avg = hist['Volume'].mean()
            last_vol = hist['Volume'].iloc[-1]
            price_trend = (hist['Close'].iloc[-1]-hist['Close'].iloc[-2])/hist['Close'].iloc[-2]*100

            for exp in tk.options[:2]:
                dd = dte(exp)
                if dd<0 or dd>14: continue
                try:
                    calls=tk.option_chain(exp).calls
                    for _,r in calls.iterrows():
                        strike=float(r['strike']); oi=int(r.get('openInterest',0) or 0); vol=int(r.get('volume',0) or 0)
                        price=float(r.get('lastPrice',0) or 0)
                        if oi<2000 or price<0.5: continue
                        bw=abs(strike-S)/S*100
                        if bw>8: continue

                        # --- سكور V800 ---
                        score=0
                        if oi>vol*2: score+=30 # تجميع
                        if oi>10000: score+=20
                        if bw<3: score+=25 # قريب جدا
                        elif bw<5: score+=15
                        if dd<=3: score+=15 # قريب ينتهي
                        if price_trend>1: score+=10 # السهم طالع
                        if last_vol>vol_avg*1.3: score+=10 # حجم اسهم عالي
                        if vol>100 and oi>5000: score+=10

                        if score>=min_score:
                            exp_type = "💥 اليوم" if dd==0 else f"⏳ {dd} يوم"
                            rows.append({"T":t,"Strike":strike,"S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Vol":vol,"Price":price,"BW":round(bw,1),"Trend%":round(price_trend,1),"SCORE":score,"حالة":exp_type})
                except: continue
        except: continue

    if rows:
        df=pd.DataFrame(rows).sort_values("SCORE", ascending=False)
        st.metric("أقوى انفجار", f"{df.iloc[0]['T']} {df.iloc[0]['Strike']}C - سكور {df.iloc[0]['SCORE']}")
        # كروت مو جدول
        for _,r in df.head(10).iterrows():
            color = "🔴" if r['SCORE']>=85 else "🟠" if r['SCORE']>=70 else "🟡"
            st.markdown(f"### {color} {r['T']} {r['Strike']}C | سكور {r['SCORE']}/100 | {r['حالة']}")
            c1,c2,c3,c4=st.columns(4)
            c1.metric("OI", r['OI']); c2.metric("BW%", f"{r['BW']}%"); c3.metric("سعر العقد", f"${r['Price']}"); c4.metric("السهم", f"${r['S']}")
            st.progress(r['SCORE']/100)
            st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("ما لقى سكور عالي - نزل السكور الى 40 لأن اليوم ويكند")

else:
    st.info("👈 هذا مو جدول OI تقليدي - هذا يحسب احتمالية الانفجار. اضغط الزر")
    st.markdown("**V800 يحسب:**\n- 30 نقطة اذا الحوت مجمع (OI>2xVol)\n- 25 نقطة اذا قريب من السعر\n- 15 نقطة اذا باقي يومين وينتهي\n- 10 نقاط اذا السهم نفسه عليه حجم دخول")
