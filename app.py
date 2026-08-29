import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime

st.set_page_config(layout="wide")
st.title("V1700 - صيد الحيتان قبل الحركة")
st.caption("OI عالي + قريب + رخيص + محشور = قبل الانفجار")

st.sidebar.markdown("""
### شروط الحوت الاصلية:
1. OI > 12k حوت مجمع
2. BW% <2.2% على السعر
3. سعر 0.8-4.5$ رخيص
4. Spread <15% سيولة
5. سهم محشور <2.5%
6. DTE 4-21 يوم
""")

@st.cache_data(ttl=900)
def whale_scan(ticker):
    tk=yf.Ticker(ticker)
    hist=tk.history(period="10d")
    if hist.empty:
        return pd.DataFrame(), 0, 0
    S=float(hist['Close'].iloc[-1])
    rng=(hist['High'].iloc[-5:].max()-hist['Low'].iloc[-5:].min())/S*100
    rows=[]
    try:
        for exp in tk.options[:3]:
            dd=(datetime.strptime(exp, "%Y-%m-%d").date()-date.today()).days
            if dd<4 or dd>21:
                continue
            oc=tk.option_chain(exp)
            for _,r in oc.calls.iterrows():
                oi=int(r.get('openInterest',0) or 0)
                if oi<12000:
                    continue
                strike=float(r['strike'])
                price=float(r.get('lastPrice',0) or 0)
                bid=float(r.get('bid',0) or 0)
                ask=float(r.get('ask',0) or 0)
                if price<0.8 or price>4.5:
                    continue
                bw=abs(strike-S)/S*100
                if bw>2.2:
                    continue
                spread=(ask-bid)/price*100 if bid>0 and price>0 else 99
                if spread>15:
                    continue
                if rng>2.5:
                    continue
                score=0
                if oi>20000:
                    score+=30
                else:
                    score+=20
                if bw<0.8:
                    score+=30
                elif bw<1.5:
                    score+=20
                if price<2:
                    score+=20
                if rng<1.2:
                    score+=20
                if score>=60:
                    rows.append({"T":ticker,"Contract":f"{strike}C","S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Price":price,"BW%":round(bw,2),"Spread%":round(spread,1),"Range%":round(rng,2),"SCORE":score})
    except:
        pass
    df=pd.DataFrame(rows)
    if not df.empty:
        df=df.sort_values("SCORE", ascending=False)
    return df, S, rng

t = st.sidebar.selectbox("اختار حوت", ["QQQ","SPY","NVDA","TSLA","META","PLTR"], index=0)

if st.sidebar.button("فك بلوك"):
    st.cache_data.clear()
    st.success("تم فك الكاش")

if st.sidebar.button("صيد الحوت قبل الحركة", type="primary", use_container_width=True):
    df,S,rng = whale_scan(t)
    if df.empty:
        st.warning(f"{t} سعره {S} - ما فيه حوت مجمع قريب ورخيص اليوم")
        st.info("جرب SPY و QQQ دايم فيها حيتان")
    else:
        st.success(f"لقيت {len(df)} حوت - قبل ما يتحرك")
        for _,r in df.head(6).iterrows():
            st.markdown(f"### {r['T']} {r['Contract']} | سكور {r['SCORE']} | دخول ${r['Price']} | OI {r['OI']:,}")
            c1,c2,c3,c4=st.columns(4)
            c1.metric("OI", f"{r['OI']:,}"); c2.metric("BW%", f"{r['BW%']}%"); c3.metric("Spread%", f"{r['Spread%']}%"); c4.metric("محشور", f"{r['Range%']}%")
            st.progress(r['SCORE']/100)
            st.divider()
        st.dataframe(df, use_container_width=True)
else:
    st.info("اختار شركة واضغط صيد الحوت - شركة واحدة عشان ما ننبلّك - هذا يجيبها قبل ما تتحرك")
