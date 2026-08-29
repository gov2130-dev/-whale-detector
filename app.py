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
    st.info("اضغط صيد كل الحيتان - يفحص 20 شركة مرة وحدة - يجيب عقود قبل ما تتحرك - بدون اختيار شركة واحدة")                strike=float(r['strike'])
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
