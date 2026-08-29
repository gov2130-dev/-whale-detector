import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("V1800 - صيد الحيتان قبل الحركة - الشروط الصارمة")
st.caption("يفحص كل الشركات مرة وحدة - بدون اعذار")

TICKERS = ["SPY","QQQ","NVDA","TSLA","META","AAPL","MSFT","AMD","PLTR","COIN","MSTR","SMCI","AVGO","ARM","HOOD","SOFI","GOOGL","AMZN","NFLX","TSM"]

st.sidebar.markdown("""
### الشروط الصارمة (قبل الحركة):
1. OI > 10,000 حوت مجمع
2. BW% < 2.5% على السعر
3. سعر 0.5 - 5.0$ رخيص لسه
4. Spread < 15% سيولة
5. DTE 4-21 يوم
6. سهم محشور <3% آخر 5 ايام
""")

@st.cache_data(ttl=600)
def get_data(t):
    try:
        tk = yf.Ticker(t)
        # حل مشكلة nan - نجرب 3 طرق للسعر
        hist = tk.history(period="10d", auto_adjust=True)
        if hist.empty:
            return None, 0, 0, "no hist"
        S = float(hist['Close'].iloc[-1])
        if pd.isna(S) or S==0:
            info = tk.info
            S = float(info.get('currentPrice',0) or info.get('regularMarketPrice',0) or 0)
        if S==0 or pd.isna(S):
            return None, 0, 0, "nan price"
        rng = (hist['High'].iloc[-5:].max() - hist['Low'].iloc[-5:].min())/S*100
        return tk, S, rng, "ok"
    except Exception as e:
        return None, 0, 0, str(e)

if st.sidebar.button("صيد كل الحيتان - فحص كامل", type="primary", use_container_width=True):
    all_rows=[]
    prog=st.progress(0); txt=st.empty()
    for i,t in enumerate(TICKERS):
        txt.text(f"يفحص {t} {i+1}/{len(TICKERS)}")
        prog.progress((i+1)/len(TICKERS))
        tk,S,rng,msg = get_data(t)
        if tk is None:
            continue
        if rng>3.0: # محشور فقط
            continue
        try:
            for exp in tk.options[:3]:
                dd=(datetime.strptime(exp, "%Y-%m-%d").date()-date.today()).days
                if dd<4 or dd>21: continue
                try:
                    calls=tk.option_chain(exp).calls
                    for _,r in calls.iterrows():
                        oi=int(r.get('openInterest',0) or 0)
                        if oi<10000: continue
                        price=float(r.get('lastPrice',0) or 0)
                        if price<0.5 or price>5.0: continue
                        if pd.isna(price): continue
                        strike=float(r['strike'])
                        bw=abs(strike-S)/S*100
                        if bw>2.5: continue
                        bid=float(r.get('bid',0) or 0); ask=float(r.get('ask',0) or 0)
                        spread=(ask-bid)/price*100 if bid>0 and price>0 else 99
                        if spread>15: continue
                        score=0
                        if oi>25000: score+=35
                        elif oi>15000: score+=25
                        else: score+=15
                        if bw<1: score+=30
                        elif bw<2: score+=20
                        else: score+=10
                        if price<2: score+=20
                        if rng<1.5: score+=15
                        if score>=60:
                            all_rows.append({"T":t,"Contract":f"{strike}C","S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Price":price,"BW%":round(bw,2),"Spread%":round(spread,1),"Range%":round(rng,2),"SCORE":score})
                except: continue
        except: continue
        time.sleep(0.3)

    prog.empty(); txt.empty()
    if all_rows:
        df=pd.DataFrame(all_rows).sort_values(["SCORE","OI"], ascending=[False,False])
        st.success(f"لقيت {len(df)} عقد - قبل الحركة - الشروط الصارمة")
        for _,r in df.head(20).iterrows():
            st.markdown(f"**{r['T']} {r['Contract']} | Exp {r['Exp']} | دخول ${r['Price']} | OI {r['OI']:,} | BW {r['BW%']}% | سكور {r['SCORE']}**")
            st.progress(min(r['SCORE']/100,1.0))
        st.dataframe(df, use_container_width=True)
    else:
        st.error("ما لقى بالشروط الصارمة - جرب تخفف Spread الى 20% او OI الى 8000 في الويكند")
else:
    st.info("اضغط صيد كل الحيتان - يفحص 20 شركة مرة وحدة - يجيب عقود قبل ما تتحرك - بدون اختيار شركة واحدة")    except Exception as e:
        return None, 0, 0, str(e)

if st.sidebar.button("صيد كل الحيتان - فحص كامل", type="primary", use_container_width=True):
    all_rows=[]
    prog=st.progress(0); txt=st.empty()
    for i,t in enumerate(TICKERS):
        txt.text(f"يفحص {t} {i+1}/{len(TICKERS)}")
        prog.progress((i+1)/len(TICKERS))
        tk,S,rng,msg = get_data(t)
        if tk is None:
            continue
        if rng>3.0: # محشور فقط
            continue
        try:
            for exp in tk.options[:3]:
                dd=(datetime.strptime(exp, "%Y-%m-%d").date()-date.today()).days
                if dd<4 or dd>21: continue
                try:
                    calls=tk.option_chain(exp).calls
                    for _,r in calls.iterrows():
                        oi=int(r.get('openInterest',0) or 0)
                        if oi<10000: continue
                        price=float(r.get('lastPrice',0) or 0)
                        if price<0.5 or price>5.0: continue
                        if pd.isna(price): continue
                        strike=float(r['strike'])
                        bw=abs(strike-S)/S*100
                        if bw>2.5: continue
                        bid=float(r.get('bid',0) or 0); ask=float(r.get('ask',0) or 0)
                        spread=(ask-bid)/price*100 if bid>0 and price>0 else 99
                        if spread>15: continue
                        score=0
                        if oi>25000: score+=35
                        elif oi>15000: score+=25
                        else: score+=15
                        if bw<1: score+=30
                        elif bw<2: score+=20
                        else: score+=10
                        if price<2: score+=20
                        if rng<1.5: score+=15
                        if score>=60:
                            all_rows.append({"T":t,"Contract":f"{strike}C","S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Price":price,"BW%":round(bw,2),"Spread%":round(spread,1),"Range%":round(rng,2),"SCORE":score})
                except: continue
        except: continue
        time.sleep(0.3)

    prog.empty(); txt.empty()
    if all_rows:
        df=pd.DataFrame(all_rows).sort_values(["SCORE","OI"], ascending=[False,False])
        st.success(f"لقيت {len(df)} عقد - قبل الحركة - الشروط الصارمة")
        for _,r in df.head(20).iterrows():
            st.markdown(f"**{r['T']} {r['Contract']} | Exp {r['Exp']} | دخول ${r['Price']} | OI {r['OI']:,} | BW {r['BW%']}% | سكور {r['SCORE']}**")
            st.progress(min(r['SCORE']/100,1.0))
        st.dataframe(df, use_container_width=True)
    else:
        st.error("ما لقى بالشروط الصارمة - جرب تخفف Spread الى 20% او OI الى 8000 في الويكند")
else:
    st.info("اضغط صيد كل الحيتان - يفحص 20 شركة مرة وحدة - يجيب عقود قبل ما تتحرك - بدون اختيار شركة واحدة")
